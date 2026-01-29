"""Type stubs for StarCraft 2 API - auto-generated for IDE autocomplete."""

from ..core.executor import ApiResponse
from ..types import Locale, Region

class SC2GameDataAPI:
    """Auto-generated stub for IDE autocomplete."""

    def get_league_data(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
        queue_id: int,
        team_type: str,
        league_id: int,
    ) -> ApiResponse:
        """Get league data for a specific season, queue, team type, and league."""
        ...

    async def get_league_data_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        season_id: int,
        queue_id: int,
        team_type: str,
        league_id: int,
    ) -> ApiResponse:
        """Get league data for a specific season, queue, team type, and league."""
        ...

class SC2CommunityAPI:
    """Auto-generated stub for IDE autocomplete."""

    def get_static_profile(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
    ) -> ApiResponse:
        """Get static profile data for a StarCraft 2 region."""
        ...

    async def get_static_profile_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
    ) -> ApiResponse:
        """Get static profile data for a StarCraft 2 region."""
        ...

    def get_metadata_profile(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        realm_id: int,
        profile_id: int,
    ) -> ApiResponse:
        """Get metadata for a StarCraft 2 profile."""
        ...

    async def get_metadata_profile_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        realm_id: int,
        profile_id: int,
    ) -> ApiResponse:
        """Get metadata for a StarCraft 2 profile."""
        ...

    def get_profile(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        realm_id: int,
        profile_id: int,
    ) -> ApiResponse:
        """Get a StarCraft 2 profile."""
        ...

    async def get_profile_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        realm_id: int,
        profile_id: int,
    ) -> ApiResponse:
        """Get a StarCraft 2 profile."""
        ...

    def get_profile_ladder_summary(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        realm_id: int,
        profile_id: int,
    ) -> ApiResponse:
        """Get ladder summary for a StarCraft 2 profile."""
        ...

    async def get_profile_ladder_summary_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        realm_id: int,
        profile_id: int,
    ) -> ApiResponse:
        """Get ladder summary for a StarCraft 2 profile."""
        ...

    def get_profile_ladder(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        realm_id: int,
        profile_id: int,
        ladder_id: int,
    ) -> ApiResponse:
        """Get a ladder for a StarCraft 2 profile."""
        ...

    async def get_profile_ladder_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        realm_id: int,
        profile_id: int,
        ladder_id: int,
    ) -> ApiResponse:
        """Get a ladder for a StarCraft 2 profile."""
        ...

    def get_grandmaster_leaderboard(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
    ) -> ApiResponse:
        """Get grandmaster leaderboard for a region."""
        ...

    async def get_grandmaster_leaderboard_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
    ) -> ApiResponse:
        """Get grandmaster leaderboard for a region."""
        ...

    def get_season(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
    ) -> ApiResponse:
        """Get current ladder season data for a region."""
        ...

    async def get_season_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
    ) -> ApiResponse:
        """Get current ladder season data for a region."""
        ...

    def get_player(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        account_id: int,
    ) -> ApiResponse:
        """Get a StarCraft 2 player by account ID."""
        ...

    async def get_player_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        account_id: int,
    ) -> ApiResponse:
        """Get a StarCraft 2 player by account ID."""
        ...

    def get_legacy_profile(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        realm_id: int,
        profile_id: int,
    ) -> ApiResponse:
        """Get legacy profile data."""
        ...

    async def get_legacy_profile_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        realm_id: int,
        profile_id: int,
    ) -> ApiResponse:
        """Get legacy profile data."""
        ...

    def get_legacy_profile_ladders(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        realm_id: int,
        profile_id: int,
    ) -> ApiResponse:
        """Get legacy profile ladder data."""
        ...

    async def get_legacy_profile_ladders_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        realm_id: int,
        profile_id: int,
    ) -> ApiResponse:
        """Get legacy profile ladder data."""
        ...

    def get_legacy_profile_matches(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        realm_id: int,
        profile_id: int,
    ) -> ApiResponse:
        """Get legacy profile match history."""
        ...

    async def get_legacy_profile_matches_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        realm_id: int,
        profile_id: int,
    ) -> ApiResponse:
        """Get legacy profile match history."""
        ...

    def get_legacy_ladder(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        ladder_id: int,
    ) -> ApiResponse:
        """Get legacy ladder data."""
        ...

    async def get_legacy_ladder_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
        ladder_id: int,
    ) -> ApiResponse:
        """Get legacy ladder data."""
        ...

    def get_legacy_achievements(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
    ) -> ApiResponse:
        """Get legacy achievements data."""
        ...

    async def get_legacy_achievements_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
    ) -> ApiResponse:
        """Get legacy achievements data."""
        ...

    def get_legacy_rewards(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
    ) -> ApiResponse:
        """Get legacy rewards data."""
        ...

    async def get_legacy_rewards_async(
        self,
        *,
        region: str | Region,
        locale: str | Locale,
        region_id: int,
    ) -> ApiResponse:
        """Get legacy rewards data."""
        ...

class SC2API:
    """StarCraft 2 API facade."""

    game_data: SC2GameDataAPI
    community: SC2CommunityAPI
