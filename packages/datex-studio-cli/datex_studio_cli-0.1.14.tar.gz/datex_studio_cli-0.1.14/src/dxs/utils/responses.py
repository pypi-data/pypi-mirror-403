"""Helper functions for building CLI responses."""

from typing import Any

from dxs.core.responses import (
    CountResponse,
    ListResponse,
    ResponseMetadata,
    SearchResponse,
    SingleResponse,
)


def single(
    item: dict | Any,
    semantic_key: str,
    **metadata_kwargs: Any,
) -> SingleResponse:
    """Build a single-item response.

    Args:
        item: The item to return
        semantic_key: Semantic key (e.g., "organization", "repository")
        **metadata_kwargs: Additional metadata fields (organization_id, etc.)

    Returns:
        SingleResponse ready for output

    Examples:
        >>> single(org_data, "organization")
        >>> single(repo_data, "repository", organization_id=1)
    """
    metadata = ResponseMetadata(**metadata_kwargs)
    return SingleResponse(item=item, semantic_key=semantic_key, metadata=metadata)


def list_response(
    items: list[dict | Any],
    semantic_key: str,
    **metadata_kwargs: Any,
) -> ListResponse:
    """Build a list response.

    Args:
        items: List of items
        semantic_key: Plural semantic key (e.g., "organizations", "repositories")
        **metadata_kwargs: Additional metadata fields

    Returns:
        ListResponse ready for output

    Examples:
        >>> list_response(orgs, "organizations")
        >>> list_response(repos, "repositories", organization_id=1)
    """
    metadata = ResponseMetadata(**metadata_kwargs)
    return ListResponse(items=items, semantic_key=semantic_key, metadata=metadata)


def search_response(
    items: list[dict | Any],
    query: str,
    total_count: int,
    semantic_key: str,
    **metadata_kwargs: Any,
) -> SearchResponse:
    """Build a search response.

    Args:
        items: List of matching items
        query: Search query string
        total_count: Total items before search filter
        semantic_key: Plural semantic key
        **metadata_kwargs: Additional metadata fields

    Returns:
        SearchResponse ready for output

    Examples:
        >>> search_response(matches, query="Datex", total_count=64, semantic_key="organizations")
        >>> search_response(repos, query="Foot", total_count=120, semantic_key="repositories", organization_id=1)
    """
    metadata = ResponseMetadata(**metadata_kwargs)
    return SearchResponse(
        items=items,
        query=query,
        total_count=total_count,
        semantic_key=semantic_key,
        metadata=metadata,
    )


def count_response(
    total_count: int,
    semantic_key: str,
    **metadata_kwargs: Any,
) -> CountResponse:
    """Build a count-only response.

    Args:
        total_count: Total count of matching items
        semantic_key: What we're counting (e.g., "cases", "accounts")
        **metadata_kwargs: Additional metadata fields

    Returns:
        CountResponse ready for output

    Examples:
        >>> count_response(247, "cases")
        >>> count_response(1024, "accounts", status_filter="active")
    """
    metadata = ResponseMetadata(**metadata_kwargs)
    return CountResponse(
        total_count=total_count,
        semantic_key=semantic_key,
        metadata=metadata,
    )
