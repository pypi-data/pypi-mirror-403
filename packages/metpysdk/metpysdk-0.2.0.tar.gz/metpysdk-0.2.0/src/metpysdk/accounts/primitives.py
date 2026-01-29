from enum import Enum
from typing import TypedDict


class DlmmHttpError(Exception):
    def __init__(self, message):
        super().__init__(message)


class StrategyType(Enum):
    SpotOneSide = 0
    CurveOneSide = 1
    BidAskOneSide = 2
    SpotImBalanced = 3
    CurveImBalanced = 4
    BidAskImBalanced = 5
    SpotBalanced = 6
    CurveBalanced = 7
    BidAskBalanced = 8


class ActivationType(Enum):
    Slot = 0
    Timestamp = 1


class PositionVersion(Enum):
    V1 = "V1"
    V2 = "V2"


class StrategyParameters(TypedDict):
    max_bin_id: int
    min_bin_id: int
    strategy_type: StrategyType
