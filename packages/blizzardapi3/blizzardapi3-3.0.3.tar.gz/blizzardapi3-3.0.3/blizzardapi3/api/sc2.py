"""StarCraft 2 API facade."""

from ..core import BaseClient, EndpointRegistry, MethodFactory, RequestExecutor


class SC2GameDataAPI:
    """StarCraft 2 Game Data API with dynamically generated methods."""

    def __init__(self, client: BaseClient, executor: RequestExecutor, registry: EndpointRegistry):
        """Initialize StarCraft 2 Game Data API.

        Args:
            client: Base client for session management
            executor: Request executor
            registry: Endpoint registry
        """
        self.client = client
        self.executor = executor
        self.registry = registry

        # Generate and attach all methods
        factory = MethodFactory(executor, registry)
        methods = factory.generate_all_methods("sc2", "game_data")

        for method_name, (sync_method, async_method) in methods.items():
            # Bind methods to this instance
            setattr(self, method_name, sync_method.__get__(self, type(self)))
            setattr(self, f"{method_name}_async", async_method.__get__(self, type(self)))


class SC2CommunityAPI:
    """StarCraft 2 Community API with dynamically generated methods."""

    def __init__(self, client: BaseClient, executor: RequestExecutor, registry: EndpointRegistry):
        """Initialize StarCraft 2 Community API.

        Args:
            client: Base client for session management
            executor: Request executor
            registry: Endpoint registry
        """
        self.client = client
        self.executor = executor
        self.registry = registry

        # Generate and attach all methods
        factory = MethodFactory(executor, registry)
        methods = factory.generate_all_methods("sc2", "community")

        for method_name, (sync_method, async_method) in methods.items():
            # Bind methods to this instance
            setattr(self, method_name, sync_method.__get__(self, type(self)))
            setattr(self, f"{method_name}_async", async_method.__get__(self, type(self)))


class SC2API:
    """StarCraft 2 API facade.

    Provides access to:
    - game_data: StarCraft 2 Game Data API (league data)
    - community: StarCraft 2 Community API (profiles, ladders)
    """

    def __init__(self, client: BaseClient, registry: EndpointRegistry):
        """Initialize StarCraft 2 API.

        Args:
            client: Base client for session management
            registry: Endpoint registry
        """
        self.client = client
        executor = RequestExecutor(client.token_manager)

        # Initialize sub-APIs
        self.game_data = SC2GameDataAPI(client, executor, registry)
        self.community = SC2CommunityAPI(client, executor, registry)
