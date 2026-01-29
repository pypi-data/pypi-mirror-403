"""
biomodels_search

Searches for computational biological models in the EBI BioModels database. Use this tool to find...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def biomodels_search(
    action: str,
    query: str,
    limit: Optional[int] = 10,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    """
    Searches for computational biological models in the EBI BioModels database. Use this tool to find...

    Parameters
    ----------
    action : str
        The specific action to perform. Must be set to 'search_models'.
    query : str
        The search term to query the BioModels database. Example queries include path...
    limit : int
        The maximum number of model results to return. The default is 10.
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
            "name": "biomodels_search",
            "arguments": {"action": action, "query": query, "limit": limit},
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["biomodels_search"]
