from .position import ActiveBin, Position
from .primitives import dataclass


@dataclass
class GetPositionByUser:
    active_bin: ActiveBin
    user_positions: list[Position]

    def __init__(self, data: dict):
        self.active_bin = data["activeBin"]
        self.user_positions = data["userPositions"]
