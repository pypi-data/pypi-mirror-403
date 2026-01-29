from __future__ import annotations

import hashlib
import json
import zlib
from typing import Final

import httpx
from nonebot import logger

from .encrypt import aes_pkcs7


class MaimaiClient:
    AesKey: Final[str] = "o2U8F6<adcYl25f_qwx_n]5_qxRcbLN>"
    AesIV: Final[str] = "AL<G:k:X6Vu7@_U]"
    ObfuscateParam: Final[str] = "LatuAa81"
    KeychipID: Final[str] = "A63E-01C28055905"

    def __init__(self):
        self.base_url = "https://maimai-gm.wahlap.com:42081/Maimai2Servlet/"
        self.aes = aes_pkcs7(self.AesKey, self.AesIV)

    async def _get_hash_api(self, api: str) -> str:
        return hashlib.md5(
            (api + "MaimaiChn" + self.ObfuscateParam).encode()
        ).hexdigest()

    async def call_api(
        self, client: httpx.AsyncClient, ApiType: str, data: dict, userId: int
    ):
        """
        先压缩再加密请求数据，发送请求后解密再解压响应数据
        这里的 client 需要传入外部创建的 httpx.AsyncClient 实例
        """

        ApiTypeHash = await self._get_hash_api(ApiType)
        url = f"{self.base_url}{ApiTypeHash}"

        headers = {
            "User-Agent": f"{ApiTypeHash}#{userId}",
            "Content-Type": "application/json",
            "Mai-Encoding": "1.53",
            "Accept-Encoding": "",
            "Charset": "UTF-8",
            "Content-Encoding": "deflate",
            "Host": "maimai-gm.wahlap.com:42081",
        }

        data_byte = bytes(json.dumps(data), encoding="utf-8")  # type: ignore
        CompressedData = zlib.compress(data_byte)
        AESEncrptedData = self.aes.encrypt(CompressedData)

        try:
            # 这里的 timeout 设置稍微长一点，防止服务端处理慢
            resp = await client.post(url, headers=headers, data=AESEncrptedData, timeout=60)  # type: ignore
            resp.raise_for_status()  # 如果状态码不是 2xx 则抛出异常

            AESEncrptedResponse = resp.content
            DecryptedData = self.aes.decrypt(AESEncrptedResponse)
            UncompressedData = zlib.decompress(DecryptedData).decode("utf-8")

            logger.info(f"✅ [SUCCESS] {ApiType} - {UncompressedData}")

            return UncompressedData

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ [HTTP ERROR] {ApiType}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"❌ [ERROR] {ApiType}: {str(e)}")
            return None
