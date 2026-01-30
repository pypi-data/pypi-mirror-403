from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from elluminate.resources.base import BaseResource
from elluminate.schemas import (
    CreateTemplateVariablesRequest,
    TemplateVariables,
    TemplateVariablesCollection,
)
from elluminate.schemas.prompt_template import PromptTemplate


def _serialize_value(value: Any) -> Any:
    """Recursively serialize Pydantic models and other complex types to JSON-compatible values."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


class TemplateVariablesResource(BaseResource):
    # Sync methods (use httpx.Client directly)

    def list(self, collection: TemplateVariablesCollection) -> list[TemplateVariables]:
        """Returns all template variables for a collection.

        Args:
            collection (TemplateVariablesCollection): The collection to get entries for.

        Returns:
            list[TemplateVariables]: List of template variables.

        Raises:
            httpx.HTTPStatusError: If the collection is not found

        """
        return self._paginate_sync(
            path=f"collections/{collection.id}/entries",
            model=TemplateVariables,
            resource_name="Template Variables",
        )

    def get(self, *, collection_id: int, id: int) -> TemplateVariables:
        """Get a template variable by id.

        Args:
            collection_id: The id of the collection containing the template variable.
            id: The id of the template variable.

        Returns:
            (TemplateVariables): The requested template variable.

        """
        response = self._get(f"collections/{collection_id}/entries/{id}")
        return TemplateVariables.model_validate(response.json())

    def add_to_collection(
        self,
        template_variables: dict[str, Any],
        collection: TemplateVariablesCollection,
    ) -> TemplateVariables:
        """Adds a new entry to a collection. If the entry already exists, it will be returned.

        Args:
            template_variables (dict[str, Any]): The template variables to add.
            collection (TemplateVariablesCollection): The collection to add the entry to.

        Returns:
            TemplateVariables: The retrieved or created template variables object

        """
        response = self._post(
            f"collections/{collection.id}/entries",
            json=CreateTemplateVariablesRequest(input_values=template_variables).model_dump(),
        )
        return TemplateVariables.model_validate(response.json())

    def generate(
        self, collection: TemplateVariablesCollection, prompt_template: PromptTemplate
    ) -> TemplateVariables:
        """Generates a new template variable in a collection using a prompt template.

        Args:
            collection (TemplateVariablesCollection): The collection to add the generated template variable to.
            prompt_template (PromptTemplate): The prompt template to use for generation.

        Returns:
            TemplateVariables: The newly generated template variables object.

        """
        response = self._post(
            f"collections/{collection.id}/entries",
            json=CreateTemplateVariablesRequest(
                input_values=None, prompt_template_id=prompt_template.id
            ).model_dump(),
        )
        return TemplateVariables.model_validate(response.json())

    def delete(
        self,
        template_variables: TemplateVariables,
        collection: TemplateVariablesCollection,
    ) -> None:
        """Deletes a template variables.

        Args:
            template_variables (TemplateVariables): The template variables to delete.
            collection (TemplateVariablesCollection): The collection containing the template variables.

        Raises:
            httpx.HTTPStatusError: If the template variables doesn't exist, belongs to a different collection,
                or belongs to a different project.

        """
        self._delete(f"collections/{collection.id}/entries/{template_variables.id}")

    def delete_all(self, collection: TemplateVariablesCollection) -> None:
        """Deletes all template variables for a collection.

        Args:
            collection (TemplateVariablesCollection): The collection to delete all template variables for.

        Raises:
            httpx.HTTPStatusError: If the collection doesn't exist or belongs to a different project.

        """
        self._delete(f"collections/{collection.id}/entries")

    def add_many_to_collection(
        self, variables: list[dict[str, str]], collection: TemplateVariablesCollection
    ) -> list[TemplateVariables]:
        """Add multiple template variable entries to a collection in one request.

        Uses the backend's batch upload endpoint by generating a JSONL payload in memory.

        Args:
            variables: List of input_values dicts to add.
            collection: Target collection.

        Returns:
            List[TemplateVariables]: The created template variables.

        """
        if not variables:
            return []

        # Serialize any Pydantic models in the variables
        serialized = [_serialize_value(v) for v in variables]

        # Build JSONL content expected by the backend batch endpoint
        jsonl = "\n".join(json.dumps(v, ensure_ascii=False) for v in serialized)
        files = {
            "file": ("variables.jsonl", jsonl.encode("utf-8"), "application/jsonl"),
        }

        response = self._post(f"collections/{collection.id}/entries/batches", files=files)
        data = response.json()
        return [TemplateVariables.model_validate(item) for item in data]

    # ===== Async Methods =====

    async def alist(self, collection: TemplateVariablesCollection) -> list[TemplateVariables]:
        """Returns all template variables for a collection (async)."""
        return await self._paginate(
            path=f"collections/{collection.id}/entries",
            model=TemplateVariables,
            resource_name="Template Variables",
        )

    async def aget(self, *, collection_id: int, id: int) -> TemplateVariables:
        """Get a template variable by id (async).

        Args:
            collection_id: The id of the collection containing the template variable.
            id: The id of the template variable.

        Returns:
            (TemplateVariables): The requested template variable.

        """
        response = await self._aget(f"collections/{collection_id}/entries/{id}")
        return TemplateVariables.model_validate(response.json())

    async def aadd_to_collection(
        self,
        template_variables: dict[str, Any],
        collection: TemplateVariablesCollection,
    ) -> TemplateVariables:
        """Adds a new entry to a collection (async)."""
        response = await self._apost(
            f"collections/{collection.id}/entries",
            json=CreateTemplateVariablesRequest(input_values=template_variables).model_dump(),
        )
        return TemplateVariables.model_validate(response.json())

    async def agenerate(
        self, collection: TemplateVariablesCollection, prompt_template: PromptTemplate
    ) -> TemplateVariables:
        """Generates a new template variable in a collection using a prompt template (async)."""
        response = await self._apost(
            f"collections/{collection.id}/entries",
            json=CreateTemplateVariablesRequest(
                input_values=None, prompt_template_id=prompt_template.id
            ).model_dump(),
        )
        return TemplateVariables.model_validate(response.json())

    async def adelete(
        self,
        template_variables: TemplateVariables,
        collection: TemplateVariablesCollection,
    ) -> None:
        """Deletes a template variables (async)."""
        await self._adelete(f"collections/{collection.id}/entries/{template_variables.id}")

    async def adelete_all(self, collection: TemplateVariablesCollection) -> None:
        """Deletes all template variables for a collection (async)."""
        await self._adelete(f"collections/{collection.id}/entries")

    async def aadd_many_to_collection(
        self, variables: list[dict[str, str]], collection: TemplateVariablesCollection
    ) -> list[TemplateVariables]:
        """Add multiple template variable entries to a collection in one request (async)."""
        if not variables:
            return []

        serialized = [_serialize_value(v) for v in variables]
        jsonl = "\n".join(json.dumps(v, ensure_ascii=False) for v in serialized)
        files = {
            "file": ("variables.jsonl", jsonl.encode("utf-8"), "application/jsonl"),
        }

        response = await self._apost(f"collections/{collection.id}/entries/batches", files=files)
        data = response.json()
        return [TemplateVariables.model_validate(item) for item in data]
