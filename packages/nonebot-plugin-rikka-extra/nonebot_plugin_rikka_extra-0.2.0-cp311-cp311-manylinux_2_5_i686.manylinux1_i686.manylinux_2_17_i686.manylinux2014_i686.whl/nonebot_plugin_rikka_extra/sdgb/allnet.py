from __future__ import annotations

import asyncio
import os
import re
import time
from dataclasses import dataclass
from typing import Final

import aiohttp
from Crypto.Cipher import AES  # type: ignore[import-not-found]
from Crypto.Util.Padding import pad, unpad  # type: ignore[import-not-found]

try:
    from tqdm import tqdm  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    tqdm = None


@dataclass(frozen=True)
class AllNetConfig:
    key: bytes
    iv: bytes
    user_agent: str
    instruction_url: str
    content: bytes


DEFAULT_CONFIG: Final[AllNetConfig] = AllNetConfig(
    key=bytes([47, 63, 106, 111, 43, 34, 76, 38, 92, 67, 114, 57, 40, 61, 107, 71]),
    iv=bytes(16),
    user_agent="SDGB;Windows/Lite",
    instruction_url="http://at.sys-allnet.cn/net/delivery/instruction",
    content=b"title_id=SDGB&title_ver=1.50&client_id=A63E01C2805&token=205648745",
)


LITE_AUTH_KEY: Final[bytes] = bytes([47, 63, 106, 111, 43, 34, 76, 38, 92, 67, 114, 57, 40, 61, 107, 71])
LITE_AUTH_IV: Final[bytes] = bytes.fromhex("00000000000000000000000000000000")
ALLNET_INITIALIZE_URL: Final[str] = "http://at.sys-allnet.cn/net/initialize"


def enc(key: bytes, iv: bytes, data: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(data, 16))


def dec(key: bytes, iv: bytes, data: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(data), 16)


def _parse_instruction_response(decrypted_str: str) -> str:
    if "|" in decrypted_str:
        url_start = decrypted_str.find("|") + 1
        return decrypted_str[url_start:].strip()
    if "uri=" in decrypted_str:
        url_start = decrypted_str.find("uri=") + 4
        return decrypted_str[url_start:].strip()
    return decrypted_str.strip()


def auth_lite_encrypt(plaintext: str) -> bytes:
    header = bytes(16)
    content = bytes(16) + plaintext.encode("utf-8")
    data = header + content
    padded_data = pad(data, AES.block_size)
    cipher = AES.new(LITE_AUTH_KEY, AES.MODE_CBC, LITE_AUTH_IV)
    return cipher.encrypt(padded_data)


def auth_lite_decrypt(ciphertext: bytes) -> str:
    cipher = AES.new(LITE_AUTH_KEY, AES.MODE_CBC, LITE_AUTH_IV)
    decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
    content = decrypted_data[16:]
    return content.decode("utf-8").strip()


def decode_lite_response(resp_data: bytes) -> str:
    """按 Lite 逻辑解密并过滤控制字符（与 get_raw_delivery 一致）。"""

    decrypted_str = auth_lite_decrypt(resp_data)
    return "".join([ch for ch in decrypted_str if 31 < ord(ch) < 127])


async def get_raw_delivery(
    session: aiohttp.ClientSession,
    *,
    title_ver: str = "1.51",
    title_id: str = "SDGB",
    client_id: str = "A63E01C2805",
) -> str:
    encrypted = auth_lite_encrypt(f"title_id={title_id}&title_ver={title_ver}&client_id={client_id}")
    async with session.post(
        DEFAULT_CONFIG.instruction_url,
        data=encrypted,
        headers={"User-Agent": DEFAULT_CONFIG.user_agent, "Pragma": "DFI"},
    ) as resp:
        resp.raise_for_status()
        resp_data = await resp.read()

    return decode_lite_response(resp_data)


async def api_official_server(session: aiohttp.ClientSession, encrypted_string: str) -> bytes:
    status_code, body = await api_official_server_request(session, encrypted_string)
    if status_code != 200:
        raise aiohttp.ClientResponseError(
            request_info=None,  # type: ignore[arg-type]
            history=(),
            status=status_code,
            message=f"unexpected status {status_code}",
            headers=None,
        )
    return body


async def api_official_server_request(session: aiohttp.ClientSession, payload: str = "") -> tuple[int, bytes]:
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": DEFAULT_CONFIG.user_agent,
    }
    async with session.post(ALLNET_INITIALIZE_URL, data=payload, headers=headers) as resp:
        body = await resp.read()
        return resp.status, body


def get_raw_delivery_sync(*, title_ver: str = "1.51", title_id: str = "SDGB", client_id: str = "A63E01C2805") -> str:
    async def _run() -> str:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            return await get_raw_delivery(session, title_ver=title_ver, title_id=title_id, client_id=client_id)

    return asyncio.run(_run())


def api_official_server_sync(encrypted_string: str) -> bytes:
    async def _run() -> bytes:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            return await api_official_server(session, encrypted_string)

    return asyncio.run(_run())


async def get_download_url(
    session: aiohttp.ClientSession,
    *,
    config: AllNetConfig = DEFAULT_CONFIG,
) -> str:
    payload = bytes(16) + config.content
    encrypted = enc(config.key, config.iv, payload)

    async with session.post(
        config.instruction_url,
        data=encrypted,
        headers={"User-Agent": config.user_agent, "Pragma": "DFI"},
    ) as resp:
        resp.raise_for_status()
        raw = await resp.read()

    decrypted = dec(config.key, raw[:16], raw[16:])
    decrypted_str = decrypted.decode("utf-8")
    return _parse_instruction_response(decrypted_str)


async def extract_document_names(session: aiohttp.ClientSession, url: str) -> tuple[list[str], list[str]]:
    async with session.get(url) as resp:
        resp.raise_for_status()
        text = await resp.text()

    pattern = r"INSTALL\d+=\s*(https?://\S+)"
    urls = re.findall(pattern, text)
    filenames = [u.split("/")[-1] for u in urls]
    return filenames, urls


async def download_file(
    session: aiohttp.ClientSession,
    url: str,
    filename: str,
    *,
    chunk_size: int = 8192,
    show_progress: bool = True,
) -> bool:
    try:
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)

        async with session.get(url) as resp:
            resp.raise_for_status()
            total_size = int(resp.headers.get("content-length", "0") or 0)

            progress_bar = None
            if show_progress and tqdm is not None:
                progress_bar = tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    desc=os.path.basename(filename),
                )

            start_time = time.time()
            with open(filename, "wb") as f:
                async for chunk in resp.content.iter_chunked(chunk_size):
                    if not chunk:
                        continue
                    f.write(chunk)
                    if progress_bar is not None:
                        progress_bar.update(len(chunk))
                        elapsed = time.time() - start_time
                        speed = (progress_bar.n / 1024) / elapsed if elapsed > 0 else 0
                        progress_bar.set_postfix(speed=f"{speed:.2f}KB/s")

            if progress_bar is not None:
                progress_bar.close()

        return True
    except Exception as e:
        print(f"\n下载失败: {e}")
        return False


def get_download_url_sync(*, config: AllNetConfig = DEFAULT_CONFIG) -> str:
    async def _run() -> str:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            return await get_download_url(session, config=config)

    return asyncio.run(_run())


def extract_document_names_sync(url: str) -> tuple[list[str], list[str]]:
    async def _run() -> tuple[list[str], list[str]]:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            return await extract_document_names(session, url)

    return asyncio.run(_run())
