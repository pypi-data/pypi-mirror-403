import json
import os
from datetime import datetime
from functools import wraps
from typing import Any, AsyncIterator, Literal, Type, TypedDict

import httpx
from httpx_sse import aconnect_sse
from loguru import logger
from openai.types.beta import AssistantToolChoiceOption, FunctionTool
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from elluminate.resources import (
    CriteriaResource,
    CriterionSetsResource,
    ExperimentsResource,
    LLMConfigsResource,
    ProjectsResource,
    PromptTemplatesResource,
    RatingsResource,
    ResponsesResource,
    TemplateVariablesCollectionsResource,
    TemplateVariablesResource,
)
from elluminate.schemas import (
    BatchCreateRatingRequest,
    CollectionColumn,
    CriterionSet,
    Experiment,
    InferenceType,
    LLMConfig,
    PromptResponse,
    PromptResponseFilter,
    PromptTemplate,
    RatingMode,
    ResponsesSample,
    TemplateVariablesCollection,
    TemplateVariablesCollectionWithEntries,
)
from elluminate.streaming import (
    BatchStatusEvent,
    ExperimentProgress,
    ExperimentStatusEvent,
    TaskStatus,
)
from elluminate.utils import raise_for_status_with_detail


def requires_initialization(func):
    """Decorator to ensure AsyncClient is initialized before API calls.

    This decorator automatically calls _initialize() on first use if the client
    wasn't initialized via the context manager. This allows AsyncClient to work
    correctly whether used with 'async with' or instantiated directly.

    Example:
        # With context manager (recommended)
        async with AsyncClient() as client:
            await client.get_collection(name="test")

        # Without context manager (also works)
        client = AsyncClient()
        await client.get_collection(name="test")  # Auto-initializes on first call
        await client.close()

    """

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self._initialized:
            await self._initialize()
        return await func(self, *args, **kwargs)

    return wrapper


# TypedDict definitions for get_or_create defaults parameters
class CollectionDefaults(TypedDict, total=False):
    """Typed defaults for get_or_create_collection."""

    description: str
    variables: list[dict[str, Any]]
    columns: list[str | CollectionColumn]
    read_only: bool


class CriterionSetDefaults(TypedDict, total=False):
    """Typed defaults for get_or_create_criterion_set."""

    criteria: list[str]


class LLMConfigDefaults(TypedDict, total=False):
    """Typed defaults for get_or_create_llm_config.

    Note: llm_model_name and api_key are required when creating a new config.
    """

    llm_model_name: str
    api_key: str
    description: str
    llm_base_url: str
    api_version: str
    temperature: float
    max_tokens: int
    max_connections: int
    max_retries: int
    timeout: int
    system_message: str
    top_p: float
    best_of: int
    top_k: int
    logprobs: bool
    top_logprobs: int
    reasoning_effort: str
    verbosity: str
    inference_type: str
    custom_api_config: dict[str, Any]
    custom_response_parser: str


class AsyncClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        token: str | None = None,
        project_id: int | None = None,
        api_key_env: str = "ELLUMINATE_API_KEY",
        token_env: str = "ELLUMINATE_OAUTH_TOKEN",
        base_url_env: str = "ELLUMINATE_BASE_URL",
        timeout: float = 120.0,
        proxy: str | None = None,
        skip_version_check: bool = False,
    ) -> None:
        """Initialize the elluminate SDK async client.

        Args:
            base_url (str): Base URL of the elluminate API. Defaults to "https://app.elluminate.de".
            api_key (str | None): API key for authentication. If not provided, will look for key in environment variable given by `api_key_env`.
            token (str | None): OAuth access token for authentication. If not provided, will look for token in environment variable given by `token_env`.
            project_id (int | None): Project ID to select.
            api_key_env (str): Name of environment variable containing API key. Defaults to "ELLUMINATE_API_KEY".
            token_env (str): Name of environment variable containing OAuth token. Defaults to "ELLUMINATE_OAUTH_TOKEN".
            base_url_env (str): Name of environment variable containing base URL. Defaults to "ELLUMINATE_BASE_URL". If set, overrides base_url.
            timeout (float): Timeout in seconds for API requests. Defaults to 120.0.
            proxy (str | None): Proxy URL for HTTP/HTTPS requests (e.g., "http://proxy.example.com:8080" or "http://user:pass@proxy.example.com:8080").
                If None or empty string, no proxy will be used.
            skip_version_check (bool): Skip the SDK version compatibility check. Useful for offline or restricted
                network environments. Defaults to False.

        Raises:
            ValueError: If neither API key nor token is provided or found in environment.

        """
        self.api_key, self.token = self._resolve_credentials(api_key, token, api_key_env, token_env)
        self.base_url = self._resolve_base_url(base_url, base_url_env)
        self.timeout = timeout
        self.proxy = self._resolve_proxy(proxy)

        # Local import to avoid circular imports when referencing the version
        from elluminate import __version__

        headers = self._build_default_headers(__version__)

        timeout_config = httpx.Timeout(self.timeout)
        self.async_session = httpx.AsyncClient(
            headers=headers,
            timeout=timeout_config,
            follow_redirects=True,
            proxy=self.proxy,
        )

        # Store these for context manager initialization
        self._skip_version_check = skip_version_check
        self._project_id = project_id
        self._initialized = False

        # Will be set by projects.load_project()
        self.project_route_prefix: str = ""
        self.current_project: Any = None

        # Initialize the resources (private - use AsyncClient methods instead)
        self._prompt_templates = PromptTemplatesResource(self)
        self._collections = TemplateVariablesCollectionsResource(self)
        self._template_variables = TemplateVariablesResource(self)
        self._responses = ResponsesResource(self)
        self._criteria = CriteriaResource(self)
        self._criterion_sets = CriterionSetsResource(self)
        self._llm_configs = LLMConfigsResource(self)
        self._experiments = ExperimentsResource(self)
        self._ratings = RatingsResource(self)
        self.projects = ProjectsResource(self)

    async def _initialize(self) -> None:
        """Initialize the client by checking version and loading project.

        This is called automatically when using the context manager.
        For non-context-manager usage, call this explicitly after creating the client.
        """
        if self._initialized:
            return

        # Check version
        if not self._skip_version_check:
            await self.check_version()

        # Load the project and set the route prefix
        self.current_project = await self.projects.aload_project(project_id=self._project_id)
        logger.info(f"Active project set to ID {self.current_project.id}")

        self._initialized = True

    async def __aenter__(self) -> "AsyncClient":
        """Enter async context manager.

        Returns:
            The client instance for use in the context.

        """
        await self._initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager and close the client.

        Args:
            exc_type: The type of exception raised, if any.
            exc_val: The exception instance raised, if any.
            exc_tb: The traceback of the exception, if any.

        """
        await self.close()

    async def close(self) -> None:
        """Close the client and release resources.

        This closes the underlying HTTP session. After calling close(),
        the client should not be used for further requests.

        """
        await self.async_session.aclose()

    def get_info(self) -> str:
        """For debugging"""
        from elluminate import __version__

        return f"AsyncClient at {self.base_url} version {__version__}"

    async def check_version(self) -> None:
        """Check if the SDK version is compatible with the required version.

        This method makes a network call to the backend to verify SDK compatibility.
        If the backend is unreachable, the check is silently skipped. If the SDK
        version is incompatible, a warning is logged with upgrade instructions.
        """
        from elluminate import __version__

        try:
            response = await self.async_session.post(
                f"{self.base_url}/api/v0/version/compatible",
                json={"current_sdk_version": __version__},
            )
            raise_for_status_with_detail(response)
            compatibility = response.json()
        except httpx.HTTPError as e:
            logger.debug(f"Version compatibility check failed: {e}")
            return

        if not compatibility["is_compatible"]:
            # PyPI lookup is best-effort - just for showing latest version in warning
            latest_version = "unknown"
            try:
                async with httpx.AsyncClient() as client:
                    pypi_response = await client.get("https://pypi.org/pypi/elluminate/json", timeout=5.0)
                    latest_version = pypi_response.json()["info"]["version"]
            except Exception:
                pass

            logger.warning(
                f"SDK version ({__version__}) is incompatible with backend "
                f"(requires {compatibility['required_sdk_version']}). "
                f"Latest version: {latest_version}. "
                "Run: pip install -U elluminate"
            )

    # =========================================================================
    # v1.0 API: Top-level async methods
    # =========================================================================

    @requires_initialization
    async def create_collection(
        self,
        name: str,
        description: str = "",
        variables: list[dict[str, Any]] | None = None,
        columns: list[str | CollectionColumn] | None = None,
        read_only: bool = False,
    ) -> TemplateVariablesCollectionWithEntries:
        """Create a new collection (async).

        Args:
            name: The name for the new collection.
            description: Optional description for the collection.
            variables: Optional list of variables to add to the collection.
            columns: Optional list of column definitions. Can be column names as strings
                (defaults to TEXT type) or CollectionColumn objects.
            read_only: Whether the collection should be read-only.

        Returns:
            The newly created collection with methods for further operations.

        Raises:
            ConflictError: If a collection with this name already exists.

        """
        from elluminate.exceptions import ConflictError

        try:
            collection = await self._collections.acreate(
                name=name,
                description=description,
                variables=variables,
                columns=columns,
                read_only=read_only,
            )
            collection._client = self
            return collection
        except ConflictError as e:
            # Re-raise with more specific resource details
            raise ConflictError(
                message=f"Collection '{name}' already exists",
                resource_type="collection",
                resource_name=name,
            ) from e

    @requires_initialization
    async def get_collection(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
    ) -> TemplateVariablesCollectionWithEntries:
        """Get an existing collection by name or id (async).

        Args:
            name: The name of the collection to get.
            id: The id of the collection to get.

        Returns:
            The collection with methods for further operations.

        Raises:
            ValueError: If neither or both name and id are provided, or if not found.

        """
        return await self._collections.aget(name=name, id=id)

    @requires_initialization
    async def get_or_create_collection(
        self,
        name: str,
        defaults: CollectionDefaults | None = None,
    ) -> tuple[TemplateVariablesCollectionWithEntries, bool]:
        """Get an existing collection by name, or create it if it doesn't exist (async).

        Args:
            name: The name of the collection (lookup key).
            defaults: Dictionary of creation-only parameters. Only used when creating
                a new collection. Supported keys:
                - description: Description for the collection.
                - variables: Initial variables to add (list of dicts).
                - columns: Column definitions (list of strings or CollectionColumn objects).
                  String column names default to TEXT type.
                - read_only: Whether collection is read-only.

        Returns:
            Tuple of (collection, created) where created is True if newly created.

        Note:
            The 'defaults' parameters are only used when creating a new collection.
            If the collection already exists, defaults are ignored and the existing
            collection is returned as-is.

        Example:
            collection, created = await client.get_or_create_collection(
                name="my-collection",
                defaults={"description": "Test data", "columns": ["topic", "category"]},
            )

        """
        defaults = defaults or {}
        collection, created = await self._collections.aget_or_create(
            name=name,
            description=defaults.get("description", ""),
            variables=defaults.get("variables"),
            columns=defaults.get("columns"),
            read_only=defaults.get("read_only", False),
        )
        collection._client = self
        return collection, created

    @requires_initialization
    async def create_prompt_template(
        self,
        name: str,
        messages: str | list[ChatCompletionMessageParam],
        response_format: Type[BaseModel] | dict[str, Any] | None = None,
        tools: list[FunctionTool] | None = None,
        tool_choice: AssistantToolChoiceOption | None = None,
    ) -> PromptTemplate:
        """Create a new prompt template (async).

        This creates version 1 of a new template. Use template.new_version()
        to create subsequent versions.

        Args:
            name: The name for the new template.
            messages: The template string with {{placeholders}}, or a list of
                ChatCompletionMessageParam dicts for multi-turn conversations.
            response_format: Optional JSON schema or Pydantic model for structured output.
            tools: Optional list of tools for function calling.
            tool_choice: Optional tool choice setting.

        Returns:
            The newly created prompt template (version 1).

        Raises:
            ConflictError: If a template with this name already exists.

        Example:
            template = await client.create_prompt_template(
                name="Essay Writer",
                messages="Write an essay about {{topic}}.",
            )

        """
        from elluminate.exceptions import ConflictError

        try:
            new_template = await self._prompt_templates.acreate(
                name=name,
                messages=messages,
                response_format=response_format,
                tools=tools,
                tool_choice=tool_choice,
            )
            new_template._client = self
            return new_template
        except ConflictError as e:
            # Re-raise with more specific resource details
            raise ConflictError(
                message=f"Prompt template '{name}' already exists",
                resource_type="prompt_template",
                resource_name=name,
            ) from e

    @requires_initialization
    async def get_prompt_template(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
        version: int | None = None,
    ) -> PromptTemplate:
        """Get an existing prompt template by name or id (async).

        Args:
            name: The name of the template to get (returns latest version by default).
            id: The id of the template to get.
            version: Specific version to get (only used with name).

        Returns:
            The prompt template.

        Raises:
            ValueError: If neither or both name and id are provided, or if not found.

        """
        return await self._prompt_templates.aget(name=name, id=id, version=version)

    @requires_initialization
    async def get_or_create_prompt_template(
        self,
        name: str,
        messages: str | list[ChatCompletionMessageParam],
        *,
        response_format: Type[BaseModel] | dict[str, Any] | None = None,
        tools: list[FunctionTool] | None = None,
        tool_choice: AssistantToolChoiceOption | None = None,
    ) -> tuple[PromptTemplate, bool]:
        """Get an existing prompt template by name and content, or create it (async).

        All parameters (name, messages, response_format, tools, tool_choice) are part
        of the template identity. A template is considered a match only if ALL these
        values match exactly.

        Behavior:
        - If a template with matching identity exists: returns it
        - If name exists but any other parameter differs: creates a new version
        - If name doesn't exist: creates version 1

        Args:
            name: The name of the template.
            messages: The template string with {{placeholders}}, or a list of
                ChatCompletionMessageParam dicts for multi-turn conversations.
            response_format: JSON schema or Pydantic model for structured output.
            tools: List of tools for function calling.
            tool_choice: Tool choice setting ("auto", "none", "required", etc.).

        Returns:
            Tuple of (template, created) where created is True if newly created.

        Example:
            template, created = await client.get_or_create_prompt_template(
                name="My Template",
                messages="Explain {{topic}} simply.",
                response_format=MySchema,
                tools=[...],
            )

        """
        template_obj, created = await self._prompt_templates.aget_or_create(
            name=name,
            messages=messages,
            response_format=response_format,
            tools=tools,
            tool_choice=tool_choice,
        )
        template_obj._client = self
        return template_obj, created

    @requires_initialization
    async def create_experiment(
        self,
        name: str,
        prompt_template: PromptTemplate,
        collection: TemplateVariablesCollection,
        llm_config: LLMConfig | None = None,
        criterion_set: CriterionSet | None = None,
        description: str = "",
        rating_version: str | None = None,
    ) -> Experiment:
        """Create a new experiment (async).

        Args:
            name: The name for the new experiment.
            prompt_template: The prompt template to use.
            collection: The template variables collection to test against.
            llm_config: Optional LLM config. Uses platform default if not specified.
            criterion_set: Optional criterion set for evaluation.
            description: Optional description for the experiment.
            rating_version: Optional rating version to use. If not provided, uses project's
                default_rating_version.

        Returns:
            The newly created experiment.

        Raises:
            ConflictError: If an experiment with this name already exists.

        Example:
            experiment = await client.create_experiment(
                name="Essay Test",
                prompt_template=template,
                collection=collection,
            )

        """
        from elluminate.exceptions import ConflictError

        try:
            experiment = await self._experiments.acreate(
                name=name,
                prompt_template=prompt_template,
                collection=collection,
                llm_config=llm_config,
                criterion_set=criterion_set,
                description=description,
                generate=False,  # Don't auto-generate, user calls run()
                rating_version=rating_version,
            )
            experiment._client = self
            return experiment
        except ConflictError as e:
            raise ConflictError(
                message=f"Experiment '{name}' already exists",
                resource_type="experiment",
                resource_name=name,
            ) from e

    @requires_initialization
    async def list_collections(self) -> list[TemplateVariablesCollection]:
        """List all collections in the current project (async).

        Returns:
            List of collections (without entries - use aget_collection for full data).

        """
        return await self._collections.alist()

    @requires_initialization
    async def list_prompt_templates(self, name: str | None = None) -> list[PromptTemplate]:
        """List all prompt templates in the current project (async).

        Args:
            name: Filter by template name (exact match).

        Returns:
            List of prompt templates.

        """
        return await self._prompt_templates.alist(name=name)

    @requires_initialization
    async def list_experiments(
        self,
        prompt_template: PromptTemplate | None = None,
        collection: TemplateVariablesCollection | None = None,
        llm_config: LLMConfig | None = None,
    ) -> list[Experiment]:
        """List all experiments in the current project (async).

        Args:
            prompt_template: Filter to only return experiments using this template.
            collection: Filter to only return experiments using this collection.
            llm_config: Filter to only return experiments using this LLM config.

        Returns:
            List of experiments.

        """
        return await self._experiments.alist(
            prompt_template=prompt_template,
            collection=collection,
            llm_config=llm_config,
        )

    @requires_initialization
    async def get_experiment(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
        fetch_responses: bool = True,
    ) -> Experiment:
        """Get an experiment by name or ID (async).

        Args:
            name: The name of the experiment to retrieve.
            id: The ID of the experiment to retrieve.
            fetch_responses: Whether to fetch responses for the experiment.
                Defaults to True. Set to False to skip fetching responses,
                which saves API calls when you only need experiment metadata.

        Returns:
            The experiment object.

        Raises:
            ValueError: If neither name nor id is provided, or if both are provided.
            ValueError: If no experiment is found with the given name.

        Example:
            # Get by name with responses
            experiment = await client.get_experiment(name="My Experiment")

            # Get by ID without responses (faster)
            experiment = await client.get_experiment(id=123, fetch_responses=False)

        """
        return await self._experiments.aget(name=name, id=id, fetch_responses=fetch_responses)

    @requires_initialization
    async def list_criterion_sets(self) -> list[CriterionSet]:
        """List all criterion sets in the current project (async).

        Returns:
            List of criterion sets.

        """
        return await self._criterion_sets.alist()

    @requires_initialization
    async def create_criterion_set(
        self,
        name: str,
        criteria: list[str] | None = None,
    ) -> CriterionSet:
        """Create a new criterion set (async).

        Args:
            name: The name for the new criterion set.
            criteria: Optional list of criterion strings to add.

        Returns:
            The newly created criterion set.

        Raises:
            ConflictError: If a criterion set with this name already exists.

        Example:
            cs = await client.create_criterion_set(
                name="Quality Checks",
                criteria=["Is the response accurate?", "Is it concise?"],
            )

        """
        from elluminate.exceptions import ConflictError

        try:
            criterion_set = await self._criterion_sets.acreate(name=name, criteria=criteria)
            criterion_set._client = self
            return criterion_set
        except ConflictError as e:
            raise ConflictError(
                message=f"Criterion set '{name}' already exists",
                resource_type="criterion_set",
                resource_name=name,
            ) from e

    @requires_initialization
    async def get_criterion_set(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
    ) -> CriterionSet:
        """Get an existing criterion set by name or id (async).

        Args:
            name: The name of the criterion set to get.
            id: The id of the criterion set to get.

        Returns:
            The criterion set.

        Raises:
            ValueError: If neither or both name and id are provided, or if not found.

        """
        criterion_set = await self._criterion_sets.aget(name=name, id=id)
        criterion_set._client = self
        return criterion_set

    @requires_initialization
    async def get_or_create_criterion_set(
        self,
        name: str,
        defaults: CriterionSetDefaults | None = None,
    ) -> tuple[CriterionSet, bool]:
        """Get an existing criterion set by name, or create it if it doesn't exist (async).

        Args:
            name: The name of the criterion set (lookup key).
            defaults: Dictionary of creation-only parameters. Only used when creating
                a new criterion set. Supported keys:
                - criteria: List of criterion strings to add.

        Returns:
            Tuple of (criterion_set, created) where created is True if newly created.

        Example:
            cs, created = await client.get_or_create_criterion_set(
                name="Quality Checks",
                defaults={"criteria": ["Is accurate?", "Is concise?"]},
            )

        """
        defaults = defaults or {}
        criterion_set, created = await self._criterion_sets.aget_or_create(
            name=name,
            criteria=defaults.get("criteria"),
        )
        criterion_set._client = self
        return criterion_set, created

    @requires_initialization
    async def create_llm_config(
        self,
        name: str,
        llm_model_name: str,
        api_key: str,
        description: str = "",
        llm_base_url: str | None = None,
        api_version: str | None = None,
        max_connections: int = 10,
        max_retries: int | None = None,
        timeout: int | None = None,
        system_message: str | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        temperature: float | None = None,
        best_of: int | None = None,
        top_k: int | None = None,
        logprobs: bool | None = None,
        top_logprobs: int | None = None,
        reasoning_effort: str | None = None,
        verbosity: str | None = None,
        inference_type: InferenceType = InferenceType.OPENAI,
        custom_api_config: dict[str, Any] | None = None,
        custom_response_parser: str | None = None,
    ) -> LLMConfig:
        """Create a new LLM configuration (async).

        Args:
            name: Name for the LLM config.
            llm_model_name: Name of the LLM model.
            api_key: API key for the LLM service.
            description: Optional description for the LLM config.
            llm_base_url: Optional base URL for the LLM service.
            api_version: Optional API version.
            max_connections: Maximum number of concurrent connections.
            max_retries: Optional maximum number of retries.
            timeout: Optional timeout in seconds.
            system_message: Optional system message for the LLM.
            max_tokens: Optional maximum tokens to generate.
            top_p: Optional nucleus sampling parameter.
            temperature: Optional temperature parameter.
            best_of: Optional number of completions to generate.
            top_k: Optional top-k sampling parameter.
            logprobs: Optional flag to return log probabilities.
            top_logprobs: Optional number of top log probabilities to return.
            reasoning_effort: Optional reasoning effort parameter for o-series models.
            verbosity: Optional verbosity parameter for GPT-5 and newer models.
            inference_type: Type of Inference Provider to use.
            custom_api_config: Optional configuration template for custom API providers.
            custom_response_parser: Optional Python code to parse custom API responses.

        Returns:
            The created LLM configuration.

        Raises:
            ConflictError: If an LLM config with this name already exists.

        """
        from elluminate.exceptions import ConflictError

        try:
            config = await self._llm_configs.acreate(
                name=name,
                llm_model_name=llm_model_name,
                api_key=api_key,
                description=description,
                llm_base_url=llm_base_url,
                api_version=api_version,
                max_connections=max_connections,
                max_retries=max_retries,
                timeout=timeout,
                system_message=system_message,
                max_tokens=max_tokens,
                top_p=top_p,
                temperature=temperature,
                best_of=best_of,
                top_k=top_k,
                logprobs=logprobs,
                top_logprobs=top_logprobs,
                reasoning_effort=reasoning_effort,
                verbosity=verbosity,
                inference_type=inference_type,
                custom_api_config=custom_api_config,
                custom_response_parser=custom_response_parser,
            )
            return config
        except ConflictError as e:
            raise ConflictError(
                message=f"LLM config '{name}' already exists",
                resource_type="llm_config",
                resource_name=name,
            ) from e

    @requires_initialization
    async def get_llm_config(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
    ) -> LLMConfig:
        """Get an existing LLM config by name or id (async).

        Args:
            name: The name of the LLM config to get.
            id: The id of the LLM config to get.

        Returns:
            The LLM configuration.

        Raises:
            ValueError: If neither or both name and id are provided, or if not found.

        """
        return await self._llm_configs.aget(name=name, id=id)

    @requires_initialization
    async def get_or_create_llm_config(
        self,
        name: str,
        defaults: LLMConfigDefaults | None = None,
    ) -> tuple[LLMConfig, bool]:
        """Get an existing LLM config by name, or create it if it doesn't exist (async).

        Args:
            name: The name of the LLM config (lookup key).
            defaults: Dictionary of creation-only parameters. Only used when creating.
                Required keys when creating:
                - llm_model_name: Name of the LLM model.
                - api_key: API key for the LLM service.
                Optional keys:
                - description, llm_base_url, api_version, temperature, max_tokens, etc.

        Returns:
            Tuple of (config, created) where created is True if newly created.

        Raises:
            ValueError: If creating and llm_model_name or api_key are not provided in defaults.

        Example:
            config, created = await client.get_or_create_llm_config(
                name="GPT-4",
                defaults={
                    "llm_model_name": "gpt-4",
                    "api_key": "sk-...",
                    "temperature": 0.7,
                },
            )

        """
        defaults = defaults or {}
        config, created = await self._llm_configs.aget_or_create(
            name=name,
            llm_model_name=defaults.get("llm_model_name"),
            api_key=defaults.get("api_key"),
            description=defaults.get("description", ""),
            llm_base_url=defaults.get("llm_base_url"),
            api_version=defaults.get("api_version"),
            max_connections=defaults.get("max_connections", 10),
            max_retries=defaults.get("max_retries"),
            timeout=defaults.get("timeout"),
            system_message=defaults.get("system_message"),
            max_tokens=defaults.get("max_tokens"),
            top_p=defaults.get("top_p"),
            temperature=defaults.get("temperature"),
            best_of=defaults.get("best_of"),
            top_k=defaults.get("top_k"),
            logprobs=defaults.get("logprobs"),
            top_logprobs=defaults.get("top_logprobs"),
            reasoning_effort=defaults.get("reasoning_effort"),
            verbosity=defaults.get("verbosity"),
            inference_type=defaults.get("inference_type", "openai"),
            custom_api_config=defaults.get("custom_api_config"),
            custom_response_parser=defaults.get("custom_response_parser"),
        )
        return config, created

    @requires_initialization
    async def run_experiment(
        self,
        name: str,
        prompt_template: PromptTemplate,
        collection: TemplateVariablesCollection,
        llm_config: LLMConfig | None = None,
        criterion_set: CriterionSet | None = None,
        criteria: list[str] | None = None,
        description: str = "",
        rating_mode: RatingMode = RatingMode.DETAILED,
        n_epochs: int = 1,
        timeout: float | None = None,
        rating_version: str | None = None,
    ) -> Experiment:
        """Create and run an experiment in one call (async).

        This is the recommended way to run experiments. It creates the experiment
        and immediately generates responses and ratings, awaiting until complete.

        Args:
            name: The name of the experiment.
            prompt_template: The prompt template to use.
            collection: The collection of template variables to use.
            llm_config: Optional LLM config. Uses platform default if not specified.
            criterion_set: Optional criterion set. Falls back to template's linked set if omitted.
            criteria: Optional list of criterion strings. If provided, auto-creates a
                criterion set named "{name} Criteria" and uses it. Cannot be used with
                criterion_set parameter.
            description: Optional description.
            rating_mode: The rating mode (FAST or DETAILED). FAST is quicker but
                without reasoning. DETAILED provides reasoning. Defaults to DETAILED.
            n_epochs: Number of times to run the experiment for each input. Useful
                for testing consistency across multiple runs. Defaults to 1.
            timeout: Optional timeout in seconds for the experiment execution.
            rating_version: Optional rating version to use. If not provided, uses project's
                default_rating_version.

        Returns:
            The completed experiment with results populated.

        Example:
            # Simple usage with inline criteria
            experiment = await client.run_experiment(
                name="My Experiment",
                prompt_template=template,
                collection=collection,
                criteria=["Is it accurate?", "Is it helpful?"],
            )

        Raises:
            ValueError: If both criterion_set and criteria are provided.

        """
        # Validate mutually exclusive parameters
        if criterion_set is not None and criteria is not None:
            raise ValueError("Cannot specify both 'criterion_set' and 'criteria'. Use one or the other.")

        # Auto-create criterion set from criteria list
        if criteria is not None:
            # Use timestamp to ensure unique name - avoids overwriting shared criterion sets
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            criterion_set_name = f"{name} Criteria ({timestamp})"
            criterion_set = await self._criterion_sets.acreate(name=criterion_set_name)
            await criterion_set.aadd_criteria(criteria)

        experiment = await self._experiments.acreate(
            name=name,
            prompt_template=prompt_template,
            collection=collection,
            llm_config=llm_config,
            criterion_set=criterion_set,
            description=description,
            rating_mode=rating_mode,
            n_epochs=n_epochs,
            generate=True,
            block=True,
            timeout=timeout,
            rating_version=rating_version,
        )
        experiment._client = self
        return experiment

    async def stream_experiment(
        self,
        name: str,
        prompt_template: PromptTemplate,
        collection: TemplateVariablesCollection,
        llm_config: LLMConfig | None = None,
        criterion_set: CriterionSet | None = None,
        criteria: list[str] | None = None,
        description: str = "",
        rating_mode: RatingMode = RatingMode.DETAILED,
        n_epochs: int = 1,
        polling_interval: float = 0.5,
    ) -> AsyncIterator[ExperimentStatusEvent]:
        """Stream experiment execution with real-time progress updates (async).

        This method creates and runs an experiment like run_experiment(), but streams
        real-time progress updates via Server-Sent Events instead of blocking until completion.
        Each event contains status, progress metrics, and incremental logs.

        Args:
            name: The name of the experiment.
            prompt_template: The prompt template to use.
            collection: The collection of template variables to use.
            llm_config: Optional LLM config. Uses platform default if not specified.
            criterion_set: Optional criterion set. Falls back to template's linked set if omitted.
            criteria: Optional list of criterion strings. If provided, auto-creates a
                criterion set named "{name} Criteria" and uses it. Cannot be used with
                criterion_set parameter.
            description: Optional description.
            rating_mode: The rating mode (FAST or DETAILED). FAST is quicker but
                without reasoning. DETAILED provides reasoning. Defaults to DETAILED.
            n_epochs: Number of times to run the experiment for each input. Defaults to 1.
            polling_interval: How often to poll for updates in seconds. Defaults to 0.5.
                Must be between 0.1 and 10.0 seconds.

        Yields:
            ExperimentStatusEvent objects with real-time progress. The final event
            (status=SUCCESS) contains the completed experiment in the result field.

        Example:
            async with AsyncClient() as client:
                async for event in client.stream_experiment(
                    name="My Experiment",
                    prompt_template=template,
                    collection=collection,
                    criteria=["Is it accurate?", "Is it helpful?"],
                ):
                    if event.status == TaskStatus.STARTED:
                        print(f"Progress: {event.progress.percent_complete:.1%}")
                        if event.logs_delta:
                            print(f"Logs: {event.logs_delta}")
                    elif event.status == TaskStatus.SUCCESS:
                        print("Complete!")
                        experiment = event.result

        Raises:
            ValueError: If both criterion_set and criteria are provided, or if
                polling_interval is out of range.
            RuntimeError: If generation fails.

        """
        # Ensure client is initialized (async generators can't use @requires_initialization)
        if not self._initialized:
            await self._initialize()

        # Validate parameters
        if criterion_set is not None and criteria is not None:
            raise ValueError("Cannot specify both 'criterion_set' and 'criteria'. Use one or the other.")

        if not 0.1 <= polling_interval <= 10.0:
            raise ValueError("polling_interval must be between 0.1 and 10.0 seconds")

        # Auto-create criterion set from criteria list
        if criteria is not None:
            if not criteria:
                raise ValueError("criteria must be a non-empty list")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            criterion_set_name = f"{name} Criteria ({timestamp})"
            criterion_set = await self._criterion_sets.acreate(name=criterion_set_name)
            await criterion_set.aadd_criteria(criteria)

        # Create experiment without blocking (generate=True triggers async task)
        experiment = await self._experiments.acreate(
            name=name,
            prompt_template=prompt_template,
            collection=collection,
            llm_config=llm_config,
            criterion_set=criterion_set,
            description=description,
            rating_mode=rating_mode,
            n_epochs=n_epochs,
            generate=True,
            block=False,  # Don't block, we'll stream instead
        )

        if not experiment.generation_task_id:
            raise RuntimeError("Failed to start experiment generation - no task ID returned")

        # Stream status updates
        stream_url = f"experiments/{experiment.id}/generation/{experiment.generation_task_id}/stream"
        async for status_data in self._astream_sse(stream_url, params={"polling_interval": polling_interval}):
            # Parse backend response into ExperimentStatusEvent
            try:
                event = ExperimentStatusEvent(
                    status=TaskStatus(status_data["status"]),
                    error_msg=status_data.get("error_msg"),
                    logs_delta=status_data.get("logs_delta"),
                    progress=(
                        ExperimentProgress(
                            responses_generated=status_data.get("completed_responses", 0),
                            responses_rated=status_data.get("completed_ratings", 0),
                            total_responses=status_data.get("total_responses", 0),
                        )
                        if status_data.get("completed_responses") is not None
                        else None
                    ),
                )
            except (KeyError, ValueError, TypeError) as e:
                # Log and re-raise with streaming context
                logger.error(f"Failed to parse experiment status event: {e}. Raw data: {status_data!r}")
                raise ValueError(
                    f"Backend sent malformed experiment status event. "
                    f"Expected valid status and progress fields but got: {status_data!r}"
                ) from e

            # On success, fetch the final experiment
            if event.status == TaskStatus.SUCCESS:
                final_experiment = await self._experiments.aget(id=experiment.id)
                event.result = final_experiment

            yield event

            # Terminal states - stop streaming
            if event.is_complete:
                break

    async def stream_batch_rate(
        self,
        prompt_responses: list[PromptResponse],
        rating_mode: RatingMode = RatingMode.DETAILED,
        polling_interval: float = 0.5,
    ) -> AsyncIterator[BatchStatusEvent]:
        """Stream batch rating operation with real-time progress updates (async).

        This method initiates a batch rating operation and streams real-time status
        updates via Server-Sent Events. Unlike rate_many() which blocks until completion,
        this method yields status events as the batch progresses.

        Note: Currently, the backend does not provide progress metrics (processed/total/failed)
        for batch rating operations, so event.progress will always be None. Status updates
        (PENDING, STARTED, SUCCESS, FAILURE) are still provided for visibility and error
        detection. Future backend enhancements may add progress tracking.

        Args:
            prompt_responses: List of prompt responses to rate.
            rating_mode: The rating mode (FAST or DETAILED). Defaults to DETAILED.
            polling_interval: How often to poll for updates in seconds. Defaults to 0.5.
                Must be between 0.1 and 10.0 seconds.

        Yields:
            BatchStatusEvent objects with real-time status updates. The final event
            (status=SUCCESS) contains the ratings in the result field as List[List[Rating]].
            Note: event.progress is currently always None (backend limitation).

        Example:
            async with AsyncClient() as client:
                responses = await client.list_responses(experiment_id=123)

                async for event in client.stream_batch_rate(
                    prompt_responses=responses,
                    rating_mode=RatingMode.DETAILED,
                ):
                    if event.status == TaskStatus.STARTED:
                        if event.progress:
                            print(f"Progress: {event.progress.percent_complete:.1%}")
                    elif event.status == TaskStatus.SUCCESS:
                        print("Complete!")
                        ratings = event.result  # List[List[Rating]]

        Raises:
            ValueError: If polling_interval is out of range.
            RuntimeError: If batch rating fails.

        """
        # Ensure client is initialized (async generators can't use @requires_initialization)
        if not self._initialized:
            await self._initialize()

        # Validate parameters
        if not 0.1 <= polling_interval <= 10.0:
            raise ValueError("polling_interval must be between 0.1 and 10.0 seconds")

        if not prompt_responses:
            raise ValueError("prompt_responses cannot be empty")

        # Initiate batch rating operation
        response = await self._apost(
            "ratings/batches",
            json=BatchCreateRatingRequest(
                prompt_response_ids=[pr.id for pr in prompt_responses],
                rating_mode=rating_mode,
            ).model_dump(),
        )
        task_id = response.json()

        if not task_id:
            raise RuntimeError("Failed to start batch rating - no task ID returned")

        # Stream status updates
        stream_url = f"ratings/batches/{task_id}/stream"
        async for status_data in self._astream_sse(stream_url, params={"polling_interval": polling_interval}):
            # Parse backend response into BatchStatusEvent
            try:
                event = BatchStatusEvent(
                    status=TaskStatus(status_data["status"]),
                    error_msg=status_data.get("error_msg"),
                    progress=None,  # Backend doesn't provide progress for batch rating yet
                )
            except (KeyError, ValueError, TypeError) as e:
                # Log and re-raise with streaming context
                logger.error(f"Failed to parse batch rating status event: {e}. Raw data: {status_data!r}")
                raise ValueError(
                    f"Backend sent malformed batch rating status event. "
                    f"Expected valid status field but got: {status_data!r}"
                ) from e

            # On success, fetch the ratings
            if event.status == TaskStatus.SUCCESS:
                # Fetch the responses which will have ratings
                responses = await self._responses.alist(
                    filters=PromptResponseFilter(response_ids=[pr.id for pr in prompt_responses])
                )
                event.result = [r.ratings for r in responses]

            yield event

            # Terminal states - stop streaming
            if event.is_complete:
                break

    @requires_initialization
    async def delete_experiment(self, experiment: Experiment) -> None:
        """Delete an experiment (async).

        Args:
            experiment: The experiment to delete.

        """
        await self._experiments.adelete(experiment)

    @requires_initialization
    async def delete_collection(self, collection: TemplateVariablesCollection) -> None:
        """Delete a collection (async).

        Args:
            collection: The collection to delete.

        """
        await self._collections.adelete(collection)

    @requires_initialization
    async def delete_prompt_template(self, prompt_template: PromptTemplate) -> None:
        """Delete a prompt template (async).

        Args:
            prompt_template: The template to delete.

        """
        await self._prompt_templates.adelete(prompt_template)

    @requires_initialization
    async def delete_criterion_set(self, criterion_set: CriterionSet) -> None:
        """Delete a criterion set (async).

        Args:
            criterion_set: The criterion set to delete.

        """
        await self._criterion_sets.adelete(criterion_set)

    @requires_initialization
    async def delete_llm_config(self, llm_config: LLMConfig) -> None:
        """Delete an LLM config (async).

        Args:
            llm_config: The LLM config to delete.

        """
        await self._llm_configs.adelete(llm_config)

    @requires_initialization
    async def list_comparison_samples(
        self,
        experiment_a: Experiment,
        experiment_b: Experiment,
        filter_samples_by: Literal["improved", "regressed"] | None = None,
        criterion_ids: list[int] | None = None,
    ) -> list[ResponsesSample]:
        """List comparison samples between two experiments (async).

        Returns representative response samples from both experiments grouped by
        template variables, enabling side-by-side comparison of results.

        Args:
            experiment_a: The first experiment (baseline).
            experiment_b: The second experiment to compare against baseline.
            filter_samples_by: Filter samples by performance difference.
                - "improved": Only show samples where B performs better than A
                - "regressed": Only show samples where B performs worse than A
            criterion_ids: Optional list of criterion IDs to consider when computing
                scores. If not provided, all criteria are used.

        Returns:
            Samples from both experiments for comparison.

        """
        return await self._responses.alist_comparison_samples(
            experiment_a=experiment_a,
            experiment_b=experiment_b,
            filter_samples_by=filter_samples_by,
            criterion_ids=criterion_ids,
        )

    # =========================================================================
    # Async HTTP methods (use httpx.AsyncClient)
    # =========================================================================

    async def _aget(self, path: str, **kwargs: Any) -> httpx.Response:
        if not self.project_route_prefix:
            raise RuntimeError(
                "AsyncClient not properly initialized. Use the async context manager:\n"
                "  async with AsyncClient() as client:\n"
                "      await client.get_collection(...)\n"
                "Or initialize manually:\n"
                "  client = AsyncClient()\n"
                "  await client._initialize()\n"
                "  await client.get_collection(...)"
            )
        response = await self.async_session.get(f"{self.project_route_prefix}/{path}", **kwargs)
        raise_for_status_with_detail(response)
        return response

    async def _apost(self, path: str, **kwargs: Any) -> httpx.Response:
        if not self.project_route_prefix:
            raise RuntimeError(
                "AsyncClient not properly initialized. Use the async context manager:\n"
                "  async with AsyncClient() as client:\n"
                "      await client.create_collection(...)"
            )
        response = await self.async_session.post(f"{self.project_route_prefix}/{path}", **kwargs)
        raise_for_status_with_detail(response)
        return response

    async def _aput(self, path: str, **kwargs: Any) -> httpx.Response:
        if not self.project_route_prefix:
            raise RuntimeError("AsyncClient not properly initialized. Use the async context manager.")
        response = await self.async_session.put(f"{self.project_route_prefix}/{path}", **kwargs)
        raise_for_status_with_detail(response)
        return response

    async def _adelete(self, path: str, **kwargs: Any) -> httpx.Response:
        if not self.project_route_prefix:
            raise RuntimeError("AsyncClient not properly initialized. Use the async context manager.")
        response = await self.async_session.delete(f"{self.project_route_prefix}/{path}", **kwargs)
        raise_for_status_with_detail(response)
        return response

    async def _apatch(self, path: str, **kwargs: Any) -> httpx.Response:
        if not self.project_route_prefix:
            raise RuntimeError("AsyncClient not properly initialized. Use the async context manager.")
        response = await self.async_session.patch(f"{self.project_route_prefix}/{path}", **kwargs)
        raise_for_status_with_detail(response)
        return response

    async def _astream_sse(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream Server-Sent Events from an endpoint.

        Args:
            path: API endpoint path relative to project route prefix
            params: Optional query parameters

        Yields:
            Parsed JSON data from each SSE event

        Raises:
            RuntimeError: If client not properly initialized
            ValueError: If event data is not valid JSON (wraps JSONDecodeError)

        """
        if not self.project_route_prefix:
            raise RuntimeError(
                "AsyncClient not properly initialized. Use the async context manager:\n"
                "  async with AsyncClient() as client:\n"
                "      async for event in client.stream_experiment(...):\n"
                "          ..."
            )

        url = f"{self.project_route_prefix}/{path}"

        async with aconnect_sse(
            self.async_session,
            "GET",
            url,
            params=params,
        ) as event_source:
            async for sse in event_source.aiter_sse():
                # Parse JSON data from event
                try:
                    yield json.loads(sse.data)
                except json.JSONDecodeError as e:
                    # Log the malformed event for debugging
                    logger.error(f"Failed to parse SSE event from {url}: {e}. Raw data: {sse.data!r}")
                    # Raise with context for data integrity (fail fast)
                    raise ValueError(
                        f"Received malformed SSE event from backend. "
                        f"Expected valid JSON but got: {sse.data[:200]!r}..."
                    ) from e

    # =========================================================================
    # Helper methods (shared with sync Client)
    # =========================================================================

    def _resolve_credentials(
        self,
        api_key: str | None,
        token: str | None,
        api_key_env: str,
        token_env: str,
    ) -> tuple[str | None, str | None]:
        if api_key is not None or token is not None:
            # Important: any token that is directly provided takes precedence over the environment variables
            resolved_api_key = api_key
            resolved_token = token
        else:
            resolved_api_key = os.getenv(api_key_env)
            resolved_token = os.getenv(token_env)

        if not resolved_api_key and not resolved_token:
            raise ValueError(f"Neither {api_key_env} nor {token_env} set.")
        return resolved_api_key, resolved_token

    def _resolve_base_url(self, base_url: str | None, base_url_env: str) -> str:
        resolved = base_url or os.getenv(base_url_env) or "https://app.elluminate.de"
        return resolved.rstrip("/")

    def _resolve_proxy(self, proxy: str | None) -> str | None:
        """Resolve proxy configuration from parameter.

        Args:
            proxy: Explicitly provided proxy URL. Empty string or None means no proxy.

        Returns:
            Proxy URL if configured, None otherwise (no proxy).

        Note:
            Environment variables (HTTP_PROXY, HTTPS_PROXY, ALL_PROXY) are NOT checked.
            If you need to use a proxy, you must explicitly provide the proxy parameter.

        """
        if proxy:
            return proxy
        return None

    def _build_default_headers(self, sdk_version: str) -> dict[str, str]:
        if self.api_key:
            logger.info(f"Using API key: {self.api_key[:5]}...")
            return {"X-API-Key": self.api_key, "SDK-Version": sdk_version}

        if not self.token:
            raise ValueError("OAuth token not provided.")

        logger.info(f"Using OAuth token: {self.token[:5]}...")
        return {"Authorization": f"Bearer {self.token}", "SDK-Version": sdk_version}
