"""Response models for CLI output formatting."""

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from dxs import __version__

T = TypeVar("T")


class ResponseMetadata(BaseModel):
    """Universal metadata for CLI responses."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cli_version: str = Field(default=__version__)

    # Universal fields
    success: bool = True

    # List/collection metadata
    count: int | None = None
    total_count: int | None = None

    # Search metadata
    query: str | None = None

    # Filter context (organization_id, repository_id, branch_id, etc.)
    # Allowing extra fields for command-specific metadata
    class Config:
        """Pydantic config."""

        extra = "allow"


class Response(BaseModel, Generic[T]):
    """Base response wrapper."""

    metadata: ResponseMetadata

    def to_output_dict(self) -> dict:
        """Convert to output format (flattened).

        Returns:
            Dictionary suitable for serialization.
        """
        raise NotImplementedError


class SingleResponse(Response[T]):
    """Response for single item with semantic key."""

    item: T
    semantic_key: str

    def to_output_dict(self) -> dict:
        """Convert to output format.

        Returns:
            Dictionary with structure: {semantic_key: item, metadata: {...}}
        """
        # Convert item to dict if it's a Pydantic model
        if hasattr(self.item, "model_dump"):
            item_dict = self.item.model_dump()
        else:
            item_dict = self.item

        return {
            self.semantic_key: item_dict,
            "metadata": self.metadata.model_dump(exclude_none=True, mode="json"),
        }


class ListResponse(Response[list[T]]):
    """Response for list of items."""

    items: list[T]
    semantic_key: str  # Plural form (e.g., "organizations", "repositories")

    def __init__(self, **data: Any):
        """Initialize and auto-set count in metadata."""
        super().__init__(**data)
        # Auto-set count in metadata
        self.metadata.count = len(self.items)

    def to_output_dict(self) -> dict:
        """Convert to output format.

        Returns:
            Dictionary with structure: {semantic_key: [...], metadata: {...}}
        """
        items_list = [
            item.model_dump() if hasattr(item, "model_dump") else item for item in self.items
        ]

        return {
            self.semantic_key: items_list,
            "metadata": self.metadata.model_dump(exclude_none=True, mode="json"),
        }


class SearchResponse(Response[list[T]]):
    """Response for search results."""

    items: list[T]
    semantic_key: str
    query: str
    total_count: int  # Total items before search filter

    def __init__(self, **data: Any):
        """Initialize and set search metadata."""
        super().__init__(**data)
        # Set search metadata
        self.metadata.query = self.query
        self.metadata.total_count = self.total_count
        self.metadata.count = len(self.items)

    def to_output_dict(self) -> dict:
        """Convert to output format.

        Returns:
            Dictionary with structure: {semantic_key: [...], metadata: {query, count, total_count, ...}}
        """
        items_list = [
            item.model_dump() if hasattr(item, "model_dump") else item for item in self.items
        ]

        return {
            self.semantic_key: items_list,
            "metadata": self.metadata.model_dump(exclude_none=True, mode="json"),
        }


class CountResponse(Response[int]):
    """Response for count-only queries."""

    total_count: int
    semantic_key: str  # What we're counting (e.g., "cases", "accounts")

    def __init__(self, **data: Any):
        """Initialize and set count metadata."""
        super().__init__(**data)
        self.metadata.total_count = self.total_count

    def to_output_dict(self) -> dict:
        """Convert to output format.

        Returns:
            Dictionary with structure: {semantic_key: total_count, metadata: {...}}
        """
        return {
            self.semantic_key: self.total_count,
            "metadata": self.metadata.model_dump(exclude_none=True, mode="json"),
        }
