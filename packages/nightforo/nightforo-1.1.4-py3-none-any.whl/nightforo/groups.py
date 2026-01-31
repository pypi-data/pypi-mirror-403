from enum import Enum

__all__ = ("ArzGuardGroupsIdsEnum", "ArzGuardGroupsNamesEnum")


class ArzGuardGroupsIdsEnum(Enum):
    FORUM_MANAGERS = "3"
    FORUM_ADMINISTRATORS = "25"
    GAME_ADMINISTRATORS = "17"
    SERVER_MANAGERS = "33"
    HEAD_MODERATORS = "4"
    SERVICE_ACCOUNTS = "19"
    DEPUTY_HEAD_MODERATORS = "9"
    TECH_MODERATORS = "32"
    CURATORS_OF_MODERATION = "20"
    SENIOR_MODERATORS = "7"
    MODERATORS = "8"


class ArzGuardGroupsNamesEnum(Enum):
    DEPUTY_HEAD_MODERATORS = "(08) Заместители главных модераторов"
    TECH_MODERATORS = "(09) Технические модераторы"
    CURATORS_OF_MODERATION = "(10) Кураторы модерации"
    SENIOR_MODERATORS = "(11) Старшие модераторы"
    MODERATORS = "(12) Модераторы"
    USERS = "(13) Пользователи"
