from __future__ import annotations

from enum import Enum


class NetworkType(Enum):
    LOCAL = "Isolated"
    SHARED = "Shared"
    VLAN = "L2"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls(value.lower())
