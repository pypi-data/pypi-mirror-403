from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Literal

from openai.types.beta import AssistantToolChoiceOption, FunctionTool
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, ConfigDict, PrivateAttr, model_validator

from elluminate.exceptions import ModelNotBoundError

if TYPE_CHECKING:
    from elluminate.async_client import AsyncClient
    from elluminate.client import Client
    from elluminate.schemas.criterion import Criterion

_PROMPT_TEMPLATE_HINT = (
    "This prompt template is not connected to a client. "
    "To use model methods, obtain prompt templates through: "
    "client.get_prompt_template(), client.create_prompt_template(), "
    "or client.get_or_create_prompt_template()."
)


class TemplateString(BaseModel):
    """Convenience class for rendering a string with template variables."""

    template_str: str
    _PLACEHOLDER_PATTERN: ClassVar[re.Pattern] = re.compile(r"{{\s*(\w+)\s*}}")

    @property
    def is_template(self) -> bool:
        """Return True if the template string contains any placeholders."""
        return bool(self._PLACEHOLDER_PATTERN.search(self.template_str))

    @property
    def placeholders(self) -> set[str]:
        """Return a set of all the placeholders in the template string."""
        return set(self._PLACEHOLDER_PATTERN.findall(self.template_str))

    def render(self, **kwargs: str) -> str:
        """Render the template string with the given variables. Raises ValueError if any placeholders are missing."""
        if not set(self.placeholders).issubset(set(kwargs.keys())):
            missing = set(self.placeholders) - set(kwargs.keys())
            raise ValueError(f"Missing template variables: {str(missing)}")

        def replacer(regex_match: re.Match[str]) -> str:
            var_name = regex_match.group(1)
            return str(kwargs[var_name])

        return self._PLACEHOLDER_PATTERN.sub(replacer, self.template_str)

    def __str__(self) -> str:
        return self.template_str

    def __eq__(self, other: object) -> bool:
        """Compare TemplateString with another object.

        If other is a string, compare with template_str.
        If other is a TemplateString, compare template_str values.
        """
        if isinstance(other, str):
            return self.template_str == other
        if isinstance(other, TemplateString):
            return self.template_str == other.template_str
        return NotImplemented


class PromptTemplateFilter(BaseModel):
    name: str | None = None
    version: int | Literal["latest"] | None = None
    search: str | None = None
    criterion_set_id: int | None = None

    @model_validator(mode="after")
    def validate_version_requires_name(self) -> "PromptTemplateFilter":
        if self.version is not None and not self.name:
            raise ValueError("Version can only be set when name is provided")
        return self


