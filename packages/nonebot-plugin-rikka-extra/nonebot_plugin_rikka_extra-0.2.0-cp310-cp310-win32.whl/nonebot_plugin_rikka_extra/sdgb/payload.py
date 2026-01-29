import json
import time
from datetime import datetime

# from nonebot import logger
from logging import getLogger

import pytz

from .configs import config
from .encrypt import CalcRandom

logger = getLogger("sdgb_payload")


def userpreview_payload(userId: int, token: str):
    requestData_UserPreview = {
        "userId": userId,
        "segaIdAuthKey": "",
        "token": token,
        "clientId": config.client_id,
    }
    return requestData_UserPreview


def userlogin_payload(userId: int, token: str):
    timestamp = datetime.now(pytz.timezone("Asia/Shanghai"))
    TimeStamp = int(time.mktime(timestamp.timetuple()))
    requestData_UserLogin = {
        "userId": userId,
        "accessCode": "",
        "regionId": config.region_id,
        "placeId": config.place_id,
        "clientId": config.client_id,
        "dateTime": TimeStamp - 600,
        "loginDateTime": TimeStamp,
        "isContinue": False,
        "genericFlag": 0,
        "token": token,
    }
    return requestData_UserLogin


def userdata_payload(userId: int):
    requestData_UserData = {"userId": userId}
    return requestData_UserData


def userlogout_payload(userId: int):
    timestamp = datetime.now(pytz.timezone("Asia/Shanghai"))
    TimeStamp = int(time.mktime(timestamp.timetuple()))
    requestData_UserLogout = {
        "userId": userId,
        "accessCode": "",
        "regionId": config.region_id,
        "placeId": config.place_id,
        "clientId": config.client_id,
        "loginDateTime": TimeStamp,
        "type": 1,
    }
    return requestData_UserLogout


