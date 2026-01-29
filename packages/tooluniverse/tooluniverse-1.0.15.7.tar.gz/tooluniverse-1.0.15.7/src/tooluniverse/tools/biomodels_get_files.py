"""
biomodels_get_files

Retrieves the download link for a specific biological model from the BioModels database using its...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def biomodels_get_files(
    action: str,
    model_id: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    """
    Retrieves the download link for a specific biological model from the BioModels database using its...

    Parameters
    ----------
    action : str
        The specific action to perform. Must be set to 'get_model_files'.
    model_id : str
        The unique Model ID (e.g., 'BIOMD0000000469') for which to retrieve the downl...
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
            "name": "biomodels_get_files",
            "arguments": {"action": action, "model_id": model_id},
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["biomodels_get_files"]
