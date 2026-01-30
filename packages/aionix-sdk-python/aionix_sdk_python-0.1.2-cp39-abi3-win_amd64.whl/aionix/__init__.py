"""
AionixOne Python SDK

High-performance Python bindings for the AionixOne platform.
All APIs return standard Python dict/list, compatible with JSON output.

Example:
    >>> import aionix
    >>> import asyncio
    >>>
    >>> async def main():
    ...     client = aionix.connect()
    ...     functions = await client.aionixfn.list_functions()
    ...     for fn in functions:
    ...         print(fn["name"])
    ...
    >>> asyncio.run(main())
"""

from aionix._aionix import (
    # Main entry points
    connect,
    connect_sync,
    Client,
    Action,
    # Exceptions
    AionixError,
    NotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    RateLimitError,
    TimeoutError,
    UnavailableError,
    TransientError,
    ExecutionFailedError,
    PaymentRequiredError,
    ConfigurationError,
    InternalError,
    CancelledError,
    # Version
    __version__,
)

__all__ = [
    # Entry points
    "connect",
    "connect_sync",
    "Client",
    "Action",
    # Exceptions
    "AionixError",
    "NotFoundError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "RateLimitError",
    "TimeoutError",
    "UnavailableError",
    "TransientError",
    "ExecutionFailedError",
    "PaymentRequiredError",
    "ConfigurationError",
    "InternalError",
    "CancelledError",
    # Version
    "__version__",
]