def UserAll_payload(
    userId: int, loginId: int, loginDate: str, musicData: dict, GeneralUserInfo: list
):
    timestamp = datetime.now(pytz.timezone("Asia/Shanghai"))
    TimeStamp = int(time.mktime(timestamp.timetuple()))

    userData = json.loads(GeneralUserInfo[0])
    userExtend = json.loads(GeneralUserInfo[1])
    userOption = json.loads(GeneralUserInfo[2])
    userRating = json.loads(GeneralUserInfo[3])
    userChargeList = json.loads(GeneralUserInfo[4])
    userActivity = json.loads(GeneralUserInfo[5])
    userMissionDataList = json.loads(GeneralUserInfo[6])

    requestData_UserAll = {
        "userId": userId,
        "playlogId": loginId,
        "isEventMode": False,
        "isFreePlay": False,
        "loginDateTime": TimeStamp,
        "userPlaylogList": [
            {
                "userId": 0,
                "orderId": 0,
                "playlogId": loginId,
                "version": 1053000,
                "placeId": config.place_id,
                "placeName": config.place_name,
                "loginDate": TimeStamp,
                "playDate": datetime.now(pytz.timezone("Asia/Shanghai")).strftime(
                    "%Y-%m-%d"
                ),
                "userPlayDate": datetime.now(pytz.timezone("Asia/Shanghai")).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                + ".0",
                "type": 0,
                "musicId": musicData["musicId"],
                "level": musicData["level"],
                "trackNo": 1,
                "vsMode": 0,
                "vsUserName": "",
                "vsStatus": 0,
                "vsUserRating": 0,
                "vsUserAchievement": 0,
                "vsUserGradeRank": 0,
                "vsRank": 0,
                "playerNum": 1,
                "playedUserId1": 0,
                "playedUserName1": "",
                "playedMusicLevel1": 0,
                "playedUserId2": 0,
                "playedUserName2": "",
                "playedMusicLevel2": 0,
                "playedUserId3": 0,
                "playedUserName3": "",
                "playedMusicLevel3": 0,
                "characterId1": userData["userData"]["charaSlot"][0],
                "characterLevel1": 1,
                "characterAwakening1": 0,
                "characterId2": userData["userData"]["charaSlot"][1],
                "characterLevel2": 1,
                "characterAwakening2": 0,
                "characterId3": userData["userData"]["charaSlot"][2],
                "characterLevel3": 1,
                "characterAwakening3": 0,
                "characterId4": userData["userData"]["charaSlot"][3],
                "characterLevel4": 1,
                "characterAwakening4": 0,
                "characterId5": userData["userData"]["charaSlot"][4],
                "characterLevel5": 1,
                "characterAwakening5": 0,
                "achievement": musicData["achievement"],
                "deluxscore": musicData["deluxscoreMax"],
                "scoreRank": musicData["scoreRank"],
                "maxCombo": 0,
                "totalCombo": 128,
                "maxSync": 0,
                "totalSync": 0,
                "tapCriticalPerfect": 101,
                "tapPerfect": 0,
                "tapGreat": 0,
                "tapGood": 0,
                "tapMiss": 0,
                "holdCriticalPerfect": 9,
                "holdPerfect": 0,
                "holdGreat": 0,
                "holdGood": 0,
                "holdMiss": 0,
                "slideCriticalPerfect": 4,
                "slidePerfect": 0,
                "slideGreat": 0,
                "slideGood": 0,
                "slideMiss": 0,
                "touchCriticalPerfect": 0,
                "touchPerfect": 0,
                "touchGreat": 0,
                "touchGood": 0,
                "touchMiss": 0,
                "breakCriticalPerfect": 1,
                "breakPerfect": 0,
                "breakGreat": 0,
                "breakGood": 0,
                "breakMiss": 0,
                "isTap": True,
                "isHold": True,
                "isSlide": True,
                "isTouch": False,
                "isBreak": True,
                "isCriticalDisp": True,
                "isFastLateDisp": True,
                "fastCount": 0,
                "lateCount": 0,
                "isAchieveNewRecord": False,
                "isDeluxscoreNewRecord": False,
                "comboStatus": musicData["comboStatus"],
                "syncStatus": musicData["syncStatus"],
                "isClear": True,
                "beforeRating": userData["userData"]["playerRating"],
                "afterRating": userData["userData"]["playerRating"],
                "beforeGrade": 0,
                "afterGrade": 0,
                "afterGradeRank": 0,
                "beforeDeluxRating": userData["userData"]["playerRating"],
                "afterDeluxRating": userData["userData"]["playerRating"],
                "isPlayTutorial": False,
                "isEventMode": False,
                "isFreedomMode": False,
                "playMode": 0,
                "isNewFree": False,
                "trialPlayAchievement": -1,
                "extNum1": 0,
                "extNum2": 0,
                "extNum4": 101,
                "extBool1": False,
                "extBool2": False,
            }
        ],
        "upsertUserAll": {
            "userData": [
                {
                    "accessCode": "",
                    "userName": userData["userData"]["userName"],
                    "isNetMember": 1,
                    "point": userData["userData"]["point"],
                    "totalPoint": userData["userData"]["totalPoint"],
                    "iconId": userData["userData"]["iconId"],
                    "plateId": userData["userData"]["plateId"],
                    "titleId": userData["userData"]["titleId"],
                    "partnerId": userData["userData"]["partnerId"],
                    "frameId": userData["userData"]["frameId"],
                    "selectMapId": userData["userData"]["selectMapId"],
                    "totalAwake": userData["userData"]["totalAwake"],
                    "gradeRating": userData["userData"]["gradeRating"],
                    "musicRating": userData["userData"]["musicRating"],
                    "playerRating": userData["userData"]["playerRating"],
                    "highestRating": userData["userData"]["highestRating"],
                    "gradeRank": userData["userData"]["gradeRank"],
                    "classRank": userData["userData"]["classRank"],
                    "courseRank": userData["userData"]["courseRank"],
                    "charaSlot": userData["userData"]["charaSlot"],
                    "charaLockSlot": userData["userData"]["charaLockSlot"],
                    "contentBit": userData["userData"]["contentBit"],
                    "playCount": userData["userData"]["playCount"] + 1,
                    "currentPlayCount": userData["userData"]["currentPlayCount"] + 1,
                    "renameCredit": userData["userData"]["renameCredit"],
                    "mapStock": userData["userData"]["mapStock"],
                    "eventWatchedDate": userData["userData"]["eventWatchedDate"],
                    "lastGameId": "SDGB",
                    "lastRomVersion": userData["userData"]["lastRomVersion"],
                    "lastDataVersion": userData["userData"]["lastDataVersion"],
                    "lastLoginDate": loginDate,
                    "lastPlayDate": datetime.now(
                        pytz.timezone("Asia/Shanghai")
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    + ".0",
                    "lastPlayCredit": 1,
                    "lastPlayMode": 0,
                    "lastPlaceId": config.place_id,
                    "lastPlaceName": config.place_name,
                    "lastAllNetId": 0,
                    "lastRegionId": config.region_id,
                    "lastRegionName": config.region_name,
                    "lastClientId": config.client_id,
                    "lastCountryCode": "CHN",
                    "lastSelectEMoney": userData["userData"]["lastSelectEMoney"],
                    "lastSelectTicket": userData["userData"]["lastSelectTicket"],
                    "lastSelectCourse": userData["userData"]["lastSelectCourse"],
                    "lastCountCourse": userData["userData"]["lastCountCourse"],
                    "firstGameId": userData["userData"]["firstGameId"],
                    "firstRomVersion": userData["userData"]["firstRomVersion"],
                    "firstDataVersion": userData["userData"]["firstDataVersion"],
                    "firstPlayDate": userData["userData"]["firstPlayDate"],
                    "compatibleCmVersion": userData["userData"]["compatibleCmVersion"],
                    "dailyBonusDate": userData["userData"]["dailyBonusDate"],
                    "dailyCourseBonusDate": userData["userData"][
                        "dailyCourseBonusDate"
                    ],
                    "lastPairLoginDate": userData["userData"]["lastPairLoginDate"],
                    "lastTrialPlayDate": userData["userData"]["lastTrialPlayDate"],
                    "playVsCount": userData["userData"]["playVsCount"],
                    "playSyncCount": userData["userData"]["playSyncCount"],
                    "winCount": userData["userData"]["winCount"],
                    "helpCount": userData["userData"]["helpCount"],
                    "comboCount": userData["userData"]["comboCount"],
                    "totalDeluxscore": userData["userData"]["totalDeluxscore"],
                    "totalBasicDeluxscore": userData["userData"][
                        "totalBasicDeluxscore"
                    ],
                    "totalAdvancedDeluxscore": userData["userData"][
                        "totalAdvancedDeluxscore"
                    ],
                    "totalExpertDeluxscore": userData["userData"][
                        "totalExpertDeluxscore"
                    ],
                    "totalMasterDeluxscore": userData["userData"][
                        "totalMasterDeluxscore"
                    ],
                    "totalReMasterDeluxscore": userData["userData"][
                        "totalReMasterDeluxscore"
                    ],
                    "totalSync": userData["userData"]["totalSync"],
                    "totalBasicSync": userData["userData"]["totalBasicSync"],
                    "totalAdvancedSync": userData["userData"]["totalAdvancedSync"],
                    "totalExpertSync": userData["userData"]["totalExpertSync"],
                    "totalMasterSync": userData["userData"]["totalMasterSync"],
                    "totalReMasterSync": userData["userData"]["totalReMasterSync"],
                    "totalAchievement": userData["userData"]["totalAchievement"],
                    "totalBasicAchievement": userData["userData"][
                        "totalBasicAchievement"
                    ],
                    "totalAdvancedAchievement": userData["userData"][
                        "totalAdvancedAchievement"
                    ],
                    "totalExpertAchievement": userData["userData"][
                        "totalExpertAchievement"
                    ],
                    "totalMasterAchievement": userData["userData"][
                        "totalMasterAchievement"
                    ],
                    "totalReMasterAchievement": userData["userData"][
                        "totalReMasterAchievement"
                    ],
                    "playerOldRating": userData["userData"]["playerOldRating"],
                    "playerNewRating": userData["userData"]["playerNewRating"],
                    "banState": userData["banState"],
                    "friendRegistSkip": userData["userData"]["friendRegistSkip"],
                    "dateTime": TimeStamp,
                }
            ],
            "userExtend": [userExtend["userExtend"]],
            "userOption": [userOption["userOption"]],
            "userCharacterList": [],
            "userGhost": [],
            "userMapList": [],
            "userLoginBonusList": [],
            "userRatingList": [userRating["userRating"]],
            "userItemList": [],
            "userMusicDetailList": [musicData],
            "userCourseList": [],
            "userFriendSeasonRankingList": [],
            "userChargeList": userChargeList["userChargeList"],
            "userFavoriteList": [
                {"itemKind": 3, "itemIdList": []},
                {"itemKind": 1, "itemIdList": []},
                {"itemKind": 2, "itemIdList": []},
                {"itemKind": 10, "itemIdList": []},
                {"itemKind": 11, "itemIdList": []},
            ],
            "userActivityList": [userActivity["userActivity"]],
            "userMissionDataList": [
                {
                    "type": userMissionDataList["userMissionDataList"][0]["type"],
                    "difficulty": userMissionDataList["userMissionDataList"][0][
                        "difficulty"
                    ],
                    "targetGenreId": userMissionDataList["userMissionDataList"][0][
                        "targetGenreId"
                    ],
                    "targetGenreTableId": userMissionDataList["userMissionDataList"][0][
                        "targetGenreTableId"
                    ],
                    "conditionGenreId": userMissionDataList["userMissionDataList"][0][
                        "conditionGenreId"
                    ],
                    "conditionGenreTableId": userMissionDataList["userMissionDataList"][
                        0
                    ]["conditionGenreTableId"],
                    "clearFlag": userMissionDataList["userMissionDataList"][0][
                        "clearFlag"
                    ],
                },
                {
                    "type": userMissionDataList["userMissionDataList"][1]["type"],
                    "difficulty": userMissionDataList["userMissionDataList"][1][
                        "difficulty"
                    ],
                    "targetGenreId": userMissionDataList["userMissionDataList"][1][
                        "targetGenreId"
                    ],
                    "targetGenreTableId": userMissionDataList["userMissionDataList"][1][
                        "targetGenreTableId"
                    ],
                    "conditionGenreId": userMissionDataList["userMissionDataList"][1][
                        "conditionGenreId"
                    ],
                    "conditionGenreTableId": userMissionDataList["userMissionDataList"][
                        1
                    ]["conditionGenreTableId"],
                    "clearFlag": userMissionDataList["userMissionDataList"][1][
                        "clearFlag"
                    ],
                },
                {
                    "type": userMissionDataList["userMissionDataList"][2]["type"],
                    "difficulty": userMissionDataList["userMissionDataList"][2][
                        "difficulty"
                    ],
                    "targetGenreId": userMissionDataList["userMissionDataList"][2][
                        "targetGenreId"
                    ],
                    "targetGenreTableId": userMissionDataList["userMissionDataList"][2][
                        "targetGenreTableId"
                    ],
                    "conditionGenreId": userMissionDataList["userMissionDataList"][2][
                        "conditionGenreId"
                    ],
                    "conditionGenreTableId": userMissionDataList["userMissionDataList"][
                        2
                    ]["conditionGenreTableId"],
                    "clearFlag": userMissionDataList["userMissionDataList"][2][
                        "clearFlag"
                    ],
                },
                {
                    "type": userMissionDataList["userMissionDataList"][3]["type"],
                    "difficulty": userMissionDataList["userMissionDataList"][3][
                        "difficulty"
                    ],
                    "targetGenreId": userMissionDataList["userMissionDataList"][3][
                        "targetGenreId"
                    ],
                    "targetGenreTableId": userMissionDataList["userMissionDataList"][3][
                        "targetGenreTableId"
                    ],
                    "conditionGenreId": userMissionDataList["userMissionDataList"][3][
                        "conditionGenreId"
                    ],
                    "conditionGenreTableId": userMissionDataList["userMissionDataList"][
                        3
                    ]["conditionGenreTableId"],
                    "clearFlag": userMissionDataList["userMissionDataList"][3][
                        "clearFlag"
                    ],
                },
                {
                    "type": userMissionDataList["userMissionDataList"][4]["type"],
                    "difficulty": userMissionDataList["userMissionDataList"][4][
                        "difficulty"
                    ],
                    "targetGenreId": userMissionDataList["userMissionDataList"][4][
                        "targetGenreId"
                    ],
                    "targetGenreTableId": userMissionDataList["userMissionDataList"][4][
                        "targetGenreTableId"
                    ],
                    "conditionGenreId": userMissionDataList["userMissionDataList"][4][
                        "conditionGenreId"
                    ],
                    "conditionGenreTableId": userMissionDataList["userMissionDataList"][
                        4
                    ]["conditionGenreTableId"],
                    "clearFlag": userMissionDataList["userMissionDataList"][4][
                        "clearFlag"
                    ],
                },
                {
                    "type": userMissionDataList["userMissionDataList"][5]["type"],
                    "difficulty": userMissionDataList["userMissionDataList"][5][
                        "difficulty"
                    ],
                    "targetGenreId": userMissionDataList["userMissionDataList"][5][
                        "targetGenreId"
                    ],
                    "targetGenreTableId": userMissionDataList["userMissionDataList"][5][
                        "targetGenreTableId"
                    ],
                    "conditionGenreId": userMissionDataList["userMissionDataList"][5][
                        "conditionGenreId"
                    ],
                    "conditionGenreTableId": userMissionDataList["userMissionDataList"][
                        5
                    ]["conditionGenreTableId"],
                    "clearFlag": userMissionDataList["userMissionDataList"][5][
                        "clearFlag"
                    ],
                },
            ],
            "userWeeklyData": {
                "lastLoginWeek": userMissionDataList["userWeeklyData"]["lastLoginWeek"],
                "beforeLoginWeek": userMissionDataList["userWeeklyData"][
                    "beforeLoginWeek"
                ],
                "friendBonusFlag": userMissionDataList["userWeeklyData"][
                    "friendBonusFlag"
                ],
            },
            "userGamePlaylogList": [
                {
                    "playlogId": loginId,
                    "version": userData["userData"]["lastRomVersion"],
                    "playDate": datetime.now(pytz.timezone("Asia/Shanghai")).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    + ".0",
                    "playMode": 0,
                    "useTicketId": -1,
                    "playCredit": 1,
                    "playTrack": 1,
                    "clientId": config.client_id,
                    "isPlayTutorial": False,
                    "isEventMode": False,
                    "isNewFree": False,
                    "playCount": 0,
                    "playSpecial": CalcRandom(),
                    "playOtherUserId": 0,
                }
            ],
            "user2pPlaylog": {
                "userId1": 0,
                "userId2": 0,
                "userName1": "",
                "userName2": "",
                "regionId": 0,
                "placeId": 0,
                "user2pPlaylogDetailList": [],
            },
            "userIntimateList": [],
            "userShopItemStockList": [],
            "userGetPointList": [],
            "userTradeItemList": [],
            "userFavoritemusicList": [],
            "userKaleidxScopeList": [],
            "isNewCharacterList": "",
            "isNewMapList": "",
            "isNewLoginBonusList": "",
            "isNewItemList": "",
            "isNewMusicDetailList": "0",
            "isNewCourseList": "",
            "isNewFavoriteList": "11111",
            "isNewFriendSeasonRankingList": "",
            "isNewUserIntimateList": "",
            "isNewFavoritemusicList": "",
            "isNewKaleidxScopeList": "",
        },
    }

    logger.info(
        f"🫥 [INFO] userId: '{userId}', loginId: '{loginId}', loginDate: '{loginDate}', timestamp: '{TimeStamp}'"
    )
    return requestData_UserAll
