"""
Pagination models for the DGMax client.

This module provides pagination-related models matching the backend API.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import Field, PrivateAttr

from dgmaxclient.models.base import DGMaxBaseModel

T = TypeVar("T")


class PaginationParams(DGMaxBaseModel):
    """Pagination parameters for list requests.

    Attributes:
        limit: Maximum number of items to return (1-1000)
        offset: Number of items to skip for pagination
    """

    limit: int = Field(default=100, ge=1, le=1000, description="Items per page")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")

    def to_query_params(self) -> dict[str, int]:
        """Convert to query parameters dict.

        Returns:
            Dictionary with limit and offset parameters
        """
        return {"limit": self.limit, "offset": self.offset}


class PaginatedResponse(DGMaxBaseModel, Generic[T]):
    """Generic paginated response wrapper.

    This generic class provides consistent pagination responses
    across all API endpoints.

    Attributes:
        count: Total number of items matching the query filters
        results: List of items for the current page
        _offset: Current offset (set internally for has_more calculation)
        _limit: Current limit (set internally for has_more calculation)

    Examples:
        >>> response: PaginatedResponse[DocumentPublic] = client.invoices.list()
        >>> print(f"Total: {response.count}")
        >>> for doc in response.results:
        ...     print(doc.encf)
    """

    count: int = Field(..., description="Total number of items matching filters")
    results: list[T] = Field(default_factory=list, description="Items for current page")
    # Internal pagination tracking (not from API response, set by SDK)
    _offset: int = PrivateAttr(default=0)
    _limit: int = PrivateAttr(default=100)

    def __iter__(self):
        """Allow iteration over results."""
        return iter(self.results)

    def __len__(self) -> int:
        """Return the number of results in the current page."""
        return len(self.results)

    def __getitem__(self, index: int) -> T:
        """Get a result by index."""
        return self.results[index]

    @property
    def has_more(self) -> bool:
        """Check if there are more results beyond this page.

        Returns:
            True if there are more items to fetch
        """
        # Calculate items fetched so far (including this page)
        items_fetched = self._offset + len(self.results)
        return items_fetched < self.count

    @property
    def is_empty(self) -> bool:
        """Check if the response contains no results."""
        return len(self.results) == 0

    @property
    def next_offset(self) -> int | None:
        """Get the offset for the next page, or None if no more pages.

        Returns:
            Next offset value, or None if this is the last page
        """
        if self.has_more:
            return self._offset + len(self.results)
        return None
