"""
iedb_search_epitopes

Searches for immune epitopes in the Immune Epitope Database (IEDB). Use this tool to find specifi...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def iedb_search_epitopes(
    action: str,
    query: Optional[str] = None,
    structure_type: Optional[str] = None,
    limit: Optional[int] = 10,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    """
    Searches for immune epitopes in the Immune Epitope Database (IEDB). Use this tool to find specifi...

    Parameters
    ----------
    action : str
        The specific action to perform. Must be set to 'search_epitopes'.
    query : str
        Sequence fragment or pattern to search for within the epitope's linear sequen...
    structure_type : str
        The chemical type of the epitope structure. Common values include 'Linear pep...
    limit : int
        The maximum number of epitope results to return. The default is 10.
    stream_callback : Callable, optional
        Callback for streaming output
    use_cache : bool, default False
        Enable caching
    validate : bool, default True
        Validate parameters

    Returns
    -------
    dict[str, Any]
    """
    # Handle mutable defaults to avoid B006 linting error

    return get_shared_client().run_one_function(
        {
            "name": "iedb_search_epitopes",
            "arguments": {
                "action": action,
                "query": query,
                "structure_type": structure_type,
                "limit": limit,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["iedb_search_epitopes"]
