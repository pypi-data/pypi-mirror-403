"""Game-specific API facades."""

from .d3 import D3API
from .hs import HearthstoneAPI
from .sc2 import SC2API
from .wow import WowAPI

__all__ = ["D3API", "HearthstoneAPI", "SC2API", "WowAPI"]
