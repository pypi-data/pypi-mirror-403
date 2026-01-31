"""Utilities for Cloro integration."""

import os
from typing import Any

import httpx
from langchain_core.utils import convert_to_secret_str


def initialize_client(values: dict, *, timeout: float = 10.0) -> dict:
    """Initialize the Cloro HTTP client.

    Args:
        values: The values dictionary containing configuration.
        timeout: Request timeout in seconds. Default: 10.0

    Returns:
        The updated values dictionary with initialized client.
    """
    cloro_api_key = values.get("cloro_api_key") or os.environ.get("CLORO_API_KEY") or ""
    values["cloro_api_key"] = convert_to_secret_str(cloro_api_key)

    # Initialize httpx client with appropriate settings
    values["client"] = httpx.Client(
        base_url="https://api.cloro.dev",
        headers={
            "Authorization": f"Bearer {values['cloro_api_key'].get_secret_value()}",
            "Content-Type": "application/json",
        },
        timeout=timeout,
    )
    return values


def build_search_params(
    query: str,
    num_results: int = 10,
    **kwargs: dict,
) -> dict[str, Any]:
    """Build search parameters for the Cloro API.

    Args:
        query: The search query string.
        num_results: Number of results to return. Default: 10
        **kwargs: Additional search parameters.

    Returns:
        Dictionary of search parameters.
    """
    params = {
        "query": query,
        "num_results": num_results,
    }
    params.update(kwargs)
    return params
