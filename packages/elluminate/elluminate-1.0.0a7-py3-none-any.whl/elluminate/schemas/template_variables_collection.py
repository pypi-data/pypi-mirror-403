from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Iterator, Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from elluminate.exceptions import ModelNotBoundError

if TYPE_CHECKING:
    from elluminate.async_client import AsyncClient
    from elluminate.client import Client
    from elluminate.schemas.prompt_template import PromptTemplate
    from elluminate.schemas.template_variables import TemplateVariables

_COLLECTION_HINT = (
    "This collection is not connected to a client. "
    "To use model methods, obtain collections through: "
    "client.get_collection(), client.create_collection(), "
    "or client.get_or_create_collection()."
)


class ColumnTypeEnum(str, Enum):
    # these mirror the supported backend types, not actively used yet
    TEXT = "text"
    JSON = "json"
    CONVERSATION = "conversation"
    RAW_INPUT = "raw_input"
    CATEGORY = "category"


class CollectionColumn(BaseModel):
    """Column definition for a template variables collection."""

    id: int | None = None
    name: str | None = None
    column_type: ColumnTypeEnum = Field(default=ColumnTypeEnum.TEXT)
    default_value: str | None = Field(default="")
    column_position: int | None = Field(default=0)


class TemplateVariablesCollection(BaseModel):
    """Collection of template variables."""

    id: int
    name: str
    description: str
    columns: list[CollectionColumn] = Field(default_factory=list)
    variables_count: int = 0
    read_only: bool = False
    created_at: datetime
    updated_at: datetime
    version: str | None = None