class PromptTemplate(BaseModel):
    """Prompt template model with rich model methods.

    This class represents a prompt template returned from the Elluminate API.
    Prompt templates have rich methods like new_version(), generate(), and
    evaluate() that require a connection to the API client.

    Important:
        Do NOT instantiate this class directly. Rich model methods will not work
        on manually constructed instances. Always obtain prompt templates through
        the client:

        - client.get_prompt_template(name="...")
        - client.create_prompt_template(...)
        - client.get_or_create_prompt_template(...)

    Example:
        # ✓ Correct - obtained through client
        template = client.get_prompt_template(name="Summarizer")
        new_version = template.new_version(messages="...")  # Works

        # ✗ Wrong - manually constructed
        template = PromptTemplate(id=1, name="Test", ...)
        template.new_version(...)  # Raises ModelNotBoundError

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    name: str
    version: int
    messages: List[ChatCompletionMessageParam] = []
    placeholders: set[str] = set()
    response_format_json_schema: Dict[str, Any] | None = None
    tools: List[FunctionTool] | None = None
    tool_choice: AssistantToolChoiceOption | None = None
    criterion_set_id: int | None = None
    created_at: datetime
    updated_at: datetime
    _client: "Client | AsyncClient | None" = PrivateAttr(default=None)

    def __eq__(self, other: object) -> bool:
        """Compare templates by data fields only, ignoring _client."""
        if not isinstance(other, PromptTemplate):
            return NotImplemented
        return self.model_dump() == other.model_dump()

    def __hash__(self) -> int:
        """Make PromptTemplate hashable based on id."""
        return hash(self.id)

    def new_version(
        self,
        messages: str | List[ChatCompletionMessageParam] | None = None,
        response_format: Dict[str, Any] | None = None,
        tools: List[FunctionTool] | None = None,
        tool_choice: AssistantToolChoiceOption | None = None,
    ) -> PromptTemplate:
        """Create a new version of this template.

        Args:
            messages: New messages for the template. If None, inherits from current version.
            response_format: New response format. If None, inherits from current version.
            tools: New tools. If None, inherits from current version.
            tool_choice: New tool choice. If None, inherits from current version.

        Returns:
            The new PromptTemplate version.

        Raises:
            ConflictError: If a version with this exact content already exists.
            ModelNotBoundError: If template is not bound to a client.

        """
        if self._client is None:
            raise ModelNotBoundError("PromptTemplate", _PROMPT_TEMPLATE_HINT)

        from elluminate.exceptions import ConflictError

        # Use current values as defaults
        new_messages = messages if messages is not None else self.messages
        new_response_format = response_format if response_format is not None else self.response_format_json_schema
        new_tools = tools if tools is not None else self.tools
        new_tool_choice = tool_choice if tool_choice is not None else self.tool_choice

        try:
            new_template = self._client._prompt_templates.create(
                messages=new_messages,
                name=self.name,
                parent_prompt_template=self,
                response_format=new_response_format,
                tools=new_tools,
                tool_choice=new_tool_choice,
            )
            new_template._client = self._client
            return new_template
        except ConflictError as e:
            raise ConflictError(
                message=f"Prompt template '{self.name}' already has a version with this content",
                status_code=e.status_code,
                response=None,  # Original response not preserved in sanitized exception
                resource_type="prompt_template",
                resource_name=self.name,
            ) from None

    def generate_criteria(self, delete_existing: bool = False) -> list[Criterion]:
        """Generate evaluation criteria for this template using an LLM.

        This method uses the project's default LLM to analyze the prompt template
        and generate appropriate evaluation criteria. The criteria will be added
        to a criterion set associated with this template.

        Args:
            delete_existing: If True, deletes any existing criteria before generating
                new ones. If False and criteria exist, raises an error. Defaults to False.

        Returns:
            List of generated Criterion objects.

        Raises:
            ModelNotBoundError: If template is not bound to a client.
            HTTPStatusError: If criteria already exist and delete_existing is False.

        Example:
            template, _ = client.get_or_create_prompt_template(
                name="My Template",
                messages="Explain {{topic}} simply.",
            )
            criteria = template.generate_criteria()

        """
        if self._client is None:
            raise ModelNotBoundError("PromptTemplate", _PROMPT_TEMPLATE_HINT)
        return self._client._criteria.generate_many(self, delete_existing=delete_existing)

    def get_or_generate_criteria(self) -> tuple[list[Criterion], bool]:
        """Get existing criteria or generate new ones if none exist.

        This method returns existing criteria if they exist, otherwise generates
        new criteria using an LLM.

        Returns:
            Tuple of (criteria_list, generated) where generated is True if criteria
            were newly generated, False if existing criteria were returned.

        Raises:
            ModelNotBoundError: If template is not bound to a client.

        Example:
            template = client.get_prompt_template(name="My Template")
            criteria, generated = template.get_or_generate_criteria()
            if generated:
                print("Generated new criteria")

        """
        if self._client is None:
            raise ModelNotBoundError("PromptTemplate", _PROMPT_TEMPLATE_HINT)
        return self._client._criteria.get_or_generate_many(self)

    def list_criteria(self) -> list[Criterion]:
        """List all criteria associated with this template.

        Returns:
            List of Criterion objects linked to this template.

        Raises:
            ModelNotBoundError: If template is not bound to a client.

        Example:
            template = client.get_prompt_template(name="My Template")
            criteria = template.list_criteria()
            for criterion in criteria:
                print(criterion.criterion_str)

        """
        if self._client is None:
            raise ModelNotBoundError("PromptTemplate", _PROMPT_TEMPLATE_HINT)
        return self._client._criteria.list(prompt_template=self)

    # ===== Async Methods =====

    async def anew_version(
        self,
        messages: str | List[ChatCompletionMessageParam] | None = None,
        response_format: Dict[str, Any] | None = None,
        tools: List[FunctionTool] | None = None,
        tool_choice: AssistantToolChoiceOption | None = None,
    ) -> PromptTemplate:
        """Create a new version of this template (async).

        Args:
            messages: New messages for the template. If None, inherits from current version.
            response_format: New response format. If None, inherits from current version.
            tools: New tools. If None, inherits from current version.
            tool_choice: New tool choice. If None, inherits from current version.

        Returns:
            The new PromptTemplate version.

        Raises:
            ConflictError: If a version with this exact content already exists.
            ModelNotBoundError: If template is not bound to a client.

        """
        if self._client is None:
            raise ModelNotBoundError("PromptTemplate", _PROMPT_TEMPLATE_HINT)

        from elluminate.exceptions import ConflictError

        # Use current values as defaults
        new_messages = messages if messages is not None else self.messages
        new_response_format = response_format if response_format is not None else self.response_format_json_schema
        new_tools = tools if tools is not None else self.tools
        new_tool_choice = tool_choice if tool_choice is not None else self.tool_choice

        try:
            new_template = await self._client._prompt_templates.acreate(
                messages=new_messages,
                name=self.name,
                parent_prompt_template=self,
                response_format=new_response_format,
                tools=new_tools,
                tool_choice=new_tool_choice,
            )
            new_template._client = self._client
            return new_template
        except ConflictError as e:
            raise ConflictError(
                message=f"Prompt template '{self.name}' already has a version with this content",
                status_code=e.status_code,
                response=None,  # Original response not preserved in sanitized exception
                resource_type="prompt_template",
                resource_name=self.name,
            ) from None

    async def agenerate_criteria(self, delete_existing: bool = False) -> list[Criterion]:
        """Generate evaluation criteria for this template using an LLM (async).

        This method uses the project's default LLM to analyze the prompt template
        and generate appropriate evaluation criteria. The criteria will be added
        to a criterion set associated with this template.

        Args:
            delete_existing: If True, deletes any existing criteria before generating
                new ones. If False and criteria exist, raises an error. Defaults to False.

        Returns:
            List of generated Criterion objects.

        Raises:
            ModelNotBoundError: If template is not bound to a client.
            HTTPStatusError: If criteria already exist and delete_existing is False.

        Example:
            template, _ = await async_client.get_or_create_prompt_template(
                name="My Template",
                messages="Explain {{topic}} simply.",
            )
            criteria = await template.agenerate_criteria()

        """
        if self._client is None:
            raise ModelNotBoundError("PromptTemplate", _PROMPT_TEMPLATE_HINT)
        return await self._client._criteria.agenerate_many(self, delete_existing=delete_existing)

    async def aget_or_generate_criteria(self) -> tuple[list[Criterion], bool]:
        """Get existing criteria or generate new ones if none exist (async).

        This method returns existing criteria if they exist, otherwise generates
        new criteria using an LLM.

        Returns:
            Tuple of (criteria_list, generated) where generated is True if criteria
            were newly generated, False if existing criteria were returned.

        Raises:
            ModelNotBoundError: If template is not bound to a client.

        Example:
            template = await client.get_prompt_template(name="My Template")
            criteria, generated = await template.aget_or_generate_criteria()
            if generated:
                print("Generated new criteria")

        """
        if self._client is None:
            raise ModelNotBoundError("PromptTemplate", _PROMPT_TEMPLATE_HINT)
        return await self._client._criteria.aget_or_generate_many(self)

    async def alist_criteria(self) -> list[Criterion]:
        """List all criteria associated with this template (async).

        Returns:
            List of Criterion objects linked to this template.

        Raises:
            ModelNotBoundError: If template is not bound to a client.

        Example:
            template = await client.get_prompt_template(name="My Template")
            criteria = await template.alist_criteria()
            for criterion in criteria:
                print(criterion.criterion_str)

        """
        if self._client is None:
            raise ModelNotBoundError("PromptTemplate", _PROMPT_TEMPLATE_HINT)
        return await self._client._criteria.alist(prompt_template=self)

    def render_messages(self, **kwargs: str) -> List[ChatCompletionMessageParam]:
        """Render the prompt template with the given variables."""
        rendered_messages = []

        for message in self.messages:
            # Create a copy of the message using dict unpacking
            rendered_message = {**message}

            # If the message has content, render it
            if "content" in message and message["content"]:
                template_string = TemplateString(template_str=message["content"])
                rendered_message["content"] = template_string.render(**kwargs)

            rendered_messages.append(rendered_message)

        return rendered_messages

    @model_validator(mode="before")
    @classmethod
    def fix_message_fields(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        # OpenAI's ChatCompletionAssistantMessageParam requires a tool_calls field.
        # Since this field is not always included, we initialize it
        # as an empty list when absent to ensure compatibility.
        if "messages" in data and isinstance(data["messages"], list):
            for i, msg in enumerate(data["messages"]):
                if isinstance(msg, dict):
                    if msg.get("role") == "assistant":
                        if "tool_calls" not in msg or msg["tool_calls"] is None:
                            data["messages"][i]["tool_calls"] = []

        return data


class CreatePromptTemplateRequest(BaseModel):
    """Request to create a new prompt template."""

    name: str | None = None
    messages: List[ChatCompletionMessageParam] = []
    response_format_json_schema: Dict[str, Any] | None = None
    tools: List[FunctionTool] | None = None
    tool_choice: AssistantToolChoiceOption | None = None
    parent_prompt_template_id: int | None = None

    @model_validator(mode="after")
    def validate_tool_choice_requires_tools(self) -> "CreatePromptTemplateRequest":
        """Validate that tool_choice cannot be set without tools."""
        if self.tool_choice is not None and self.tools is None:
            raise ValueError("tool_choice cannot be set without tools")
        return self
