from __future__ import annotations

from typing import Any, Dict, List, Literal, Type

from openai.types.beta import AssistantToolChoiceOption, FunctionTool
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam
from pydantic import BaseModel

from elluminate.resources.base import BaseResource
from elluminate.schemas import (
    CreatePromptTemplateRequest,
    CriterionSet,
    PromptTemplate,
    PromptTemplateFilter,
    TemplateVariablesCollection,
)


def _convert_response_format_to_backend_format(
    response_format: Type[BaseModel] | Dict[str, Any],
) -> Dict[str, Any]:
    """Convert a response format to the format expected by the backend.

    Args:
        response_format: Either a Pydantic model class or an OpenAI-style dict format

    Returns:
        Dictionary in the format expected by the backend

    """
    if isinstance(response_format, type) and issubclass(response_format, BaseModel):
        # Create a `json_schema` from this Pydantic model definition
        # Models the behavior of `openai.lib._pydantic.to_strict_json_schema`, but chose to not
        # use since it is a part of the private `_pydantic` module of the `openai` package
        schema = response_format.model_json_schema()
        if "additionalProperties" not in schema:
            schema["additionalProperties"] = False
        return {
            "type": "json_schema",
            "json_schema": {
                "name": response_format.__name__.lower(),
                "schema": schema,
                "strict": True,
            },
        }
    elif isinstance(response_format, dict):
        return response_format
    else:
        raise ValueError("response_format must be either a Pydantic model class or OpenAI structured outputs dict")


