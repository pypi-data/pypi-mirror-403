import asyncio
import json
import logging
from typing import TypedDict

import httpx

from .sdgb.chime import qr_api
from .sdgb.payload import userlogin_payload, userlogout_payload, userpreview_payload
from .sdgb.sdgb import MaimaiClient

maimai = MaimaiClient()
logger = logging.getLogger("sdgb_workflow")


class UserMusicDetail(TypedDict):
    musicId: int
    level: int
    playCount: int
    achievement: int
    comboStatus: int
    syncStatus: int
    deluxscoreMax: int
    scoreRank: int
    extNum1: int
    extNum2: int


class UserMusicEntry(TypedDict, total=False):
    userMusicDetailList: list[UserMusicDetail]
    length: int


class GetUserMusicResponse(TypedDict, total=False):
    userId: int
    length: int
    nextIndex: int
    userMusicList: list[UserMusicEntry]


async def get_all_score(
    sdgb_client: MaimaiClient, client: httpx.AsyncClient, user_id: int, token: str
) -> list[UserMusicDetail]:
    user_music_list: list[UserMusicDetail] = []
    next_index = 0
    max_count = 200  # 每次获取的数量

    while True:
        data = {
            "userId": user_id,
            "nextIndex": next_index,
            "maxCount": max_count,
            "token": token,
        }

        try:
            resp_str = await sdgb_client.call_api(
                client, "GetUserMusicApi", data, user_id
            )
            if not resp_str:
                logger.info("Empty response, breaking loop")
                break

            resp: GetUserMusicResponse = json.loads(resp_str)
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            break

        # 检查响应内容
        current_list = resp.get("userMusicList", [])
        length = resp.get("length", 0)
        new_next_index = resp.get("nextIndex", 0)

        if current_list:
            for entry in current_list:
                detail_list = entry.get("userMusicDetailList", [])
                for detail in detail_list:
                    if isinstance(detail, dict):
                        user_music_list.append(detail)  # type: ignore[arg-type]

        logger.debug(f"Fetched {length} items. Next index: {new_next_index}")

        # 如果 nextIndex 为 0，说明没有更多数据了
        if new_next_index == 0 or not current_list:
            break

        next_index = new_next_index

    return user_music_list


async def run_workflow(qr_code: str) -> list[UserMusicDetail]:
    sdgb_client = MaimaiClient()

    async with httpx.AsyncClient(verify=False) as client:

        # QR Code 解析
        qr_response = await qr_api(qr_code)
        if qr_response["errorID"] != 0:
            raise RuntimeError("二维码解析失败。")
        user_id = qr_response["userID"]
        token = qr_response["token"]

        # Preview 探测
        preview_payload = userpreview_payload(user_id, token)
        response = await sdgb_client.call_api(
            client, "GetUserPreviewApi", preview_payload, user_id
        )
        assert response is not None, "Preview 请求失败。"

        preview_response = json.loads(response)
        if preview_response["isLogin"]:
            raise RuntimeError("已在他处登录。")

        # UserLogin
        login_payload = userlogin_payload(user_id, token)
        response = await sdgb_client.call_api(
            client, "UserLoginApi", login_payload, user_id
        )
        assert response is not None, "Login 请求失败。"

        login_response = json.loads(response)
        if login_response["returnCode"] == 102:
            raise RuntimeError("二维码已失效。")
        if login_response["returnCode"] != 1:
            raise RuntimeError("login failed.")
        # login_id = login_response["loginId"]
        # login_date = login_response["lastLoginDate"]

        # UserData 等
        player_scores = await get_all_score(sdgb_client, client, user_id, token)
        logger.info(f"获取到总计 {len(player_scores)} 首歌曲记录。")

        await asyncio.sleep(60)  # 模拟游戏时间

        # UserAll

        # requestData_UserAll = UserAll_payload(loginId, loginDate, musicData, GeneralUserInfo)

        # await self.call_api(client, "UpsertUserAllApi", requestData_UserAll, userId)

        # UserLogout
        request_payload = userlogout_payload(user_id)
        result = await sdgb_client.call_api(
            client, "UserLogoutApi", request_payload, user_id
        )
        assert result is not None, "Logout 请求失败。"

        return player_scores
