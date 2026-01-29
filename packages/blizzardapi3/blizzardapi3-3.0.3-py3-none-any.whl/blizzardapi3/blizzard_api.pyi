"""Type stubs for BlizzardAPI - auto-generated for IDE autocomplete."""

from .api.d3 import D3API
from .api.hs import HearthstoneAPI
from .api.sc2 import SC2API
from .api.wow import WowAPI
from .types import Locale, Region

class BlizzardAPI:
    """Main Blizzard API client with full type hints."""

    wow: WowAPI
    d3: D3API
    hearthstone: HearthstoneAPI
    sc2: SC2API

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        region: Region | str = ...,
        locale: Locale | str | None = ...,
    ) -> None: ...
    def close(self) -> None: ...
    async def aclose(self) -> None: ...
    def __enter__(self) -> BlizzardAPI: ...
    def __exit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: object) -> None: ...
    async def __aenter__(self) -> BlizzardAPI: ...
    async def __aexit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: object) -> None: ...
