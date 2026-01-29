import hashlib
import json
from datetime import datetime
from typing import TypedDict

import httpx
import pytz

from .configs import config


class QRApiResponse(TypedDict):
    errorID: int
    key: str
    timestamp: str
    userID: int
    token: str


async def qr_api(qr_code: str) -> QRApiResponse:
    if len(qr_code) > 64:
        qr_code = qr_code[-64:]
    time_stamp = datetime.now(pytz.timezone("Asia/Shanghai")).strftime("%y%m%d%H%M%S")
    auth_key = (
        hashlib.sha256(
            (
                config.keychip_id + time_stamp + "XcW5FW4cPArBXEk4vzKz3CIrMuA5EVVW"
            ).encode("UTF-8")
        )
        .hexdigest()
        .upper()
    )
    param = {
        "chipID": config.keychip_id,
        "openGameID": "MAID",
        "key": auth_key,
        "qrCode": qr_code,
        "timestamp": time_stamp,
    }
    headers = {
        "Connection": "Keep-Alive",
        "Host": "ai.sys-allnet.cn",
        "User-Agent": "WC_AIME_LIB",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(verify=False) as client:
        res = await client.post(
            "http://ai.sys-allnet.cn/wc_aime/api/get_data",
            json=param,  # type:ignore
            headers=headers,
        )

    assert res.status_code == 200, "网络错误"
    return json.loads(res.content)
