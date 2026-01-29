from enum import StrEnum, auto


class DeployStage(StrEnum):
    UNKNOW = auto()

    LOCAL = auto()
    DEV = auto()
    TEST = auto()
    UAT = auto()

    PRD = auto()
