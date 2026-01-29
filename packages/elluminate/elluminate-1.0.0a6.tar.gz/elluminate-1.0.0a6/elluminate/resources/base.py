from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Type, TypeVar, Union

from pydantic import BaseModel
from tqdm import tqdm

if TYPE_CHECKING:
    from elluminate.async_client import AsyncClient
    from elluminate.client import Client


T = TypeVar("T", bound=BaseModel)


class BaseResource:
    def __init__(self, client: Union[Client, AsyncClient]) -> None:
        self._client = client
        # HTTP methods - bind sync or async depending on client type
        if hasattr(client, "_get"):
            # Sync client
            self._get = client._get
            self._post = client._post
            self._put = client._put
            self._delete = client._delete
            self._patch = client._patch
        if hasattr(client, "_aget"):
            # Async client
            self._aget = client._aget
            self._apost = client._apost
            self._aput = client._aput
            self._adelete = client._adelete
            self._apatch = client._apatch

    def _paginate_sync(
        self,
        path: str,
        model: Type[T],
        params: Dict[str, Any] | None = None,
        resource_name: str = "",
        min_pages_to_show_progress: int = 10,
    ) -> list[T]:
        """Sync helper that handles pagination.

        Args:
            path (str): API endpoint path relative to the project route prefix
            model (Type[T]): Pydantic model to validate the response against
            params (Dict[str, Any] | None): Additional query parameters for the request
            resource_name (str): Name of the resource being fetched (for progress bar)
            min_pages_to_show_progress (int): Minimum number of pages to show progress bar

        Returns:
            list[T]: Combined list of all items across all pages

        """

        def fetch_page(page_number: int) -> Tuple[List[T], int]:
            page_params = {**(params or {}), "page": page_number}
            response = self._get(path, params=page_params)
            data = response.json()
            items = []
            for item in data["items"]:
                obj = model.model_validate(item)
                # Bind _client for rich model methods
                if hasattr(obj, "_client"):
                    obj._client = self._client
                items.append(obj)
            return items, data["count"]

        # Fetch first page
        all_items, total_count = fetch_page(1)

        if len(all_items) == total_count:
            return all_items

        # Calculate pagination details
        items_per_page = len(all_items)
        total_pages = math.ceil(total_count / items_per_page)

        # Configure progress bar
        should_show_progress = total_pages > min_pages_to_show_progress and resource_name
        remaining_pages = range(2, total_pages + 1)
        if should_show_progress:
            remaining_pages = tqdm(remaining_pages, desc=f"Getting {resource_name}")

        # Fetch remaining pages
        for page in remaining_pages:
            page_items, _ = fetch_page(page)
            all_items.extend(page_items)

        return all_items

    async def _paginate(
        self,
        path: str,
        model: Type[T],
        params: Dict[str, Any] | None = None,
        resource_name: str = "",
        min_pages_to_show_progress: int = 10,
    ) -> list[T]:
        """Async helper that handles pagination.

        Args:
            path (str): API endpoint path relative to the project route prefix
            model (Type[T]): Pydantic model to validate the response against
            params (Dict[str, Any] | None): Additional query parameters for the request
            resource_name (str): Name of the resource being fetched (for progress bar)
            min_pages_to_show_progress (int): Minimum number of pages to show progress bar

        Returns:
            list[T]: Combined list of all items across all pages

        """

        async def fetch_page(page_number: int) -> Tuple[List[T], int]:
            page_params = {**(params or {}), "page": page_number}
            response = await self._aget(path, params=page_params)
            data = response.json()
            items = []
            for item in data["items"]:
                obj = model.model_validate(item)
                # Bind _client for rich model methods
                if hasattr(obj, "_client"):
                    obj._client = self._client
                items.append(obj)
            return items, data["count"]

        # Fetch first page
        all_items, total_count = await fetch_page(1)

        if len(all_items) == total_count:
            return all_items

        # Calculate pagination details
        items_per_page = len(all_items)
        total_pages = math.ceil(total_count / items_per_page)

        # Configure progress bar
        should_show_progress = total_pages > min_pages_to_show_progress and resource_name
        remaining_pages = range(2, total_pages + 1)
        if should_show_progress:
            remaining_pages = tqdm(remaining_pages, desc=f"Getting {resource_name}")

        # Fetch remaining pages
        for page in remaining_pages:
            page_items, _ = await fetch_page(page)
            all_items.extend(page_items)

        return all_items
