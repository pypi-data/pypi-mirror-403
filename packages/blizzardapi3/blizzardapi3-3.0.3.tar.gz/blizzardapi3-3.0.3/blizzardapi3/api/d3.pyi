"""Type stubs for Diablo 3 API - auto-generated for IDE autocomplete."""

from ..core.executor import ApiResponse
from ..types import Locale, Region

class D3GameDataAPI:
    """Auto-generated stub for IDE autocomplete."""

    def get_item(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        item_slug_and_id: int,
    ) -> ApiResponse:
        """Get an item by slug and ID (game data)."""
        ...

    async def get_item_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        item_slug_and_id: int,
    ) -> ApiResponse:
        """Get an item by slug and ID (game data)."""
        ...

    def get_item_type_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
    ) -> ApiResponse:
        """Get an index of item types."""
        ...

    async def get_item_type_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
    ) -> ApiResponse:
        """Get an index of item types."""
        ...

    def get_item_type(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        item_type_slug: str,
    ) -> ApiResponse:
        """Get an item type by slug."""
        ...

    async def get_item_type_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        item_type_slug: str,
    ) -> ApiResponse:
        """Get an item type by slug."""
        ...

    def get_recipe(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        artisan_slug: str,
        recipe_slug: str,
    ) -> ApiResponse:
        """Get a recipe for an artisan."""
        ...

    async def get_recipe_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        artisan_slug: str,
        recipe_slug: str,
    ) -> ApiResponse:
        """Get a recipe for an artisan."""
        ...

    def get_follower(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        follower_slug: str,
    ) -> ApiResponse:
        """Get a follower by slug."""
        ...

    async def get_follower_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        follower_slug: str,
    ) -> ApiResponse:
        """Get a follower by slug."""
        ...

    def get_artisan(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        artisan_slug: str,
    ) -> ApiResponse:
        """Get an artisan by slug."""
        ...

    async def get_artisan_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        artisan_slug: str,
    ) -> ApiResponse:
        """Get an artisan by slug."""
        ...

class D3CommunityAPI:
    """Auto-generated stub for IDE autocomplete."""

    def get_account(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        battletag: str,
    ) -> ApiResponse:
        """Get Diablo 3 account profile by BattleTag."""
        ...

    async def get_account_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        battletag: str,
    ) -> ApiResponse:
        """Get Diablo 3 account profile by BattleTag."""
        ...

    def get_hero(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        battletag: str,
        hero_id: int,
    ) -> ApiResponse:
        """Get a single hero by BattleTag and hero ID."""
        ...

    async def get_hero_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        battletag: str,
        hero_id: int,
    ) -> ApiResponse:
        """Get a single hero by BattleTag and hero ID."""
        ...

    def get_hero_items(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        battletag: str,
        hero_id: int,
    ) -> ApiResponse:
        """Get items for a hero."""
        ...

    async def get_hero_items_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        battletag: str,
        hero_id: int,
    ) -> ApiResponse:
        """Get items for a hero."""
        ...

    def get_hero_follower_items(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        battletag: str,
        hero_id: int,
    ) -> ApiResponse:
        """Get follower items for a hero."""
        ...

    async def get_hero_follower_items_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        battletag: str,
        hero_id: int,
    ) -> ApiResponse:
        """Get follower items for a hero."""
        ...

    def get_act_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
    ) -> ApiResponse:
        """Get an index of acts."""
        ...

    async def get_act_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
    ) -> ApiResponse:
        """Get an index of acts."""
        ...

    def get_act(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        act_id: int,
    ) -> ApiResponse:
        """Get an act by ID."""
        ...

    async def get_act_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        act_id: int,
    ) -> ApiResponse:
        """Get an act by ID."""
        ...

    def get_artisan(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        artisan_slug: str,
    ) -> ApiResponse:
        """Get an artisan by slug."""
        ...

    async def get_artisan_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        artisan_slug: str,
    ) -> ApiResponse:
        """Get an artisan by slug."""
        ...

    def get_recipe(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        artisan_slug: str,
        recipe_slug: str,
    ) -> ApiResponse:
        """Get a recipe for an artisan."""
        ...

    async def get_recipe_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        artisan_slug: str,
        recipe_slug: str,
    ) -> ApiResponse:
        """Get a recipe for an artisan."""
        ...

    def get_follower(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        follower_slug: str,
    ) -> ApiResponse:
        """Get a follower by slug."""
        ...

    async def get_follower_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        follower_slug: str,
    ) -> ApiResponse:
        """Get a follower by slug."""
        ...

    def get_character_class(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        class_slug: str,
    ) -> ApiResponse:
        """Get a character class by slug."""
        ...

    async def get_character_class_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        class_slug: str,
    ) -> ApiResponse:
        """Get a character class by slug."""
        ...

    def get_api_skill(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        class_slug: str,
        skill_slug: str,
    ) -> ApiResponse:
        """Get a skill for a character class."""
        ...

    async def get_api_skill_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        class_slug: str,
        skill_slug: str,
    ) -> ApiResponse:
        """Get a skill for a character class."""
        ...

    def get_item_type_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
    ) -> ApiResponse:
        """Get an index of item types."""
        ...

    async def get_item_type_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
    ) -> ApiResponse:
        """Get an index of item types."""
        ...

    def get_item_type(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        item_type_slug: str,
    ) -> ApiResponse:
        """Get an item type by slug."""
        ...

    async def get_item_type_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        item_type_slug: str,
    ) -> ApiResponse:
        """Get an item type by slug."""
        ...

    def get_item(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        item_slug_and_id: int,
    ) -> ApiResponse:
        """Get an item by slug and ID."""
        ...

    async def get_item_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        item_slug_and_id: int,
    ) -> ApiResponse:
        """Get an item by slug and ID."""
        ...

    def get_season_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
    ) -> ApiResponse:
        """Get an index of seasons."""
        ...

    async def get_season_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
    ) -> ApiResponse:
        """Get an index of seasons."""
        ...

    def get_season(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
    ) -> ApiResponse:
        """Get a season by ID."""
        ...

    async def get_season_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
    ) -> ApiResponse:
        """Get a season by ID."""
        ...

    def get_season_leaderboard(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
        leaderboard: str,
    ) -> ApiResponse:
        """Get a season leaderboard."""
        ...

    async def get_season_leaderboard_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
        leaderboard: str,
    ) -> ApiResponse:
        """Get a season leaderboard."""
        ...

    def get_era_index(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
    ) -> ApiResponse:
        """Get an index of eras."""
        ...

    async def get_era_index_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
    ) -> ApiResponse:
        """Get an index of eras."""
        ...

    def get_era(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        era_id: int,
    ) -> ApiResponse:
        """Get an era by ID."""
        ...

    async def get_era_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        era_id: int,
    ) -> ApiResponse:
        """Get an era by ID."""
        ...

    def get_era_leaderboard(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        era_id: int,
        leaderboard: str,
    ) -> ApiResponse:
        """Get an era leaderboard."""
        ...

    async def get_era_leaderboard_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        era_id: int,
        leaderboard: str,
    ) -> ApiResponse:
        """Get an era leaderboard."""
        ...

class D3API:
    """Diablo 3 API facade."""

    game_data: D3GameDataAPI
    community: D3CommunityAPI