class PromptTemplatesResource(BaseResource):
    # Sync methods (use httpx.Client directly)

    def get(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
        version: int | Literal["latest"] = "latest",
    ) -> PromptTemplate:
        """Get a prompt template by name and version, or by id.

        Args:
            name (str | None): Name of the prompt template.
            id (int | None): ID of the prompt template.
            version (int | Literal["latest"]): Version number or "latest". Defaults to "latest".
                Only used when looking up by name; ignored when looking up by id.

        Returns:
            (PromptTemplate): The requested prompt template.

        Raises:
            ValueError: If neither or both name and id are provided.
            ValueError: If no template is found with given name and version.

        """
        if name is not None and id is not None:
            raise ValueError("Provide either 'name' or 'id', not both")
        if name is None and id is None:
            raise ValueError("Either 'name' or 'id' must be provided")

        if id is not None:
            # Fetch by id directly (version is ignored)
            response = self._get(f"prompt_templates/{id}")
            pt = PromptTemplate.model_validate(response.json())
            pt._client = self._client
            return pt

        # Fetch by name and version
        params = {}
        if name:
            params["name"] = name
        if version != "latest":
            params["version"] = str(version)

        response = self._get("prompt_templates", params=params)
        templates = []
        for template in response.json().get("items", []):
            pt = PromptTemplate.model_validate(template)
            pt._client = self._client
            templates.append(pt)
        if not templates:
            raise ValueError(f"No prompt template found with name {name} and version {version}")
        return templates[0]

    def list(
        self,
        name: str | None = None,
        criterion_set: CriterionSet | None = None,
        compatible_collection: TemplateVariablesCollection | None = None,
    ) -> list[PromptTemplate]:
        """Get a list of prompt templates.

        Args:
            name (str | None): Name of the prompt template to filter by.
            criterion_set (CriterionSet | None): Criterion set to filter by.
            compatible_collection (TemplateVariablesCollection | None): Compatible template variables collection to filter by.

        Returns:
            list[PromptTemplate]: A list of prompt templates.

        """
        filter = PromptTemplateFilter(
            name=name,
            criterion_set_id=criterion_set.id if criterion_set else None,
        ).model_dump(exclude_none=True)

        # Add empty sort options (required by the API)
        filter["sort_options"] = {}
        # Add compatible_collection_id separately if it exists
        if compatible_collection:
            filter["compatible_collection_id"] = compatible_collection.id

        return self._paginate_sync(
            path="prompt_templates",
            model=PromptTemplate,
            params=filter,
        )

    def create(
        self,
        messages: str | List[ChatCompletionMessageParam],
        name: str,
        parent_prompt_template: PromptTemplate | None = None,
        response_format: Type[BaseModel] | Dict[str, Any] | None = None,
        tools: List[FunctionTool] | None = None,
        tool_choice: AssistantToolChoiceOption | None = None,
    ) -> PromptTemplate:
        """Create a new prompt template.

        Args:
            messages: The template string with {{placeholders}}, or a list of
                ChatCompletionMessageParam dicts for multi-turn conversations.
            name: Name for the template.
            parent_prompt_template: Optional parent template to inherit from.
            response_format: Optional Pydantic model or OpenAI-style dict for structured output generation.
            tools: Optional list of tools available to the model.
            tool_choice: Optional tool choice setting.

        """
        if isinstance(messages, str):
            messages_list = [ChatCompletionUserMessageParam(role="user", content=messages)]
        else:
            messages_list = messages

        # Convert response_format to response_format_json_schema if provided
        response_format_json_schema = None
        if response_format is not None:
            response_format_json_schema = _convert_response_format_to_backend_format(response_format)

        prompt_template_create = CreatePromptTemplateRequest(
            name=name,
            messages=messages_list,
            response_format_json_schema=response_format_json_schema,
            tools=tools,
            tool_choice=tool_choice,
            parent_prompt_template_id=parent_prompt_template.id if parent_prompt_template else None,
        )

        response = self._post("prompt_templates", json=prompt_template_create.model_dump())
        pt = PromptTemplate.model_validate(response.json())
        pt._client = self._client
        return pt

    def get_or_create(
        self,
        messages: str | List[ChatCompletionMessageParam],
        name: str,
        parent_prompt_template: PromptTemplate | None = None,
        response_format: Type[BaseModel] | None = None,
        tools: List[FunctionTool] | None = None,
        tool_choice: AssistantToolChoiceOption | None = None,
    ) -> tuple[PromptTemplate, bool]:
        """Gets the prompt template by its name and messages content if it exists.
        If the prompt template name does not exist, it creates a new prompt template with version 1.
        If a prompt template with the same name exists, but the messages content is new,
        then it creates a new prompt template version with the new messages
        which will be the new latest version. When a prompt template with the same name and
        messages already exists, it returns the existing prompt template, ignoring the given
        parent_prompt_template.

        Args:
            messages: The template string with {{placeholders}}, or a list of
                ChatCompletionMessageParam dicts for multi-turn conversations.
            name: Name for the template.
            parent_prompt_template: Optional parent template to inherit from.
            response_format: Optional Pydantic model for structured output generation.
            tools: Optional list of tools available to the model.
            tool_choice: Optional tool choice setting.

        Returns:
            tuple[PromptTemplate, bool]: A tuple containing:
                - The prompt template
                - Boolean indicating if a new template was created (True) or existing one returned (False)

        Raises:
            ValueError: If a 409 response is received without a prompt_template_id.

        """
        from elluminate.exceptions import ConflictError

        try:
            return self.create(
                messages=messages,
                name=name,
                parent_prompt_template=parent_prompt_template,
                response_format=response_format,
                tools=tools,
                tool_choice=tool_choice,
            ), True
        except ConflictError as e:
            # Code 409 means resource already exists, simply get and return it
            # Extract the existing template ID from the sanitized response_info
            if e.response_info is not None and isinstance(e.response_info.body, dict):
                error_data = e.response_info.body
                template_id = error_data.get("prompt_template_id")
                if template_id is not None:
                    response = self._get(f"prompt_templates/{template_id}")
                    prompt_template = PromptTemplate.model_validate(response.json())
                    prompt_template._client = self._client
                    return prompt_template, False
            raise ValueError("Received 409 without prompt_template_id") from e

    def delete(self, prompt_template: PromptTemplate) -> None:
        """Deletes a prompt template.

        Args:
            prompt_template (PromptTemplate): The prompt template to delete.

        Raises:
            httpx.HTTPStatusError: If the prompt template doesn't exist or belongs to a different project.

        """
        self._delete(f"prompt_templates/{prompt_template.id}")

    # ===== Async Methods =====

    async def aget(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
        version: int | None = None,
    ) -> PromptTemplate:
        """Get a specific prompt template by name or id (async)."""
        if name is not None and id is not None:
            raise ValueError("Provide either 'name' or 'id', not both")
        if name is None and id is None:
            raise ValueError("Either 'name' or 'id' must be provided")

        if id is not None:
            response = await self._aget(f"prompt_templates/{id}")
            pt = PromptTemplate.model_validate(response.json())
            pt._client = self._client
            return pt

        # Get by name (and optionally version)
        params = {"name": name}
        if version is not None:
            params["version"] = version

        response = await self._aget("prompt_templates", params=params)
        data = response.json()
        items = data.get("items", [])

        if not items:
            version_msg = f" version {version}" if version is not None else ""
            raise ValueError(f"No prompt template found with name '{name}'{version_msg}")

        pt = PromptTemplate.model_validate(items[0])
        pt._client = self._client
        return pt

    async def alist(
        self,
        name: str | None = None,
        criterion_set: CriterionSet | None = None,
        compatible_collection: TemplateVariablesCollection | None = None,
    ) -> list[PromptTemplate]:
        """Get a list of prompt templates (async).

        Args:
            name: Name of the prompt template to filter by.
            criterion_set: Criterion set to filter by.
            compatible_collection: Compatible template variables collection to filter by.

        Returns:
            List of prompt templates.

        """
        filter = PromptTemplateFilter(
            name=name,
            criterion_set_id=criterion_set.id if criterion_set else None,
        ).model_dump(exclude_none=True)

        # Add empty sort options (required by the API)
        filter["sort_options"] = {}
        # Add compatible_collection_id separately if it exists
        if compatible_collection:
            filter["compatible_collection_id"] = compatible_collection.id

        return await self._paginate(
            "prompt_templates",
            model=PromptTemplate,
            params=filter,
            resource_name="Prompt Templates",
        )

    async def acreate(
        self,
        messages: str | List[ChatCompletionMessageParam],
        name: str,
        parent_prompt_template: PromptTemplate | None = None,
        response_format: Type[BaseModel] | Dict[str, Any] | None = None,
        tools: List[FunctionTool] | None = None,
        tool_choice: AssistantToolChoiceOption | None = None,
    ) -> PromptTemplate:
        """Create a new prompt template (async)."""
        if isinstance(messages, str):
            messages_list = [ChatCompletionUserMessageParam(role="user", content=messages)]
        else:
            messages_list = messages

        # Convert response_format to response_format_json_schema if provided
        response_format_json_schema = None
        if response_format is not None:
            response_format_json_schema = _convert_response_format_to_backend_format(response_format)

        prompt_template_create = CreatePromptTemplateRequest(
            name=name,
            messages=messages_list,
            response_format_json_schema=response_format_json_schema,
            tools=tools,
            tool_choice=tool_choice,
            parent_prompt_template_id=parent_prompt_template.id if parent_prompt_template else None,
        )

        response = await self._apost("prompt_templates", json=prompt_template_create.model_dump())
        pt = PromptTemplate.model_validate(response.json())
        pt._client = self._client
        return pt

    async def aget_or_create(
        self,
        messages: str | List[ChatCompletionMessageParam],
        name: str,
        parent_prompt_template: PromptTemplate | None = None,
        response_format: Type[BaseModel] | None = None,
        tools: List[FunctionTool] | None = None,
        tool_choice: AssistantToolChoiceOption | None = None,
    ) -> tuple[PromptTemplate, bool]:
        """Get or create a prompt template (async)."""
        from elluminate.exceptions import ConflictError

        try:
            return await self.acreate(
                messages=messages,
                name=name,
                parent_prompt_template=parent_prompt_template,
                response_format=response_format,
                tools=tools,
                tool_choice=tool_choice,
            ), True
        except ConflictError as e:
            # Code 409 means resource already exists, simply get and return it
            # Extract the existing template ID from the sanitized response_info
            if e.response_info is not None and isinstance(e.response_info.body, dict):
                error_data = e.response_info.body
                template_id = error_data.get("prompt_template_id")
                if template_id is not None:
                    response = await self._aget(f"prompt_templates/{template_id}")
                    prompt_template = PromptTemplate.model_validate(response.json())
                    prompt_template._client = self._client
                    return prompt_template, False
            raise ValueError("Received 409 without prompt_template_id") from e

    async def adelete(self, prompt_template: PromptTemplate) -> None:
        """Delete a prompt template (async)."""
        await self._adelete(f"prompt_templates/{prompt_template.id}")
