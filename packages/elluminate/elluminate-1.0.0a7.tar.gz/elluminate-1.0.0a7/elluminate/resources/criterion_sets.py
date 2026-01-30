from typing import List, Tuple

from loguru import logger

from elluminate.resources.base import BaseResource
from elluminate.schemas import (
    PromptTemplate,
)
from elluminate.schemas.criterion import CriterionIn
from elluminate.schemas.criterion_set import CreateCriterionSetRequest, CriterionSet


class CriterionSetsResource(BaseResource):
    # Sync methods (use httpx.Client directly)

    def list(self) -> List[CriterionSet]:
        """List all criterion sets in the project.

        Returns:
            list[CriterionSet]: List of criterion set objects.

        """
        return self._paginate_sync(
            path="criterion_sets",
            model=CriterionSet,
            resource_name="Criterion Sets",
        )

    def get(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
    ) -> CriterionSet:
        """Get a specific criterion set by name or id.

        Args:
            name: The name of the criterion set.
            id: The id of the criterion set.

        Returns:
            CriterionSet: The requested criterion set.

        Raises:
            ValueError: If neither or both name and id are provided, or if not found.

        """
        if name is not None and id is not None:
            raise ValueError("Provide either 'name' or 'id', not both")
        if name is None and id is None:
            raise ValueError("Either 'name' or 'id' must be provided")

        if id is not None:
            response = self._get(f"criterion_sets/{id}")
            cs = CriterionSet.model_validate(response.json())
            cs._client = self._client
            return cs

        # Get by name
        params = {"name": name}
        response = self._get("criterion_sets", params=params)

        data = response.json()
        items = data.get("items", [])

        if not items:
            raise ValueError(f"No criterion set found with name '{name}'")

        cs = CriterionSet.model_validate(items[0])
        cs._client = self._client
        return cs

    def create(
        self,
        name: str,
        criteria: List[str | CriterionIn] | None = None,
    ) -> CriterionSet:
        """Create a new criterion set.

        Args:
            name (str): The name of the criterion set.
            criteria (list[str | CriterionIn], optional): List of criterion strings or CriterionIn objects.

        Returns:
            CriterionSet: The created criterion set.

        """
        # Convert `str` criteria to `CriterionIn` before sending the request
        normalized_criteria = None
        if criteria:
            normalized_criteria = [CriterionIn(criterion_str=c) if isinstance(c, str) else c for c in criteria]

        request_data = CreateCriterionSetRequest(
            name=name,
            criteria=normalized_criteria,
        )
        response = self._post("criterion_sets", json=request_data.model_dump())
        criterion_set = CriterionSet.model_validate(response.json())
        criterion_set._client = self._client

        return criterion_set

    def get_or_create(
        self,
        name: str,
        criteria: List[str | CriterionIn] | None = None,
    ) -> Tuple[CriterionSet, bool]:
        """Get or create a criterion set.

        Attempts to get a criterion set first. If it doesn't exist, creates a new one.

        Args:
            name (str): The name of the criterion set.
            criteria (list[str | CriterionIn], optional): List of criterion strings or CriterionIn objects
                if creation is needed.

        Returns:
            Tuple[CriterionSet, bool]: A tuple containing:
                - The criterion set
                - Boolean indicating if a new criterion set was created (True) or existing one returned (False)

        """
        # First attempt to get the existing criterion set
        try:
            existing_criterion_set = self.get(name=name)
            logger.info(f"Found existing criterion set '{name}'")
            return existing_criterion_set, False
        except ValueError:
            # Criterion set doesn't exist, create it
            new_criterion_set = self.create(name=name, criteria=criteria)
            return new_criterion_set, True

    def delete(self, criterion_set: CriterionSet) -> None:
        """Delete a criterion set.

        This will also delete all associated criteria.

        Args:
            criterion_set (CriterionSet): The criterion set to delete.

        """
        self._delete(f"criterion_sets/{criterion_set.id}")

    def add_prompt_template(self, criterion_set: CriterionSet, prompt_template: PromptTemplate) -> CriterionSet:
        """Add a prompt template to an existing criterion set.

        Args:
            criterion_set (CriterionSet): The criterion set.
            prompt_template (PromptTemplate): The prompt template to add.

        Returns:
            CriterionSet: The updated criterion set.

        """
        response = self._put(
            f"criterion_sets/{criterion_set.id}/prompt_templates/{prompt_template.id}",
        )
        cs = CriterionSet.model_validate(response.json())
        cs._client = self._client
        return cs

    def remove_prompt_template(self, criterion_set: CriterionSet, prompt_template: PromptTemplate) -> None:
        """Remove a prompt template from a criterion set.

        Args:
            criterion_set (CriterionSet): The criterion set.
            prompt_template (PromptTemplate): The prompt template to remove.

        """
        self._delete(f"criterion_sets/{criterion_set.id}/prompt_templates/{prompt_template.id}")

    # ===== Async Methods =====

    async def alist(self) -> List[CriterionSet]:
        """List all criterion sets in the project (async)."""
        return await self._paginate(
            path="criterion_sets",
            model=CriterionSet,
            resource_name="Criterion Sets",
        )

    async def aget(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
    ) -> CriterionSet:
        """Get a specific criterion set by name or id (async)."""
        if name is not None and id is not None:
            raise ValueError("Provide either 'name' or 'id', not both")
        if name is None and id is None:
            raise ValueError("Either 'name' or 'id' must be provided")

        if id is not None:
            response = await self._aget(f"criterion_sets/{id}")
            cs = CriterionSet.model_validate(response.json())
            cs._client = self._client
            return cs

        # Get by name
        params = {"name": name}
        response = await self._aget("criterion_sets", params=params)

        data = response.json()
        items = data.get("items", [])

        if not items:
            raise ValueError(f"No criterion set found with name '{name}'")

        cs = CriterionSet.model_validate(items[0])
        cs._client = self._client
        return cs

    async def acreate(
        self,
        name: str,
        criteria: List[str | CriterionIn] | None = None,
    ) -> CriterionSet:
        """Create a new criterion set (async)."""
        normalized_criteria = None
        if criteria:
            normalized_criteria = [CriterionIn(criterion_str=c) if isinstance(c, str) else c for c in criteria]

        request_data = CreateCriterionSetRequest(
            name=name,
            criteria=normalized_criteria,
        )
        response = await self._apost("criterion_sets", json=request_data.model_dump())
        criterion_set = CriterionSet.model_validate(response.json())
        criterion_set._client = self._client
        return criterion_set

    async def aget_or_create(
        self,
        name: str,
        criteria: List[str | CriterionIn] | None = None,
    ) -> Tuple[CriterionSet, bool]:
        """Get or create a criterion set (async)."""
        try:
            existing_criterion_set = await self.aget(name=name)
            logger.info(f"Found existing criterion set '{name}'")
            return existing_criterion_set, False
        except ValueError:
            new_criterion_set = await self.acreate(name=name, criteria=criteria)
            return new_criterion_set, True

    async def adelete(self, criterion_set: CriterionSet) -> None:
        """Delete a criterion set (async)."""
        await self._adelete(f"criterion_sets/{criterion_set.id}")

    async def aadd_prompt_template(
        self, criterion_set: CriterionSet, prompt_template: PromptTemplate
    ) -> CriterionSet:
        """Add a prompt template to an existing criterion set (async)."""
        response = await self._aput(
            f"criterion_sets/{criterion_set.id}/prompt_templates/{prompt_template.id}",
        )
        cs = CriterionSet.model_validate(response.json())
        cs._client = self._client
        return cs

    async def aremove_prompt_template(self, criterion_set: CriterionSet, prompt_template: PromptTemplate) -> None:
        """Remove a prompt template from a criterion set (async)."""
        await self._adelete(f"criterion_sets/{criterion_set.id}/prompt_templates/{prompt_template.id}")
