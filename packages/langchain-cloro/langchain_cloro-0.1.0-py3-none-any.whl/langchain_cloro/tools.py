"""Tool for the Cloro.dev Search API."""

from __future__ import annotations

from typing import Any

import httpx
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import Field, SecretStr, model_validator

from langchain_cloro._utilities import build_search_params, initialize_client


class CloroSearchRun(BaseTool):
    r"""Cloro.dev Search tool.

    Setup:
        Install ``langchain-cloro`` and set environment variable ``CLORO_API_KEY``.

        .. code-block:: bash

            pip install -U langchain-cloro
            export CLORO_API_KEY="your-api-key"

    Instantiation:
        .. code-block:: python

            from langchain_cloro import CloroSearchRun

            tool = CloroSearchRun()

    Invocation with args:
        .. code-block:: python

            tool.invoke({"query": "latest AI news", "num_results": 5})

    Invocation with ToolCall:
        .. code-block:: python

            tool.invoke(
                {
                    "args": {"query": "python programming", "num_results": 3},
                    "id": "1",
                    "name": tool.name,
                    "type": "tool_call",
                }
            )
    """

    name: str = "cloro_search"
    description: str = (
        "A wrapper around Cloro.dev Search API. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query. "
        "Output is a JSON array of search results."
    )
    client: httpx.Client = Field(default=None)  # type: ignore[assignment]
    cloro_api_key: SecretStr = Field(default=SecretStr(""))
    timeout: float = Field(default=10.0, description="Request timeout in seconds")

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: dict) -> Any:
        """Validate the environment and initialize the client.

        Args:
            values: The values dictionary containing configuration.

        Returns:
            The validated and updated values dictionary.
        """
        return initialize_client(values, timeout=values.get("timeout", 10.0))

    def _run(
        self,
        query: str,
        num_results: int = 10,
        run_manager: CallbackManagerForToolRun | None = None,
        **kwargs: dict,
    ) -> str:
        """Use the Cloro tool to search.

        Args:
            query: The search query string.
            num_results: Number of search results to return (default: 10).
            run_manager: The run manager for callbacks.
            **kwargs: Additional search parameters to pass to the API.

        Returns:
            JSON string of search results or error message.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        try:
            params = build_search_params(
                query=query,
                num_results=num_results,
                **kwargs,
            )

            response = self.client.get(
                "/search",
                params=params,
            )
            response.raise_for_status()

            results = response.json()
            return str(results)

        except httpx.HTTPError as e:
            return f"Error searching with Cloro: {e!s}"
        except Exception as e:
            return f"Unexpected error: {e!s}"


# Alias for backwards compatibility
CloroSearchResults = CloroSearchRun
