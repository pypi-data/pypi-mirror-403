from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, PrivateAttr

from elluminate.exceptions import ModelNotBoundError
from elluminate.schemas.criterion import Criterion, CriterionIn
from elluminate.schemas.prompt_template import PromptTemplate

if TYPE_CHECKING:
    from elluminate.async_client import AsyncClient
    from elluminate.client import Client

_CRITERION_SET_HINT = (
    "This criterion set is not connected to a client. "
    "To use model methods, obtain criterion sets through: "
    "client.get_criterion_set(), client.create_criterion_set(), "
    "or client.get_or_create_criterion_set()."
)


class CriterionSet(BaseModel):
    """Criterion set model with rich model methods.

    This class represents a criterion set returned from the Elluminate API.
    Criterion sets have rich methods like add_criteria() and clear() that
    require a connection to the API client.

    Important:
        Do NOT instantiate this class directly. Rich model methods will not work
        on manually constructed instances. Always obtain criterion sets through
        the client:

        - client.get_criterion_set(name="...")
        - client.create_criterion_set("...")
        - client.get_or_create_criterion_set("...")

    Example:
        # ✓ Correct - obtained through client
        cs = client.get_criterion_set(name="Quality Checks")
        cs.add_criteria(["Is it accurate?"])  # Works

        # ✗ Wrong - manually constructed
        cs = CriterionSet(id=1, name="Test")
        cs.add_criteria([...])  # Raises ModelNotBoundError

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    name: str
    linked_prompt_templates: list[PromptTemplate] | None = None
    criteria: list[Criterion] | None = None
    _client: "Client | AsyncClient | None" = PrivateAttr(default=None)

    def __eq__(self, other: object) -> bool:
        """Compare criterion sets by data fields only, ignoring _client."""
        if not isinstance(other, CriterionSet):
            return NotImplemented
        return self.model_dump() == other.model_dump()

    def __hash__(self) -> int:
        """Make CriterionSet hashable based on id."""
        return hash(self.id)

    def add_criterion(self, criterion: str | CriterionIn) -> Criterion:
        """Add a single criterion to this criterion set.

        Args:
            criterion: Criterion string or CriterionIn object.

        Returns:
            The created Criterion.

        """
        if self._client is None:
            raise ModelNotBoundError("CriterionSet", _CRITERION_SET_HINT)
        results = self._client._criteria.add_many(criteria=[criterion], criterion_set=self)
        return results[0]

    def add_criteria(self, criteria: list[str | CriterionIn]) -> list[Criterion]:
        """Add multiple criteria to this criterion set.

        Args:
            criteria: List of criterion strings or CriterionIn objects.

        Returns:
            List of created Criteria.

        """
        if self._client is None:
            raise ModelNotBoundError("CriterionSet", _CRITERION_SET_HINT)
        return self._client._criteria.add_many(criteria=criteria, criterion_set=self)

    def clear(self) -> None:
        """Remove all criteria from this criterion set.

        This is useful during development when iterating on criteria definitions.
        After clearing, you can add new criteria with add_criteria().

        Raises:
            ModelNotBoundError: If criterion set is not bound to a client.

        Example:
            criterion_set, created = client.get_or_create_criterion_set(name="Quality Checks")
            if not created:
                criterion_set.clear()  # Remove existing criteria for fresh start
            criterion_set.add_criteria(["Is the response accurate?", "Is it concise?"])

        """
        if self._client is None:
            raise ModelNotBoundError("CriterionSet", _CRITERION_SET_HINT)
        # Use add_many with empty list and delete_existing=True to clear all criteria
        self._client._criteria.add_many(criteria=[], criterion_set=self, delete_existing=True)
        # Update local criteria list
        self.criteria = []

    # ===== Async Methods =====

    async def aadd_criterion(self, criterion: str | CriterionIn) -> Criterion:
        """Add a single criterion to this criterion set (async).

        Args:
            criterion: Criterion string or CriterionIn object.

        Returns:
            The created Criterion.

        """
        if self._client is None:
            raise ModelNotBoundError("CriterionSet", _CRITERION_SET_HINT)
        results = await self._client._criteria.aadd_many(criteria=[criterion], criterion_set=self)
        return results[0]

    async def aadd_criteria(self, criteria: list[str | CriterionIn]) -> list[Criterion]:
        """Add multiple criteria to this criterion set (async).

        Args:
            criteria: List of criterion strings or CriterionIn objects.

        Returns:
            List of created Criteria.

        """
        if self._client is None:
            raise ModelNotBoundError("CriterionSet", _CRITERION_SET_HINT)
        return await self._client._criteria.aadd_many(criteria=criteria, criterion_set=self)

    async def aclear(self) -> None:
        """Remove all criteria from this criterion set (async).

        This is useful during development when iterating on criteria definitions.
        After clearing, you can add new criteria with aadd_criteria().

        Raises:
            ModelNotBoundError: If criterion set is not bound to a client.

        Example:
            criterion_set, created = await client.get_or_create_criterion_set(name="Quality Checks")
            if not created:
                await criterion_set.aclear()  # Remove existing criteria for fresh start
            await criterion_set.aadd_criteria(["Is the response accurate?", "Is it concise?"])

        """
        if self._client is None:
            raise ModelNotBoundError("CriterionSet", _CRITERION_SET_HINT)
        # Use aadd_many with empty list and delete_existing=True to clear all criteria
        await self._client._criteria.aadd_many(criteria=[], criterion_set=self, delete_existing=True)
        # Update local criteria list
        self.criteria = []

    def link_template(self, template: PromptTemplate) -> CriterionSet:
        """Link this criterion set to a prompt template.

        Associates this criterion set with the given prompt template, so that
        the criteria will be used when evaluating responses from that template.

        Args:
            template: The prompt template to link.

        Returns:
            The updated CriterionSet.

        Raises:
            ModelNotBoundError: If criterion set is not bound to a client.

        Example:
            criterion_set, _ = client.get_or_create_criterion_set(name="Quality Checks")
            criterion_set.add_criteria(["Is the response accurate?", "Is it concise?"])
            criterion_set.link_template(my_template)

        """
        if self._client is None:
            raise ModelNotBoundError("CriterionSet", _CRITERION_SET_HINT)
        updated = self._client._criterion_sets.add_prompt_template(
            criterion_set=self,
            prompt_template=template,
        )
        updated._client = self._client
        return updated

    async def alink_template(self, template: PromptTemplate) -> CriterionSet:
        """Link this criterion set to a prompt template (async).

        Associates this criterion set with the given prompt template, so that
        the criteria will be used when evaluating responses from that template.

        Args:
            template: The prompt template to link.

        Returns:
            The updated CriterionSet.

        Raises:
            ModelNotBoundError: If criterion set is not bound to a client.

        Example:
            criterion_set, _ = await client.get_or_create_criterion_set(name="Quality Checks")
            await criterion_set.aadd_criteria(["Is the response accurate?", "Is it concise?"])
            await criterion_set.alink_template(my_template)

        """
        if self._client is None:
            raise ModelNotBoundError("CriterionSet", _CRITERION_SET_HINT)
        updated = await self._client._criterion_sets.aadd_prompt_template(
            criterion_set=self,
            prompt_template=template,
        )
        updated._client = self._client
        return updated

    def unlink_template(self, template: PromptTemplate) -> None:
        """Unlink this criterion set from a prompt template.

        Removes the association between this criterion set and the given prompt
        template. The criteria will no longer be used when evaluating responses
        from that template (unless explicitly passed to the experiment).

        Args:
            template: The prompt template to unlink.

        Raises:
            ModelNotBoundError: If criterion set is not bound to a client.

        Example:
            # Remove criterion set from a template
            criterion_set.unlink_template(old_template)

            # Link to a different template instead
            criterion_set.link_template(new_template)

        """
        if self._client is None:
            raise ModelNotBoundError("CriterionSet", _CRITERION_SET_HINT)
        self._client._criterion_sets.remove_prompt_template(
            criterion_set=self,
            prompt_template=template,
        )

    async def aunlink_template(self, template: PromptTemplate) -> None:
        """Unlink this criterion set from a prompt template (async).

        Removes the association between this criterion set and the given prompt
        template. The criteria will no longer be used when evaluating responses
        from that template (unless explicitly passed to the experiment).

        Args:
            template: The prompt template to unlink.

        Raises:
            ModelNotBoundError: If criterion set is not bound to a client.

        Example:
            # Remove criterion set from a template
            await criterion_set.aunlink_template(old_template)

            # Link to a different template instead
            await criterion_set.alink_template(new_template)

        """
        if self._client is None:
            raise ModelNotBoundError("CriterionSet", _CRITERION_SET_HINT)
        await self._client._criterion_sets.aremove_prompt_template(
            criterion_set=self,
            prompt_template=template,
        )


class CreateCriterionSetRequest(BaseModel):
    """Request to create a new criterion set.

    Args:
        name: The name of the criterion set
        criteria: Optional list of criteria to create alongside the criterion set

    """

    name: str
    criteria: list[CriterionIn] | None = None
