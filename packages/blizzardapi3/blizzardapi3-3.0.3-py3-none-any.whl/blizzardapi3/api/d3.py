"""Diablo 3 API facade."""

from ..core import BaseClient, EndpointRegistry, MethodFactory, RequestExecutor


class D3GameDataAPI:
    """Diablo 3 Game Data API with dynamically generated methods."""

    def __init__(self, client: BaseClient, executor: RequestExecutor, registry: EndpointRegistry):
        """Initialize Diablo 3 Game Data API.

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
        methods = factory.generate_all_methods("d3", "game_data")

        for method_name, (sync_method, async_method) in methods.items():
            # Bind methods to this instance
            setattr(self, method_name, sync_method.__get__(self, type(self)))
            setattr(self, f"{method_name}_async", async_method.__get__(self, type(self)))


class D3CommunityAPI:
    """Diablo 3 Community API with dynamically generated methods."""

    def __init__(self, client: BaseClient, executor: RequestExecutor, registry: EndpointRegistry):
        """Initialize Diablo 3 Community API.

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
        methods = factory.generate_all_methods("d3", "community")

        for method_name, (sync_method, async_method) in methods.items():
            # Bind methods to this instance
            setattr(self, method_name, sync_method.__get__(self, type(self)))
            setattr(self, f"{method_name}_async", async_method.__get__(self, type(self)))


class D3API:
    """Diablo 3 API facade.

    Provides access to:
    - game_data: Diablo 3 Game Data API (items, item types, recipes, etc.)
    - community: Diablo 3 Community API (profiles, heroes, etc.)
    """

    def __init__(self, client: BaseClient, registry: EndpointRegistry):
        """Initialize Diablo 3 API.

        Args:
            client: Base client for session management
            registry: Endpoint registry
        """
        self.client = client
        executor = RequestExecutor(client.token_manager)

        # Initialize sub-APIs
        self.game_data = D3GameDataAPI(client, executor, registry)
        self.community = D3CommunityAPI(client, executor, registry)
