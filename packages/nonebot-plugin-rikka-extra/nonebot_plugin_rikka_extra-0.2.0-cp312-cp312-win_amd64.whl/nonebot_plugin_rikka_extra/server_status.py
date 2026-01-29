from __future__ import annotations

import asyncio
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import aiohttp
import httpx

from .sdgb.allnet import (
    api_official_server_request,
    decode_lite_response,
    get_raw_delivery,
)
from .sdgb.sdgb import MaimaiClient

_AIME_ALIVE_CHECK_URL = "http://ai.sys-allnet.cn/wc_aime/api/alive_check"


def _exc_to_str(e: Exception) -> str:
    msg = str(e).strip()
    if msg:
        return f"{type(e).__name__}: {msg}"
    return type(e).__name__


@dataclass(frozen=True)
class AllNetDeliveryStatus:
    ok: bool
    elapsed_ms: Optional[float]
    raw: Optional[str]
    error: Optional[str]


@dataclass(frozen=True)
class AllNetInitializeStatus:
    called: bool
    ok: bool
    elapsed_ms: Optional[float]
    status_code: Optional[int]
    response_len: Optional[int]
    response_text: Optional[str]
    error: Optional[str]


@dataclass(frozen=True)
class AimeAliveStatus:
    ok: bool
    elapsed_ms: Optional[float]
    response: Optional[str]
    error: Optional[str]


@dataclass(frozen=True)
class MaimaiTitleStatus:
    ok: bool
    elapsed_ms: Optional[float]
    response_len: Optional[int]
    empty_response: bool
    response: Optional[str]
    error: Optional[str]


@dataclass(frozen=True)
class AllNetServerStatus:
    checked_at: datetime
    ok: bool
    delivery: AllNetDeliveryStatus
    initialize: AllNetInitializeStatus
    aime: AimeAliveStatus
    title: MaimaiTitleStatus
    error: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["checked_at"] = self.checked_at.isoformat()
        return data


async def check_allnet_server_status(
    *,
    title_ver: str = "1.51",
    initialize_payload: Optional[str] = None,
    timeout_seconds: float = 20.0,
) -> AllNetServerStatus:
    checked_at = datetime.now(timezone.utc)

    delivery_elapsed: Optional[float] = None
    initialize_elapsed: Optional[float] = None
    aime_elapsed: Optional[float] = None
    title_elapsed: Optional[float] = None

    raw_delivery: Optional[str] = None
    initialize_len: Optional[int] = None
    initialize_text: Optional[str] = None
    initialize_status: Optional[int] = None
    aime_resp: Optional[str] = None
    title_text: Optional[str] = None
    title_len: Optional[int] = None

    delivery_ok = False
    initialize_called = True
    initialize_ok = False
    aime_ok = False
    title_ok = False
    title_empty = False

    delivery_error: Optional[str] = None
    initialize_error: Optional[str] = None
    aime_error: Optional[str] = None
    title_error: Optional[str] = None

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=timeout_seconds)
    ) as aio_session:
        # 1) AllNet delivery/instruction
        try:
            t0 = time.perf_counter()
            raw_delivery = await get_raw_delivery(aio_session, title_ver=title_ver)
            delivery_elapsed = (time.perf_counter() - t0) * 1000
            delivery_ok = "result=1" in raw_delivery
        except Exception as e:
            delivery_error = _exc_to_str(e)

        # 2) AllNet initialize
        # initialize_payload 目前不可提供：改为空请求体 POST，返回 200 即视为在线。
        try:
            t0 = time.perf_counter()
            payload = initialize_payload or ""
            initialize_status, init_bytes = await api_official_server_request(
                aio_session, payload
            )
            initialize_elapsed = (time.perf_counter() - t0) * 1000
            initialize_len = len(init_bytes)
            initialize_ok = initialize_status == 200
            try:
                initialize_text = decode_lite_response(init_bytes)
            except Exception:
                initialize_text = init_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            initialize_ok = False
            initialize_error = _exc_to_str(e)

        # 3) Aime alive_check
        try:
            t0 = time.perf_counter()
            async with aio_session.get(_AIME_ALIVE_CHECK_URL) as resp:
                resp.raise_for_status()
                aime_resp = (await resp.text()).strip()
                aime_ok = aime_resp == "alive"
            aime_elapsed = (time.perf_counter() - t0) * 1000
        except Exception as e:
            aime_error = _exc_to_str(e)

    # 4) Maimai title service ping (sdgb_api uses httpx)
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as httpx_client:
            t0 = time.perf_counter()
            try:
                maimai_client = MaimaiClient()
                title_text = await maimai_client.call_api(httpx_client, "ping", {}, 0)
            except ValueError as e:
                # Some servers respond with empty body, which may indicate blocked/limited.
                # sdgb_api may raise on decrypt/unpad with zero-length input.
                if "Zero-length input cannot be unpadded" in str(e):
                    title_text = ""
                    title_empty = True
                else:
                    raise
            finally:
                title_elapsed = (time.perf_counter() - t0) * 1000

        title_len = len(title_text) if title_text is not None else 0
        title_ok = True
        if title_len == 0:
            title_empty = True
    except Exception as e:
        title_error = _exc_to_str(e)

    ok = delivery_ok and initialize_ok and aime_ok and title_ok
    error = next(
        (x for x in [delivery_error, initialize_error, aime_error, title_error] if x),
        None,
    )

    return AllNetServerStatus(
        checked_at=checked_at,
        ok=ok,
        delivery=AllNetDeliveryStatus(
            ok=delivery_ok,
            elapsed_ms=delivery_elapsed,
            raw=raw_delivery,
            error=delivery_error,
        ),
        initialize=AllNetInitializeStatus(
            called=initialize_called,
            ok=initialize_ok,
            elapsed_ms=initialize_elapsed,
            status_code=initialize_status,
            response_len=initialize_len,
            response_text=initialize_text,
            error=initialize_error,
        ),
        aime=AimeAliveStatus(
            ok=aime_ok,
            elapsed_ms=aime_elapsed,
            response=aime_resp,
            error=aime_error,
        ),
        title=MaimaiTitleStatus(
            ok=title_ok,
            elapsed_ms=title_elapsed,
            response_len=title_len,
            empty_response=title_empty,
            response=title_text,
            error=title_error,
        ),
        error=error,
    )


def check_allnet_server_status_sync(
    *,
    title_ver: str = "1.53",
    initialize_payload: Optional[str] = None,
    timeout_seconds: float = 20.0,
) -> AllNetServerStatus:
    return asyncio.run(
        check_allnet_server_status(
            title_ver=title_ver,
            initialize_payload=initialize_payload,
            timeout_seconds=timeout_seconds,
        )
    )
