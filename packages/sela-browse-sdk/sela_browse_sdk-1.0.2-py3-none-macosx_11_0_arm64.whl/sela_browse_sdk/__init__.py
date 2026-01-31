"""
Sela Network Python SDK

High-level client for interacting with the Sela Network P2P agent system.

Example:
    >>> import asyncio
    >>> from sela_browse_sdk import SelaClient, SelaClientConfig, BootstrapNode
    >>>
    >>> async def main():
    ...     config = SelaClientConfig(
    ...         bootstrap_nodes=[
    ...             BootstrapNode(peer_id="12D3KooW...", multiaddr="/ip4/.../tcp/9000")
    ...         ],
    ...         api_key="sk_live_xxx"
    ...     )
    ...     client = await SelaClient(config)
    ...     await client.start()
    ...     agents = await client.discover_agents("web")
    ...     await client.shutdown()
    >>>
    >>> asyncio.run(main())
"""

from .sela import (
    # Top-level functions
    version,
    valid_event_types,

    # Main client
    SelaClient,

    # Configuration types
    BootstrapNode,
    RelayNode,
    SelaClientConfig,
    DiscoveryOptions,
    ConnectionOptions,
    BrowseOptions,

    # Discovery types
    DiscoveredAgent,

    # Response types
    PageMetadata,
    AvailableAction,
    SemanticContent,
    SemanticPage,
    ActionResult,
    SemanticResponse,
    SessionInfo,
    BrowserResponse,

    # Reputation types
    ReputationRecord,
    TaskOutcome,

    # Event types
    ClientEvent,

    # Error types
    SelaError,
)

__version__ = version()
__all__ = [
    # Functions
    "version",
    "valid_event_types",

    # Client
    "SelaClient",

    # Config
    "BootstrapNode",
    "RelayNode",
    "SelaClientConfig",
    "DiscoveryOptions",
    "ConnectionOptions",
    "BrowseOptions",

    # Discovery
    "DiscoveredAgent",

    # Response
    "PageMetadata",
    "AvailableAction",
    "SemanticContent",
    "SemanticPage",
    "ActionResult",
    "SemanticResponse",
    "SessionInfo",
    "BrowserResponse",

    # Reputation
    "ReputationRecord",
    "TaskOutcome",

    # Events
    "ClientEvent",

    # Errors
    "SelaError",
]
