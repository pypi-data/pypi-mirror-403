"""
Cubit Python SDK

A Python client for the Cubit AI Job Vulnerability API.

Example:
    >>> from cubit import CubitClient
    >>> client = CubitClient("cubit_xxxxxxxxxxxx")
    >>> 
    >>> # Search for jobs
    >>> results = client.search_jobs("software developer")
    >>> for job in results["jobs"]:
    ...     print(f"{job['title']}: {job['balanced_impact_score']}")
    >>> 
    >>> # Get a specific job profile
    >>> job = client.get_job("15-1252.00")
    >>> print(job["scores"]["automation_susceptibility_score"])

Async Example:
    >>> from cubit import CubitAsyncClient
    >>> async with CubitAsyncClient("cubit_xxxxxxxxxxxx") as client:
    ...     job = await client.get_job("15-1252.00")
"""

from .client import CubitClient
from .async_client import CubitAsyncClient
from .exceptions import (
    CubitError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    ServerError,
)

__version__ = "0.2.0"
__all__ = [
    # Clients
    "CubitClient",
    "CubitAsyncClient",
    # Exceptions
    "CubitError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    "ServerError",
]

