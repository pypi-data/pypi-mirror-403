from __future__ import annotations

from typing import Any, Dict, List

from loguru import logger

from elluminate.resources.base import BaseResource
from elluminate.schemas import (
    CollectionColumn,
    CreateCollectionRequest,
    PromptTemplate,
    TemplateVariablesCollection,
    TemplateVariablesCollectionFilter,
    TemplateVariablesCollectionSort,
    TemplateVariablesCollectionWithEntries,
    UpdateCollectionRequest,
)


class TemplateVariablesCollectionsResource(BaseResource):
    # Sync methods (use httpx.Client directly)

    def get(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
    ) -> TemplateVariablesCollectionWithEntries:
        """Get a collection by name or id.

        Args:
            name (str | None): The name of the collection to get.
            id (int | None): The id of the collection to get.

        Returns:
            TemplateVariablesCollectionWithEntries: The collection object.

        Raises:
            ValueError: If neither or both name and id are provided, or if not found.

        """
        if name is not None and id is not None:
            raise ValueError("Provide either 'name' or 'id', not both")
        if name is None and id is None:
            raise ValueError("Either 'name' or 'id' must be provided")

        if id is not None:
            response = self._get(f"collections/{id}")
            coll = TemplateVariablesCollectionWithEntries.model_validate(response.json())
            coll._client = self._client
            return coll

        # Lookup by name
        response = self._get("collections", params={"name": name})
        collections = []
        for c in response.json()["items"]:
            coll = TemplateVariablesCollection.model_validate(c)
            coll._client = self._client
            collections.append(coll)

        if not collections:
            raise ValueError(f"No collection found with name '{name}'")

        # Since collection name are unique per project, there should be only one
        collection = collections[0]

        # Fetch the `collection` by `id` since this response includes the template variables
        response = self._get(f"collections/{collection.id}")
        coll = TemplateVariablesCollectionWithEntries.model_validate(response.json())
        coll._client = self._client
        return coll

    def list(
        self,
        filters: TemplateVariablesCollectionFilter | None = None,
        compatible_prompt_template: PromptTemplate | None = None,
        sort_options: TemplateVariablesCollectionSort | None = None,
    ) -> list[TemplateVariablesCollection]:
        """Get a list of template variables collections.

        Args:
            filters (TemplateVariablesCollectionFilter | None): Filter for template variables collections.
            compatible_prompt_template (PromptTemplate | None): Filter collections compatible with a specific prompt template.
            sort_options (TemplateVariablesCollectionSort | None): Sort for template variables collections.

        Returns:
            list[TemplateVariablesCollection]: A list of template variables collections.

        """
        params: Dict[str, Any] = {}

        if filters:
            params["filters"] = filters.model_dump()
        if compatible_prompt_template:
            params["compatible_prompt_template_id"] = compatible_prompt_template.id
        if sort_options:
            params["sort_options"] = sort_options.model_dump()

        return self._paginate_sync("collections", model=TemplateVariablesCollection, params=params)

    def create(
        self,
        name: str,
        description: str = "",
        variables: List[Dict[str, Any]] | None = None,
        columns: List[str | CollectionColumn] | None = None,
        read_only: bool = False,
    ) -> TemplateVariablesCollectionWithEntries:
        """Creates a new collection.

        Args:
            name (str): The name for the new collection.
            description (str): Optional description for the collection.
            variables (list[dict[str, Any]]): Optional list of variables to add to the collection.
                Values can be strings for TEXT columns, dicts for CONVERSATION columns, or other types.
            columns (list[str | CollectionColumn]): Optional list of column definitions.
                Can be column names as strings (defaults to TEXT type) or CollectionColumn objects.
            read_only (bool): Whether the collection should be read-only.

        Returns:
            (TemplateVariablesCollection): The newly created collection object.

        Raises:
            httpx.HTTPStatusError: If collection with same name already exists (400 BAD REQUEST)

        """
        # Normalize string columns to CollectionColumn objects
        normalized_columns = None
        if columns:
            normalized_columns = [CollectionColumn(name=c) if isinstance(c, str) else c for c in columns]

        response = self._post(
            "collections",
            json=CreateCollectionRequest(
                name=name,
                description=description,
                variables=variables,
                columns=normalized_columns,
                read_only=read_only,
            ).model_dump(exclude_none=True),
        )
        coll = TemplateVariablesCollectionWithEntries.model_validate(response.json())
        coll._client = self._client
        return coll

    def get_or_create(
        self,
        name: str,
        description: str = "",
        variables: List[Dict[str, Any]] | None = None,
        columns: List[str | CollectionColumn] | None = None,
        read_only: bool = False,
    ) -> tuple[TemplateVariablesCollectionWithEntries, bool]:
        """Gets an existing collection by name or creates a new one if it doesn't exist.

        If a collection with the given name exists:
        - If columns parameter is provided, validates that the existing collection has matching column types
        - Returns the existing collection if compatible, otherwise raises ValueError
        - Other parameters (description, variables, read_only) are ignored with warnings

        Args:
            name: The name of the collection to get or create.
            description: Optional description for the collection if created.
            variables: Optional list of variables to add to the collection if created.
                Values can be strings for TEXT columns, dicts for CONVERSATION columns, or other types.
            columns: Optional list of column definitions for the collection if created.
                Can be column names as strings (defaults to TEXT type) or CollectionColumn objects.
                If provided and collection exists, column types must match existing collection.
            read_only: Whether the collection should be read-only if created.

        Returns:
            tuple[TemplateVariablesCollectionWithEntries, bool]: A tuple containing:
                - Collection: The retrieved or created collection object
                - bool: True if a new collection was created, False if existing was found

        Raises:
            ValueError: If collection exists but has incompatible column types

        """
        from elluminate.exceptions import ConflictError

        try:
            return self.create(
                name=name,
                description=description,
                variables=variables,
                columns=columns,
                read_only=read_only,
            ), True
        except ConflictError:
            # Code 409 means resource already exists, simply get and return it
            collection = self.get(name=name)
            if description != "" and collection.description != description:
                logger.warning(
                    f"Collection with name {name} already exists with a different description "
                    f"(expected: {description}, actual: {collection.description}), returning existing collection."
                )
            if variables:
                logger.warning(
                    f"Collection with name {name} already exists. Given variables are ignored. "
                    "Please use `.template_variables.add_to_collection` to add variables to the collection."
                )
            if columns:
                # Normalize string columns for comparison
                normalized_columns = [CollectionColumn(name=c) if isinstance(c, str) else c for c in columns]
                # Validate that existing collection has compatible columns
                existing_column_types = {col.column_type for col in collection.columns}
                requested_column_types = {col.column_type for col in normalized_columns}

                if requested_column_types != existing_column_types:
                    raise ValueError(
                        f"Collection '{name}' already exists with different column types. "
                        f"Existing: {existing_column_types}, Requested: {requested_column_types}. "
                        f"Use a different collection name or modify the existing collection."
                    )

                logger.warning(
                    f"Collection with name {name} already exists. Given columns are ignored. "
                    "Please use `.update` to modify the collection structure."
                )
            return collection, False

    def delete(self, template_variables_collection: TemplateVariablesCollection) -> None:
        """Delete a collection."""
        self._delete(f"collections/{template_variables_collection.id}")

    def update(
        self,
        collection_id: int,
        name: str,
        description: str | None = None,
        read_only: bool | None = None,
        columns: List[str | CollectionColumn] | None = None,
    ) -> TemplateVariablesCollection:
        """Update an existing collection.

        Args:
            collection_id: The ID of the collection to update.
            name: The new name for the collection.
            description: Optional new description for the collection.
            read_only: Optional new read-only status for the collection.
            columns: Optional list of columns in the desired order.
                    Can be column names as strings (defaults to TEXT type) or CollectionColumn objects.
                    Missing columns are deleted, new columns are created, existing columns are reordered.

        Returns:
            TemplateVariablesCollection: The updated collection object.

        Raises:
            httpx.HTTPStatusError: If collection doesn't exist or validation fails.

        """
        # Normalize string columns to CollectionColumn objects
        normalized_columns = None
        if columns:
            normalized_columns = [CollectionColumn(name=c) if isinstance(c, str) else c for c in columns]

        response = self._put(
            f"collections/{collection_id}",
            json=UpdateCollectionRequest(
                name=name,
                description=description,
                read_only=read_only,
                columns=normalized_columns,
            ).model_dump(exclude_none=True),
        )
        coll = TemplateVariablesCollection.model_validate(response.json())
        coll._client = self._client
        return coll

    # ===== Async Methods =====

    async def aget(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
    ) -> TemplateVariablesCollectionWithEntries:
        """Get a collection by name or id (async).

        Args:
            name: The name of the collection to get.
            id: The id of the collection to get.

        Returns:
            TemplateVariablesCollectionWithEntries: The collection object.

        Raises:
            ValueError: If neither or both name and id are provided, or if not found.

        """
        if name is not None and id is not None:
            raise ValueError("Provide either 'name' or 'id', not both")
        if name is None and id is None:
            raise ValueError("Either 'name' or 'id' must be provided")

        if id is not None:
            response = await self._aget(f"collections/{id}")
            coll = TemplateVariablesCollectionWithEntries.model_validate(response.json())
            coll._client = self._client
            return coll

        # Get by name
        response = await self._aget("collections", params={"name": name})
        collections = []
        for c in response.json()["items"]:
            coll = TemplateVariablesCollection.model_validate(c)
            coll._client = self._client
            collections.append(coll)

        if not collections:
            raise ValueError(f"No collection found with name '{name}'")

        collection = collections[0]
        response = await self._aget(f"collections/{collection.id}")
        coll = TemplateVariablesCollectionWithEntries.model_validate(response.json())
        coll._client = self._client
        return coll

    async def alist(
        self,
        filters: TemplateVariablesCollectionFilter | None = None,
        compatible_prompt_template: PromptTemplate | None = None,
        sort_options: TemplateVariablesCollectionSort | None = None,
    ) -> list[TemplateVariablesCollection]:
        """Get a list of template variables collections (async)."""
        params: Dict[str, Any] = {}

        if filters:
            params["filters"] = filters.model_dump()
        if compatible_prompt_template:
            params["compatible_prompt_template_id"] = compatible_prompt_template.id
        if sort_options:
            params["sort_options"] = sort_options.model_dump()

        return await self._paginate("collections", model=TemplateVariablesCollection, params=params)

    async def acreate(
        self,
        name: str,
        description: str = "",
        variables: List[Dict[str, Any]] | None = None,
        columns: List[str | CollectionColumn] | None = None,
        read_only: bool = False,
    ) -> TemplateVariablesCollectionWithEntries:
        """Creates a new collection (async)."""
        normalized_columns = None
        if columns:
            normalized_columns = [CollectionColumn(name=c) if isinstance(c, str) else c for c in columns]

        response = await self._apost(
            "collections",
            json=CreateCollectionRequest(
                name=name,
                description=description,
                variables=variables,
                columns=normalized_columns,
                read_only=read_only,
            ).model_dump(exclude_none=True),
        )
        coll = TemplateVariablesCollectionWithEntries.model_validate(response.json())
        coll._client = self._client
        return coll

    async def aget_or_create(
        self,
        name: str,
        description: str = "",
        variables: List[Dict[str, Any]] | None = None,
        columns: List[str | CollectionColumn] | None = None,
        read_only: bool = False,
    ) -> tuple[TemplateVariablesCollectionWithEntries, bool]:
        """Gets an existing collection by name or creates a new one if it doesn't exist (async)."""
        from elluminate.exceptions import ConflictError

        try:
            return await self.acreate(
                name=name,
                description=description,
                variables=variables,
                columns=columns,
                read_only=read_only,
            ), True
        except ConflictError:
            collection = await self.aget(name=name)
            if description != "" and collection.description != description:
                logger.warning(
                    f"Collection with name {name} already exists with a different description "
                    f"(expected: {description}, actual: {collection.description}), returning existing collection."
                )
            if variables:
                logger.warning(
                    f"Collection with name {name} already exists. Given variables are ignored. "
                    "Please use `.template_variables.add_to_collection` to add variables to the collection."
                )
            if columns:
                normalized_columns = [CollectionColumn(name=c) if isinstance(c, str) else c for c in columns]
                existing_column_types = {col.column_type for col in collection.columns}
                requested_column_types = {col.column_type for col in normalized_columns}

                if requested_column_types != existing_column_types:
                    raise ValueError(
                        f"Collection '{name}' already exists with different column types. "
                        f"Existing: {existing_column_types}, Requested: {requested_column_types}. "
                        f"Use a different collection name or modify the existing collection."
                    )

                logger.warning(
                    f"Collection with name {name} already exists. Given columns are ignored. "
                    "Please use `.update` to modify the collection structure."
                )
            return collection, False

    async def adelete(self, template_variables_collection: TemplateVariablesCollection) -> None:
        """Delete a collection (async)."""
        await self._adelete(f"collections/{template_variables_collection.id}")

    async def aupdate(
        self,
        collection_id: int,
        name: str,
        description: str | None = None,
        read_only: bool | None = None,
        columns: List[str | CollectionColumn] | None = None,
    ) -> TemplateVariablesCollection:
        """Update an existing collection (async)."""
        normalized_columns = None
        if columns:
            normalized_columns = [CollectionColumn(name=c) if isinstance(c, str) else c for c in columns]

        response = await self._aput(
            f"collections/{collection_id}",
            json=UpdateCollectionRequest(
                name=name,
                description=description,
                read_only=read_only,
                columns=normalized_columns,
            ).model_dump(exclude_none=True),
        )
        coll = TemplateVariablesCollection.model_validate(response.json())
        coll._client = self._client
        return coll