class TemplateVariablesCollectionWithEntries(TemplateVariablesCollection):
    """Template variables collection with entries and rich model methods.

    This class represents a collection returned from the Elluminate API with
    its template variables loaded. Collections have rich methods like add_many()
    and delete_variables() that require a connection to the API client.

    Important:
        Do NOT instantiate this class directly. Rich model methods will not work
        on manually constructed instances. Always obtain collections through the
        client:

        - client.get_collection(name="...")
        - client.create_collection("...")
        - client.get_or_create_collection("...")

    Example:
        # ✓ Correct - obtained through client
        collection = client.get_collection(name="Test Cases")
        collection.add_many(variables=[...])  # Works

        # ✗ Wrong - manually constructed
        collection = TemplateVariablesCollectionWithEntries(id=1, name="Test", ...)
        collection.add_many(...)  # Raises ModelNotBoundError

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    variables: list[TemplateVariables]
    _client: "Client | AsyncClient | None" = PrivateAttr(default=None)

    def __eq__(self, other: object) -> bool:
        """Compare collections by data fields only, ignoring _client."""
        if not isinstance(other, TemplateVariablesCollectionWithEntries):
            return NotImplemented
        return self.model_dump() == other.model_dump()

    def __hash__(self) -> int:
        """Make TemplateVariablesCollectionWithEntries hashable based on id."""
        return hash(self.id)

    def add_many(self, variables: list[dict[str, str]]) -> list[TemplateVariables]:
        """Add multiple variables to this collection.

        Args:
            variables: List of variable dictionaries to add.

        Returns:
            List of the newly added TemplateVariables objects.

        Example:
            added = collection.add_many([
                {"topic": "AI"},
                {"topic": "ML"},
            ])
            print(f"Added {len(added)} items")
            for item in added:
                print(item.input_values)

        """
        if self._client is None:
            raise ModelNotBoundError("Collection", _COLLECTION_HINT)
        added_items = self._client._template_variables.add_many_to_collection(variables=variables, collection=self)
        # Update the local variables list
        self.variables.extend(added_items)
        self.variables_count = len(self.variables)
        return added_items

    def items(self) -> Iterator[TemplateVariables]:
        """Iterate over the variables in this collection.

        Returns:
            Iterator over TemplateVariables in the collection.

        Example:
            for item in collection.items():
                print(item.input_values)

        """
        return iter(self.variables)

    def clear(self) -> TemplateVariablesCollectionWithEntries:
        """Delete all variables from this collection.

        Returns:
            Updated collection with no variables.

        Raises:
            ModelNotBoundError: If collection is not bound to a client.

        """
        if self._client is None:
            raise ModelNotBoundError("Collection", _COLLECTION_HINT)
        self._client._template_variables.delete_all(collection=self)
        # Refresh the collection
        updated = self._client._collections.get(id=self.id)
        updated._client = self._client
        return updated

    # ===== Async Methods =====

    async def aadd_many(self, variables: list[dict[str, str]]) -> list[TemplateVariables]:
        """Add multiple variables to this collection (async).

        Args:
            variables: List of variable dictionaries to add.

        Returns:
            List of the newly added TemplateVariables objects.

        Example:
            added = await collection.aadd_many([
                {"topic": "AI"},
                {"topic": "ML"},
            ])
            print(f"Added {len(added)} items")
            for item in added:
                print(item.input_values)

        """
        if self._client is None:
            raise ModelNotBoundError("Collection", _COLLECTION_HINT)
        added_items = await self._client._template_variables.aadd_many_to_collection(
            variables=variables, collection=self
        )
        # Update the local variables list
        self.variables.extend(added_items)
        self.variables_count = len(self.variables)
        return added_items

    async def aclear(self) -> TemplateVariablesCollectionWithEntries:
        """Delete all variables from this collection (async).

        Returns:
            Updated collection with no variables.

        Raises:
            ModelNotBoundError: If collection is not bound to a client.

        """
        if self._client is None:
            raise ModelNotBoundError("Collection", _COLLECTION_HINT)
        await self._client._template_variables.adelete_all(collection=self)
        # Refresh the collection
        updated = await self._client._collections.aget(id=self.id)
        updated._client = self._client
        return updated

    def generate_variables(self, prompt_template: PromptTemplate) -> TemplateVariables:
        """Generate a new test case using AI based on the prompt template.

        Uses the LLM to generate variable values that would be interesting
        test cases for the given prompt template.

        Args:
            prompt_template: The prompt template to generate variables for.
                The template's placeholders determine what variables are generated.

        Returns:
            The newly generated TemplateVariables object, which is also
            added to this collection.

        Raises:
            ModelNotBoundError: If collection is not bound to a client.

        Example:
            # Generate AI-powered test cases for a template
            template, _ = client.get_or_create_prompt_template(
                name="Explain Concept",
                messages="Explain {{concept}} to a {{audience}}."
            )
            collection, _ = client.get_or_create_collection(name="Generated Tests")

            # Generate 5 diverse test cases
            for _ in range(5):
                generated = collection.generate_variables(template)
                print(f"Generated: {generated.input_values}")

        """
        if self._client is None:
            raise ModelNotBoundError("Collection", _COLLECTION_HINT)
        generated = self._client._template_variables.generate(
            collection=self,
            prompt_template=prompt_template,
        )
        # Update the local variables list
        self.variables.append(generated)
        self.variables_count = len(self.variables)
        return generated

    async def agenerate_variables(self, prompt_template: PromptTemplate) -> TemplateVariables:
        """Generate a new test case using AI based on the prompt template (async).

        Uses the LLM to generate variable values that would be interesting
        test cases for the given prompt template.

        Args:
            prompt_template: The prompt template to generate variables for.
                The template's placeholders determine what variables are generated.

        Returns:
            The newly generated TemplateVariables object, which is also
            added to this collection.

        Raises:
            ModelNotBoundError: If collection is not bound to a client.

        Example:
            # Generate AI-powered test cases for a template
            template, _ = await client.get_or_create_prompt_template(
                name="Explain Concept",
                messages="Explain {{concept}} to a {{audience}}."
            )
            collection, _ = await client.get_or_create_collection(name="Generated Tests")

            # Generate 5 diverse test cases
            for _ in range(5):
                generated = await collection.agenerate_variables(template)
                print(f"Generated: {generated.input_values}")

        """
        if self._client is None:
            raise ModelNotBoundError("Collection", _COLLECTION_HINT)
        generated = await self._client._template_variables.agenerate(
            collection=self,
            prompt_template=prompt_template,
        )
        # Update the local variables list
        self.variables.append(generated)
        self.variables_count = len(self.variables)
        return generated


class CreateCollectionRequest(BaseModel):
    """Request to create a new template variables collection."""

    name: str | None = None
    description: str = ""
    variables: list[dict[str, Any]] | None = None
    columns: list[CollectionColumn] | None = None
    read_only: bool = False


class TemplateVariablesCollectionFilter(BaseModel):
    """Filter for template variables collections."""

    name: str | None = None
    name_search: str | None = None
    has_entries: bool | None = None


class TemplateVariablesCollectionSort(BaseModel):
    """Sort for template variables collections."""

    sort: Literal["name", "-name", "created_at", "-created_at", "updated_at", "-updated_at"] | None = None


class UpdateCollectionRequest(BaseModel):
    """Request to update a template variables collection."""

    name: str = Field(..., min_length=1)
    description: str | None = None
    read_only: bool | None = None
    columns: list[CollectionColumn] | None = Field(
        None,
        description="List of columns in the desired order. Missing columns are deleted, new columns are created as TEXT with default='', existing columns are reordered.",
    )
