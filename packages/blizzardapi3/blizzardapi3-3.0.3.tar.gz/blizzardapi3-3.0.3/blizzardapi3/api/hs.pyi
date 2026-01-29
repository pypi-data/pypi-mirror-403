"""Type stubs for Hearthstone API - auto-generated for IDE autocomplete."""

from typing import Any

from ..core.executor import ApiResponse
from ..types import Locale, Region

class HSGameDataAPI:
    """Auto-generated stub for IDE autocomplete."""

    def search_cards(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for Hearthstone cards (supports filters as kwargs)."""
        ...

    async def search_cards_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for Hearthstone cards (supports filters as kwargs)."""
        ...

    def get_card(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        id_or_slug: str,
    ) -> ApiResponse:
        """Get a Hearthstone card by ID or slug."""
        ...

    async def get_card_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        id_or_slug: str,
    ) -> ApiResponse:
        """Get a Hearthstone card by ID or slug."""
        ...

    def search_card_backs(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for Hearthstone card backs (supports filters as kwargs)."""
        ...

    async def search_card_backs_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for Hearthstone card backs (supports filters as kwargs)."""
        ...

    def get_card_back(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        id_or_slug: str,
    ) -> ApiResponse:
        """Get a Hearthstone card back by ID or slug."""
        ...

    async def get_card_back_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        id_or_slug: str,
    ) -> ApiResponse:
        """Get a Hearthstone card back by ID or slug."""
        ...

    def get_deck(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        deck_code: str,
    ) -> ApiResponse:
        """Get a Hearthstone deck by deck code."""
        ...

    async def get_deck_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        deck_code: str,
    ) -> ApiResponse:
        """Get a Hearthstone deck by deck code."""
        ...

    def create_deck(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
    ) -> ApiResponse:
        """Create a Hearthstone deck (POST request)."""
        ...

    async def create_deck_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
    ) -> ApiResponse:
        """Create a Hearthstone deck (POST request)."""
        ...

    def get_metadata(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
    ) -> ApiResponse:
        """Get Hearthstone metadata (all types)."""
        ...

    async def get_metadata_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
    ) -> ApiResponse:
        """Get Hearthstone metadata (all types)."""
        ...

    def get_metadata_type(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        metadata_type: str,
    ) -> ApiResponse:
        """Get Hearthstone metadata by type (sets, setGroups, types, rarities, classes, etc.)."""
        ...

    async def get_metadata_type_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        metadata_type: str,
    ) -> ApiResponse:
        """Get Hearthstone metadata by type (sets, setGroups, types, rarities, classes, etc.)."""
        ...

class HearthstoneAPI:
    """Hearthstone API facade."""

    game_data: HSGameDataAPI
