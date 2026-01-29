"""Type stubs for WoW API - auto-generated for IDE autocomplete."""

from typing import Any

from ..core.executor import ApiResponse
from ..types import Locale, Region

class WowGameDataAPI:
    """Auto-generated stub for IDE autocomplete."""

    def get_achievement_categories_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of achievement categories."""
        ...

    async def get_achievement_categories_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of achievement categories."""
        ...

    def get_achievement_category(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        category_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an achievement category by ID."""
        ...

    async def get_achievement_category_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        category_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an achievement category by ID."""
        ...

    def get_achievements_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of achievements."""
        ...

    async def get_achievements_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of achievements."""
        ...

    def get_achievement(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        achievement_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an achievement by ID."""
        ...

    async def get_achievement_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        achievement_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an achievement by ID."""
        ...

    def get_achievement_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        achievement_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for an achievement."""
        ...

    async def get_achievement_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        achievement_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for an achievement."""
        ...

    def get_decor_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of decor items."""
        ...

    async def get_decor_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of decor items."""
        ...

    def get_decor(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        decor_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a decor item by ID."""
        ...

    async def get_decor_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        decor_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a decor item by ID."""
        ...

    def search_decor(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for decor items."""
        ...

    async def search_decor_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for decor items."""
        ...

    def get_fixture_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of fixtures."""
        ...

    async def get_fixture_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of fixtures."""
        ...

    def get_fixture(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        fixture_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a fixture by ID."""
        ...

    async def get_fixture_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        fixture_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a fixture by ID."""
        ...

    def search_fixture(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for fixtures."""
        ...

    async def search_fixture_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for fixtures."""
        ...

    def get_fixture_hook_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of fixture hooks."""
        ...

    async def get_fixture_hook_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of fixture hooks."""
        ...

    def get_fixture_hook(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        fixture_hook_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a fixture hook by ID."""
        ...

    async def get_fixture_hook_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        fixture_hook_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a fixture hook by ID."""
        ...

    def search_fixture_hook(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for fixture hooks."""
        ...

    async def search_fixture_hook_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for fixture hooks."""
        ...

    def get_room_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of rooms."""
        ...

    async def get_room_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of rooms."""
        ...

    def get_room(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        room_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a room by ID."""
        ...

    async def get_room_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        room_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a room by ID."""
        ...

    def search_room(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for rooms."""
        ...

    async def search_room_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for rooms."""
        ...

    def get_auctions(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        connected_realm_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get auction house data for a connected realm."""
        ...

    async def get_auctions_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        connected_realm_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get auction house data for a connected realm."""
        ...

    def get_commodities(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get commodity auction data."""
        ...

    async def get_commodities_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get commodity auction data."""
        ...

    def get_azerite_essences_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of azerite essences."""
        ...

    async def get_azerite_essences_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of azerite essences."""
        ...

    def get_azerite_essence(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        essence_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an azerite essence by ID."""
        ...

    async def get_azerite_essence_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        essence_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an azerite essence by ID."""
        ...

    def search_azerite_essence(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for azerite essences."""
        ...

    async def search_azerite_essence_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for azerite essences."""
        ...

    def get_azerite_essence_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        essence_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for an azerite essence."""
        ...

    async def get_azerite_essence_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        essence_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for an azerite essence."""
        ...

    def get_connected_realms_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of connected realms."""
        ...

    async def get_connected_realms_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of connected realms."""
        ...

    def get_connected_realm(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        connected_realm_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a connected realm by ID."""
        ...

    async def get_connected_realm_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        connected_realm_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a connected realm by ID."""
        ...

    def search_connected_realm(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for connected realms."""
        ...

    async def search_connected_realm_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for connected realms."""
        ...

    def get_covenant_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of covenants."""
        ...

    async def get_covenant_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of covenants."""
        ...

    def get_covenant(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        covenant_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a covenant by ID."""
        ...

    async def get_covenant_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        covenant_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a covenant by ID."""
        ...

    def get_covenant_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        covenant_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a covenant."""
        ...

    async def get_covenant_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        covenant_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a covenant."""
        ...

    def get_soulbind_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of soulbinds."""
        ...

    async def get_soulbind_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of soulbinds."""
        ...

    def get_soulbind(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        soulbind_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a soulbind by ID."""
        ...

    async def get_soulbind_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        soulbind_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a soulbind by ID."""
        ...

    def get_conduit_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of conduits."""
        ...

    async def get_conduit_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of conduits."""
        ...

    def get_conduit(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        conduit_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a conduit by ID."""
        ...

    async def get_conduit_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        conduit_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a conduit by ID."""
        ...

    def get_creature_families_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of creature families."""
        ...

    async def get_creature_families_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of creature families."""
        ...

    def get_creature_family(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        creature_family_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a creature family by ID."""
        ...

    async def get_creature_family_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        creature_family_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a creature family by ID."""
        ...

    def get_creature_types_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of creature types."""
        ...

    async def get_creature_types_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of creature types."""
        ...

    def get_creature_type(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        creature_type_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a creature type by ID."""
        ...

    async def get_creature_type_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        creature_type_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a creature type by ID."""
        ...

    def get_creature(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        creature_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a creature by ID."""
        ...

    async def get_creature_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        creature_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a creature by ID."""
        ...

    def search_creature(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for creatures."""
        ...

    async def search_creature_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for creatures."""
        ...

    def get_creature_display_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        creature_display_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get display media for a creature."""
        ...

    async def get_creature_display_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        creature_display_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get display media for a creature."""
        ...

    def get_creature_family_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        creature_family_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a creature family."""
        ...

    async def get_creature_family_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        creature_family_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a creature family."""
        ...

    def get_guild_crest_components_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of guild crest components."""
        ...

    async def get_guild_crest_components_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of guild crest components."""
        ...

    def get_guild_crest_border_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        border_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a guild crest border."""
        ...

    async def get_guild_crest_border_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        border_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a guild crest border."""
        ...

    def get_guild_crest_emblem_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        emblem_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a guild crest emblem."""
        ...

    async def get_guild_crest_emblem_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        emblem_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a guild crest emblem."""
        ...

    def get_heirloom_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of heirlooms."""
        ...

    async def get_heirloom_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of heirlooms."""
        ...

    def get_heirloom(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        heirloom_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an heirloom by ID."""
        ...

    async def get_heirloom_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        heirloom_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an heirloom by ID."""
        ...

    def get_item_classes_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of item classes."""
        ...

    async def get_item_classes_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of item classes."""
        ...

    def get_item_class(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        class_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an item class by ID."""
        ...

    async def get_item_class_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        class_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an item class by ID."""
        ...

    def get_item_sets_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of item sets."""
        ...

    async def get_item_sets_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of item sets."""
        ...

    def get_item_set(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        set_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an item set by ID."""
        ...

    async def get_item_set_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        set_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an item set by ID."""
        ...

    def get_item_subclass(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        class_id: int,
        subclass_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an item subclass."""
        ...

    async def get_item_subclass_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        class_id: int,
        subclass_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an item subclass."""
        ...

    def get_item(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        item_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an item by ID."""
        ...

    async def get_item_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        item_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an item by ID."""
        ...

    def get_item_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        item_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for an item."""
        ...

    async def get_item_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        item_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for an item."""
        ...

    def search_item(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for items."""
        ...

    async def search_item_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for items."""
        ...

    def get_journal_expansions_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of journal expansions."""
        ...

    async def get_journal_expansions_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of journal expansions."""
        ...

    def get_journal_expansion(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        expansion_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a journal expansion by ID."""
        ...

    async def get_journal_expansion_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        expansion_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a journal expansion by ID."""
        ...

    def get_journal_encounters_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of journal encounters."""
        ...

    async def get_journal_encounters_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of journal encounters."""
        ...

    def get_journal_encounter(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        encounter_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a journal encounter by ID."""
        ...

    async def get_journal_encounter_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        encounter_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a journal encounter by ID."""
        ...

    def search_journal_encounter(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for journal encounters."""
        ...

    async def search_journal_encounter_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for journal encounters."""
        ...

    def get_journal_instances_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of journal instances."""
        ...

    async def get_journal_instances_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of journal instances."""
        ...

    def get_journal_instance(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        instance_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a journal instance by ID."""
        ...

    async def get_journal_instance_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        instance_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a journal instance by ID."""
        ...

    def get_journal_instance_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        instance_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a journal instance."""
        ...

    async def get_journal_instance_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        instance_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a journal instance."""
        ...

    def search_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for media."""
        ...

    async def search_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for media."""
        ...

    def get_modified_crafting_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get the modified crafting index."""
        ...

    async def get_modified_crafting_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get the modified crafting index."""
        ...

    def get_modified_crafting_category_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of modified crafting categories."""
        ...

    async def get_modified_crafting_category_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of modified crafting categories."""
        ...

    def get_modified_crafting_category(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        category_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a modified crafting category by ID."""
        ...

    async def get_modified_crafting_category_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        category_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a modified crafting category by ID."""
        ...

    def get_modified_crafting_reagent_slot_type_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of modified crafting reagent slot types."""
        ...

    async def get_modified_crafting_reagent_slot_type_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of modified crafting reagent slot types."""
        ...

    def get_modified_crafting_reagent_slot_type(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        slot_type_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a modified crafting reagent slot type by ID."""
        ...

    async def get_modified_crafting_reagent_slot_type_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        slot_type_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a modified crafting reagent slot type by ID."""
        ...

    def get_mounts_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of mounts."""
        ...

    async def get_mounts_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of mounts."""
        ...

    def get_mount(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        mount_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a mount by ID."""
        ...

    async def get_mount_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        mount_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a mount by ID."""
        ...

    def search_mount(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for mounts."""
        ...

    async def search_mount_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for mounts."""
        ...

    def get_mythic_keystone_affixes_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of mythic keystone affixes."""
        ...

    async def get_mythic_keystone_affixes_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of mythic keystone affixes."""
        ...

    def get_mythic_keystone_affix(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        affix_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a mythic keystone affix by ID."""
        ...

    async def get_mythic_keystone_affix_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        affix_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a mythic keystone affix by ID."""
        ...

    def get_mythic_keystone_affix_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        affix_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a mythic keystone affix."""
        ...

    async def get_mythic_keystone_affix_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        affix_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a mythic keystone affix."""
        ...

    def get_mythic_keystone_dungeons_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of mythic keystone dungeons."""
        ...

    async def get_mythic_keystone_dungeons_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of mythic keystone dungeons."""
        ...

    def get_mythic_keystone_dungeon(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        dungeon_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a mythic keystone dungeon by ID."""
        ...

    async def get_mythic_keystone_dungeon_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        dungeon_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a mythic keystone dungeon by ID."""
        ...

    def get_mythic_keystone_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get the mythic keystone index."""
        ...

    async def get_mythic_keystone_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get the mythic keystone index."""
        ...

    def get_mythic_keystone_periods_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of mythic keystone periods."""
        ...

    async def get_mythic_keystone_periods_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of mythic keystone periods."""
        ...

    def get_mythic_keystone_period(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        period_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a mythic keystone period by ID."""
        ...

    async def get_mythic_keystone_period_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        period_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a mythic keystone period by ID."""
        ...

    def get_mythic_keystone_seasons_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of mythic keystone seasons."""
        ...

    async def get_mythic_keystone_seasons_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of mythic keystone seasons."""
        ...

    def get_mythic_keystone_season(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a mythic keystone season by ID."""
        ...

    async def get_mythic_keystone_season_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a mythic keystone season by ID."""
        ...

    def get_mythic_keystone_leaderboards_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        connected_realm_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of mythic keystone leaderboards for a connected realm."""
        ...

    async def get_mythic_keystone_leaderboards_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        connected_realm_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of mythic keystone leaderboards for a connected realm."""
        ...

    def get_mythic_keystone_leaderboard(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        connected_realm_id: int,
        dungeon_id: int,
        period_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a mythic keystone leaderboard."""
        ...

    async def get_mythic_keystone_leaderboard_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        connected_realm_id: int,
        dungeon_id: int,
        period_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a mythic keystone leaderboard."""
        ...

    def get_mythic_raid_leaderboard(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        raid: str,
        faction: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get the mythic raid hall of fame leaderboard."""
        ...

    async def get_mythic_raid_leaderboard_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        raid: str,
        faction: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get the mythic raid hall of fame leaderboard."""
        ...

    def get_pets_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of battle pets."""
        ...

    async def get_pets_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of battle pets."""
        ...

    def get_pet(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        pet_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a battle pet by ID."""
        ...

    async def get_pet_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        pet_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a battle pet by ID."""
        ...

    def get_pet_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        pet_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a battle pet."""
        ...

    async def get_pet_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        pet_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a battle pet."""
        ...

    def get_pet_abilities_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of pet abilities."""
        ...

    async def get_pet_abilities_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of pet abilities."""
        ...

    def get_pet_ability(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        ability_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a pet ability by ID."""
        ...

    async def get_pet_ability_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        ability_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a pet ability by ID."""
        ...

    def get_pet_ability_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        ability_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a pet ability."""
        ...

    async def get_pet_ability_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        ability_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a pet ability."""
        ...

    def get_playable_classes_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of playable classes."""
        ...

    async def get_playable_classes_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of playable classes."""
        ...

    def get_playable_class(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        class_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a playable class by ID."""
        ...

    async def get_playable_class_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        class_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a playable class by ID."""
        ...

    def get_playable_class_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        class_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a playable class."""
        ...

    async def get_playable_class_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        class_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a playable class."""
        ...

    def get_pvp_talent_slots(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        class_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get PvP talent slots for a playable class."""
        ...

    async def get_pvp_talent_slots_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        class_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get PvP talent slots for a playable class."""
        ...

    def get_playable_races_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of playable races."""
        ...

    async def get_playable_races_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of playable races."""
        ...

    def get_playable_race(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        race_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a playable race by ID."""
        ...

    async def get_playable_race_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        race_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a playable race by ID."""
        ...

    def get_playable_specializations_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of playable specializations."""
        ...

    async def get_playable_specializations_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of playable specializations."""
        ...

    def get_playable_specialization(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        spec_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a playable specialization by ID."""
        ...

    async def get_playable_specialization_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        spec_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a playable specialization by ID."""
        ...

    def get_playable_specialization_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        spec_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a playable specialization."""
        ...

    async def get_playable_specialization_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        spec_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a playable specialization."""
        ...

    def get_power_types_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of power types."""
        ...

    async def get_power_types_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of power types."""
        ...

    def get_power_type(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        power_type_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a power type by ID."""
        ...

    async def get_power_type_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        power_type_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a power type by ID."""
        ...

    def get_professions_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of professions."""
        ...

    async def get_professions_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of professions."""
        ...

    def get_profession(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        profession_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a profession by ID."""
        ...

    async def get_profession_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        profession_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a profession by ID."""
        ...

    def get_profession_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        profession_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a profession."""
        ...

    async def get_profession_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        profession_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a profession."""
        ...

    def get_profession_skill_tier(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        profession_id: int,
        skill_tier_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a profession skill tier."""
        ...

    async def get_profession_skill_tier_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        profession_id: int,
        skill_tier_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a profession skill tier."""
        ...

    def get_recipe(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        recipe_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a recipe by ID."""
        ...

    async def get_recipe_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        recipe_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a recipe by ID."""
        ...

    def get_recipe_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        recipe_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a recipe."""
        ...

    async def get_recipe_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        recipe_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a recipe."""
        ...

    def get_pvp_seasons_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of PvP seasons."""
        ...

    async def get_pvp_seasons_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of PvP seasons."""
        ...

    def get_pvp_season(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a PvP season by ID."""
        ...

    async def get_pvp_season_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a PvP season by ID."""
        ...

    def get_pvp_leaderboards_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of PvP leaderboards for a season."""
        ...

    async def get_pvp_leaderboards_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of PvP leaderboards for a season."""
        ...

    def get_pvp_leaderboard(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
        bracket: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a PvP leaderboard for a bracket."""
        ...

    async def get_pvp_leaderboard_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
        bracket: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a PvP leaderboard for a bracket."""
        ...

    def get_pvp_rewards_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of PvP rewards for a season."""
        ...

    async def get_pvp_rewards_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of PvP rewards for a season."""
        ...

    def get_pvp_tiers_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of PvP tiers."""
        ...

    async def get_pvp_tiers_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of PvP tiers."""
        ...

    def get_pvp_tier(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        tier_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a PvP tier by ID."""
        ...

    async def get_pvp_tier_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        tier_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a PvP tier by ID."""
        ...

    def get_pvp_tier_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        tier_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a PvP tier."""
        ...

    async def get_pvp_tier_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        tier_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a PvP tier."""
        ...

    def get_quests_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of quests."""
        ...

    async def get_quests_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of quests."""
        ...

    def get_quest(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        quest_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a quest by ID."""
        ...

    async def get_quest_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        quest_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a quest by ID."""
        ...

    def get_quest_categories_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of quest categories."""
        ...

    async def get_quest_categories_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of quest categories."""
        ...

    def get_quest_category(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        category_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a quest category by ID."""
        ...

    async def get_quest_category_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        category_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a quest category by ID."""
        ...

    def get_quest_areas_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of quest areas."""
        ...

    async def get_quest_areas_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of quest areas."""
        ...

    def get_quest_area(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        area_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a quest area by ID."""
        ...

    async def get_quest_area_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        area_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a quest area by ID."""
        ...

    def get_quest_types_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of quest types."""
        ...

    async def get_quest_types_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of quest types."""
        ...

    def get_quest_type(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        type_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a quest type by ID."""
        ...

    async def get_quest_type_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        type_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a quest type by ID."""
        ...

    def get_realms_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of realms."""
        ...

    async def get_realms_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of realms."""
        ...

    def get_realm(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a realm by slug."""
        ...

    async def get_realm_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a realm by slug."""
        ...

    def search_realm(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for realms."""
        ...

    async def search_realm_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for realms."""
        ...

    def get_regions_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of regions."""
        ...

    async def get_regions_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of regions."""
        ...

    def get_region(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a region by ID."""
        ...

    async def get_region_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a region by ID."""
        ...

    def get_reputation_factions_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of reputation factions."""
        ...

    async def get_reputation_factions_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of reputation factions."""
        ...

    def get_reputation_faction(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        faction_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a reputation faction by ID."""
        ...

    async def get_reputation_faction_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        faction_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a reputation faction by ID."""
        ...

    def get_reputation_tiers_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of reputation tiers."""
        ...

    async def get_reputation_tiers_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of reputation tiers."""
        ...

    def get_reputation_tiers(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        tiers_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get reputation tiers by ID."""
        ...

    async def get_reputation_tiers_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        tiers_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get reputation tiers by ID."""
        ...

    def get_spell(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        spell_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a spell by ID."""
        ...

    async def get_spell_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        spell_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a spell by ID."""
        ...

    def get_spell_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        spell_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a spell."""
        ...

    async def get_spell_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        spell_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a spell."""
        ...

    def search_spell(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for spells."""
        ...

    async def search_spell_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
        **kwargs: Any,
    ) -> ApiResponse:
        """Search for spells."""
        ...

    def get_talents_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of talents."""
        ...

    async def get_talents_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of talents."""
        ...

    def get_talent(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        talent_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a talent by ID."""
        ...

    async def get_talent_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        talent_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a talent by ID."""
        ...

    def get_pvp_talents_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of PvP talents."""
        ...

    async def get_pvp_talents_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of PvP talents."""
        ...

    def get_pvp_talent(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        talent_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a PvP talent by ID."""
        ...

    async def get_pvp_talent_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        talent_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a PvP talent by ID."""
        ...

    def get_talent_tree_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of talent trees."""
        ...

    async def get_talent_tree_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of talent trees."""
        ...

    def get_talent_tree(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        tree_id: int,
        spec_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a talent tree for a specialization."""
        ...

    async def get_talent_tree_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        tree_id: int,
        spec_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a talent tree for a specialization."""
        ...

    def get_talent_tree_nodes(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        tree_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get talent tree nodes."""
        ...

    async def get_talent_tree_nodes_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        tree_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get talent tree nodes."""
        ...

    def get_tech_talent_tree_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of tech talent trees."""
        ...

    async def get_tech_talent_tree_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of tech talent trees."""
        ...

    def get_tech_talent_tree(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        tree_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a tech talent tree by ID."""
        ...

    async def get_tech_talent_tree_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        tree_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a tech talent tree by ID."""
        ...

    def get_tech_talent_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of tech talents."""
        ...

    async def get_tech_talent_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of tech talents."""
        ...

    def get_tech_talent(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        talent_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a tech talent by ID."""
        ...

    async def get_tech_talent_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        talent_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a tech talent by ID."""
        ...

    def get_tech_talent_media(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        talent_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a tech talent."""
        ...

    async def get_tech_talent_media_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        talent_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get media for a tech talent."""
        ...

    def get_titles_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of titles."""
        ...

    async def get_titles_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of titles."""
        ...

    def get_title(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        title_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a title by ID."""
        ...

    async def get_title_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        title_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a title by ID."""
        ...

    def get_toy_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of toys."""
        ...

    async def get_toy_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get an index of toys."""
        ...

    def get_toy(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        toy_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a toy by ID."""
        ...

    async def get_toy_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        toy_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get a toy by ID."""
        ...

    def get_token_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get the WoW token index."""
        ...

    async def get_token_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get the WoW token index."""
        ...

class WowProfileAPI:
    """Auto-generated stub for IDE autocomplete."""

    def get_account_profile_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get account profile summary (requires OAuth token)."""
        ...

    async def get_account_profile_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get account profile summary (requires OAuth token)."""
        ...

    def get_protected_character_profile_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        realm_id: int,
        character_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get protected character profile summary (requires OAuth token)."""
        ...

    async def get_protected_character_profile_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        realm_id: int,
        character_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get protected character profile summary (requires OAuth token)."""
        ...

    def get_account_collections_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get account collections index (requires OAuth token)."""
        ...

    async def get_account_collections_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get account collections index (requires OAuth token)."""
        ...

    def get_account_mounts_collection_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get account mounts collection (requires OAuth token)."""
        ...

    async def get_account_mounts_collection_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get account mounts collection (requires OAuth token)."""
        ...

    def get_account_pets_collection_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get account battle pets collection (requires OAuth token)."""
        ...

    async def get_account_pets_collection_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get account battle pets collection (requires OAuth token)."""
        ...

    def get_account_heirlooms_collection_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get account heirlooms collection (requires OAuth token)."""
        ...

    async def get_account_heirlooms_collection_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get account heirlooms collection (requires OAuth token)."""
        ...

    def get_account_toys_collection_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get account toys collection (requires OAuth token)."""
        ...

    async def get_account_toys_collection_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get account toys collection (requires OAuth token)."""
        ...

    def get_account_transmog_collection_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get account transmog collection (requires OAuth token)."""
        ...

    async def get_account_transmog_collection_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        access_token: str | None = None,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get account transmog collection (requires OAuth token)."""
        ...

    def get_character_achievements_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character achievements summary."""
        ...

    async def get_character_achievements_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character achievements summary."""
        ...

    def get_character_achievement_statistics(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character achievement statistics."""
        ...

    async def get_character_achievement_statistics_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character achievement statistics."""
        ...

    def get_character_appearance_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character appearance summary."""
        ...

    async def get_character_appearance_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character appearance summary."""
        ...

    def get_character_collections_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character collections index."""
        ...

    async def get_character_collections_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character collections index."""
        ...

    def get_character_mounts_collection_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character mounts collection."""
        ...

    async def get_character_mounts_collection_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character mounts collection."""
        ...

    def get_character_pets_collection_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character battle pets collection."""
        ...

    async def get_character_pets_collection_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character battle pets collection."""
        ...

    def get_character_heirlooms_collection_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character heirlooms collection."""
        ...

    async def get_character_heirlooms_collection_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character heirlooms collection."""
        ...

    def get_character_toys_collection_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character toys collection."""
        ...

    async def get_character_toys_collection_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character toys collection."""
        ...

    def get_character_transmog_collection_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character transmog collection."""
        ...

    async def get_character_transmog_collection_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character transmog collection."""
        ...

    def get_character_encounters_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character encounters summary."""
        ...

    async def get_character_encounters_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character encounters summary."""
        ...

    def get_character_dungeons(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character dungeon encounters."""
        ...

    async def get_character_dungeons_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character dungeon encounters."""
        ...

    def get_character_raids(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character raid encounters."""
        ...

    async def get_character_raids_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character raid encounters."""
        ...

    def get_character_equipment_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character equipment summary."""
        ...

    async def get_character_equipment_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character equipment summary."""
        ...

    def get_character_hunter_pets_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character hunter pets summary."""
        ...

    async def get_character_hunter_pets_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character hunter pets summary."""
        ...

    def get_character_media_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character media (avatar, portrait, etc.)."""
        ...

    async def get_character_media_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character media (avatar, portrait, etc.)."""
        ...

    def get_character_mythic_keystone_profile_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character mythic keystone profile index."""
        ...

    async def get_character_mythic_keystone_profile_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character mythic keystone profile index."""
        ...

    def get_character_mythic_keystone_season_details(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        season_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character mythic keystone season details."""
        ...

    async def get_character_mythic_keystone_season_details_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        season_id: int,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character mythic keystone season details."""
        ...

    def get_character_professions_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character professions summary."""
        ...

    async def get_character_professions_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character professions summary."""
        ...

    def get_character_profile_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character profile summary."""
        ...

    async def get_character_profile_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character profile summary."""
        ...

    def get_character_profile_status(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character profile status."""
        ...

    async def get_character_profile_status_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character profile status."""
        ...

    def get_character_pvp_bracket_statistics(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        pvp_bracket: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character PvP bracket statistics."""
        ...

    async def get_character_pvp_bracket_statistics_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        pvp_bracket: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character PvP bracket statistics."""
        ...

    def get_character_pvp_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character PvP summary."""
        ...

    async def get_character_pvp_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character PvP summary."""
        ...

    def get_character_quests(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character quests."""
        ...

    async def get_character_quests_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character quests."""
        ...

    def get_character_completed_quests(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character completed quests."""
        ...

    async def get_character_completed_quests_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character completed quests."""
        ...

    def get_character_reputations_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character reputations summary."""
        ...

    async def get_character_reputations_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character reputations summary."""
        ...

    def get_character_soulbinds(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character soulbinds."""
        ...

    async def get_character_soulbinds_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character soulbinds."""
        ...

    def get_character_specializations_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character specializations summary."""
        ...

    async def get_character_specializations_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character specializations summary."""
        ...

    def get_character_statistics_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character statistics summary."""
        ...

    async def get_character_statistics_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character statistics summary."""
        ...

    def get_character_titles_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character titles summary."""
        ...

    async def get_character_titles_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        character_name: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get character titles summary."""
        ...

    def get_guild(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        name_slug: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get guild by realm and name."""
        ...

    async def get_guild_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        name_slug: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get guild by realm and name."""
        ...

    def get_guild_activity(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        name_slug: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get guild activity."""
        ...

    async def get_guild_activity_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        name_slug: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get guild activity."""
        ...

    def get_guild_achievements(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        name_slug: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get guild achievements."""
        ...

    async def get_guild_achievements_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        name_slug: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get guild achievements."""
        ...

    def get_guild_roster(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        name_slug: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get guild roster."""
        ...

    async def get_guild_roster_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        realm_slug: str,
        name_slug: str,
        is_classic: bool = False,
    ) -> ApiResponse:
        """Get guild roster."""
        ...

class WowAPI:
    """World of Warcraft API facade."""

    game_data: WowGameDataAPI
    profile: WowProfileAPI
