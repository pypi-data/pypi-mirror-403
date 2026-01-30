import os
from datetime import datetime
from typing import Any, Literal, Type, TypedDict

import httpx
from loguru import logger
from openai.types.beta import AssistantToolChoiceOption, FunctionTool
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
    CollectionColumn,
    CriterionSet,
    Experiment,
    InferenceType,
    LLMConfig,
    PromptTemplate,
    RatingMode,
    ResponsesSample,
    TemplateVariablesCollection,
    TemplateVariablesCollectionWithEntries,
)
from elluminate.schemas.prompt_template import ChatCompletionMessageParam
from elluminate.utils import raise_for_status_with_detail


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


class Client:
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
        """Initialize the elluminate SDK client.

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
        self.sync_session = httpx.Client(
            headers=headers,
            timeout=timeout_config,
            follow_redirects=True,
            proxy=self.proxy,
        )

        # Check the SDK version compatibility and print warning if needed
        if not skip_version_check:
            self.check_version()

        # Load the project and set the route prefix
        self.projects = ProjectsResource(self)
        # The projects resource sets `current_project` and `project_route_prefix`
        self.current_project = self.projects.load_project(project_id=project_id)
        logger.info(f"Active project set to ID {self.current_project.id}")

        # Initialize the resources (private - use Client methods instead)
        self._prompt_templates = PromptTemplatesResource(self)
        self._collections = TemplateVariablesCollectionsResource(self)
        self._template_variables = TemplateVariablesResource(self)
        self._responses = ResponsesResource(self)
        self._criteria = CriteriaResource(self)
        self._criterion_sets = CriterionSetsResource(self)
        self._llm_configs = LLMConfigsResource(self)
        self._experiments = ExperimentsResource(self)
        self._ratings = RatingsResource(self)

    def get_info(self) -> str:
        """For debugging"""
        from elluminate import __version__

        return f"Client at {self.base_url} version {__version__}"

    def check_version(self) -> None:
        """Check if the SDK version is compatible with the required version.

        This method makes a network call to the backend to verify SDK compatibility.
        If the backend is unreachable, the check is silently skipped. If the SDK
        version is incompatible, a warning is logged with upgrade instructions.
        """
        from elluminate import __version__

        try:
            response = self.sync_session.post(
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
                pypi_response = httpx.get("https://pypi.org/pypi/elluminate/json", timeout=5.0)
                latest_version = pypi_response.json()["info"]["version"]
            except Exception:
                pass

            logger.warning(
                f"SDK version ({__version__}) is incompatible with backend "
                f"(requires {compatibility['required_sdk_version']}). "
                f"Latest version: {latest_version}. "
                "Run: pip install -U elluminate"
            )

    def __enter__(self) -> "Client":
        """Enter context manager.

        Returns:
            The client instance for use in the context.

        """
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        """Exit context manager and close the client.

        Args:
            exc_type: The type of exception raised, if any.
            exc_val: The exception instance raised, if any.
            exc_tb: The traceback of the exception, if any.

        """
        self.close()

    def close(self) -> None:
        """Close the client and release resources.

        This closes the underlying HTTP session. After calling close(),
        the client should not be used for further requests.

        """
        self.sync_session.close()

    # =========================================================================
    # v1.0 API: Top-level methods
    # =========================================================================

    def create_collection(
        self,
        name: str,
        description: str = "",
        variables: list[dict[str, Any]] | None = None,
        columns: list[str | CollectionColumn] | None = None,
        read_only: bool = False,
    ) -> TemplateVariablesCollectionWithEntries:
        """Create a new collection.

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
            collection = self._collections.create(
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

    def get_collection(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
    ) -> TemplateVariablesCollectionWithEntries:
        """Get an existing collection by name or id.

        Args:
            name: The name of the collection to get.
            id: The id of the collection to get.

        Returns:
            The collection with methods for further operations.

        Raises:
            ValueError: If neither or both name and id are provided, or if not found.

        """
        collection = self._collections.get(name=name, id=id)
        collection._client = self
        return collection

    def get_or_create_collection(
        self,
        name: str,
        defaults: CollectionDefaults | None = None,
    ) -> tuple[TemplateVariablesCollectionWithEntries, bool]:
        """Get an existing collection by name, or create it if it doesn't exist.

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
            collection, created = client.get_or_create_collection(
                name="my-collection",
                defaults={"description": "Test data", "columns": ["topic", "category"]},
            )

        """
        defaults = defaults or {}
        collection, created = self._collections.get_or_create(
            name=name,
            description=defaults.get("description", ""),
            variables=defaults.get("variables"),
            columns=defaults.get("columns"),
            read_only=defaults.get("read_only", False),
        )
        collection._client = self
        return collection, created

    def create_prompt_template(
        self,
        name: str,
        messages: str | list[ChatCompletionMessageParam],
        response_format: Type[BaseModel] | dict[str, Any] | None = None,
        tools: list[FunctionTool] | None = None,
        tool_choice: AssistantToolChoiceOption | None = None,
    ) -> PromptTemplate:
        """Create a new prompt template.

        This creates version 1 of a new template. Use template.new_version()
        to create subsequent versions.

        Args:
            name: The name for the new template.
            messages: The template string with {{placeholders}}, or a list of
                ChatCompletionMessageParam dicts for multi-turn conversations.
            response_format: Optional JSON schema for structured output.
            tools: Optional list of tools for function calling.
            tool_choice: Optional tool choice setting.

        Returns:
            The newly created prompt template (version 1).

        Raises:
            ConflictError: If a template with this name already exists.

        Example:
            template = client.create_prompt_template(
                name="Essay Writer",
                messages="Write an essay about {{topic}}.",
            )

        """
        from elluminate.exceptions import ConflictError

        try:
            new_template = self._prompt_templates.create(
                name=name,
                messages=messages,
                response_format=response_format,
                tools=tools,
                tool_choice=tool_choice,
            )
            new_template._client = self
            return new_template
        except ConflictError as e:
            # Re-raise with resource details
            raise ConflictError(
                message=f"Prompt template '{name}' already exists",
                resource_type="prompt_template",
                resource_name=name,
            ) from e

    def get_prompt_template(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
        version: int | None = None,
    ) -> PromptTemplate:
        """Get an existing prompt template by name or id.

        Args:
            name: The name of the template to get (returns latest version by default).
            id: The id of the template to get.
            version: Specific version to get (only used with name).

        Returns:
            The prompt template.

        Raises:
            ValueError: If neither or both name and id are provided, or if not found.

        """
        template = self._prompt_templates.get(name=name, id=id, version=version or "latest")
        template._client = self
        return template

    def get_or_create_prompt_template(
        self,
        name: str,
        messages: str | list[ChatCompletionMessageParam],
        *,
        response_format: Type[BaseModel] | dict[str, Any] | None = None,
        tools: list[FunctionTool] | None = None,
        tool_choice: AssistantToolChoiceOption | None = None,
    ) -> tuple[PromptTemplate, bool]:
        """Get an existing prompt template by name and content, or create it.

        All parameters (name, template, response_format, tools, tool_choice) are part
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
            template, created = client.get_or_create_prompt_template(
                name="My Template",
                messages="Explain {{topic}} simply.",
                response_format=MySchema,
                tools=[...],
            )

        """
        pt, created = self._prompt_templates.get_or_create(
            name=name,
            messages=messages,
            response_format=response_format,
            tools=tools,
            tool_choice=tool_choice,
        )
        pt._client = self
        return pt, created

    def create_experiment(
        self,
        name: str,
        prompt_template: PromptTemplate,
        collection: TemplateVariablesCollection,
        llm_config: LLMConfig | None = None,
        criterion_set: CriterionSet | None = None,
        description: str = "",
        rating_version: str | None = None,
    ) -> Experiment:
        """Create a new experiment.

        Args:
            name: The name of the experiment.
            prompt_template: The prompt template to use.
            collection: The collection of template variables to use.
            llm_config: Optional LLM config. Uses platform default if not specified.
            criterion_set: Optional criterion set. Falls back to template's linked set if omitted.
            description: Optional description.
            rating_version: Optional rating version to use. If not provided, uses project's
                default_rating_version.

        Returns:
            The newly created experiment. Call experiment.run() to execute it.

        """
        experiment = self._experiments.create(
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

    def list_collections(self) -> list[TemplateVariablesCollection]:
        """List all collections in the current project.

        Returns:
            List of collections (without entries - use get_collection for full data).

        """
        return self._collections.list()

    def list_prompt_templates(self, name: str | None = None) -> list[PromptTemplate]:
        """List all prompt templates in the current project.

        Args:
            name: Filter by template name (exact match).

        Returns:
            List of prompt templates.

        """
        return self._prompt_templates.list(name=name)

    def list_experiments(
        self,
        prompt_template: PromptTemplate | None = None,
        collection: TemplateVariablesCollection | None = None,
        llm_config: LLMConfig | None = None,
    ) -> list[Experiment]:
        """List all experiments in the current project.

        Args:
            prompt_template: Filter to only return experiments using this template.
            collection: Filter to only return experiments using this collection.
            llm_config: Filter to only return experiments using this LLM config.

        Returns:
            List of experiments.

        """
        return self._experiments.list(
            prompt_template=prompt_template,
            collection=collection,
            llm_config=llm_config,
        )

    def get_experiment(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
        fetch_responses: bool = True,
    ) -> Experiment:
        """Get an experiment by name or ID.

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
            experiment = client.get_experiment(name="My Experiment")

            # Get by ID without responses (faster)
            experiment = client.get_experiment(id=123, fetch_responses=False)

        """
        return self._experiments.get(name=name, id=id, fetch_responses=fetch_responses)

    def list_criterion_sets(self) -> list[CriterionSet]:
        """List all criterion sets in the current project.

        Returns:
            List of criterion sets.

        """
        return self._criterion_sets.list()

    def create_criterion_set(
        self,
        name: str,
        criteria: list[str] | None = None,
    ) -> CriterionSet:
        """Create a new criterion set.

        Args:
            name: The name for the new criterion set.
            criteria: Optional list of criterion strings to add.

        Returns:
            The newly created criterion set.

        Raises:
            ConflictError: If a criterion set with this name already exists.

        Example:
            cs = client.create_criterion_set(
                name="Quality Checks",
                criteria=["Is the response accurate?", "Is it concise?"],
            )

        """
        from elluminate.exceptions import ConflictError

        try:
            criterion_set = self._criterion_sets.create(name=name, criteria=criteria)
            criterion_set._client = self
            return criterion_set
        except ConflictError as e:
            raise ConflictError(
                message=f"Criterion set '{name}' already exists",
                resource_type="criterion_set",
                resource_name=name,
            ) from e

    def get_criterion_set(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
    ) -> CriterionSet:
        """Get an existing criterion set by name or id.

        Args:
            name: The name of the criterion set to get.
            id: The id of the criterion set to get.

        Returns:
            The criterion set.

        Raises:
            ValueError: If neither or both name and id are provided, or if not found.

        """
        criterion_set = self._criterion_sets.get(name=name, id=id)
        criterion_set._client = self
        return criterion_set

    def get_or_create_criterion_set(
        self,
        name: str,
        defaults: CriterionSetDefaults | None = None,
    ) -> tuple[CriterionSet, bool]:
        """Get an existing criterion set by name, or create it if it doesn't exist.

        Args:
            name: The name of the criterion set (lookup key).
            defaults: Dictionary of creation-only parameters. Only used when creating
                a new criterion set. Supported keys:
                - criteria: List of criterion strings to add.

        Returns:
            Tuple of (criterion_set, created) where created is True if newly created.

        Note:
            The 'defaults' parameters are only used when creating a new criterion set.
            If the criterion set already exists, defaults are ignored and the existing
            criterion set is returned as-is.

        Example:
            cs, created = client.get_or_create_criterion_set(
                name="quality-checks",
                defaults={"criteria": ["Is the response accurate?", "Is it concise?"]},
            )

        """
        defaults = defaults or {}
        criterion_set, created = self._criterion_sets.get_or_create(
            name=name,
            criteria=defaults.get("criteria"),
        )
        criterion_set._client = self
        return criterion_set, created

    def create_llm_config(
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
        """Create a new LLM configuration.

        Args:
            name: The name for the new LLM config.
            llm_model_name: The model name (e.g., "gpt-4o", "claude-3-sonnet").
            api_key: The API key for the LLM provider.
            description: Optional description.
            llm_base_url: Optional base URL override for the LLM API.
            api_version: Optional API version (e.g., for Azure OpenAI).
            max_connections: Maximum concurrent connections to the LLM provider.
            max_retries: Optional maximum number of retries.
            timeout: Optional timeout in seconds.
            system_message: Optional system message for the LLM.
            max_tokens: Optional maximum tokens to generate.
            top_p: Optional nucleus sampling parameter.
            temperature: Optional temperature setting.
            best_of: Optional number of completions to generate.
            top_k: Optional top-k sampling parameter.
            logprobs: Optional flag to return log probabilities.
            top_logprobs: Optional number of top log probabilities to return.
            reasoning_effort: Optional reasoning effort parameter for o-series models.
            verbosity: Optional verbosity parameter for GPT-5 and newer models.
            inference_type: Type of inference provider to use.
            custom_api_config: Optional configuration for custom API providers.
            custom_response_parser: Optional Python code to parse custom API responses.

        Returns:
            The newly created LLM configuration.

        Raises:
            ConflictError: If an LLM config with this name already exists.

        Example:
            config = client.create_llm_config(
                name="GPT-4o",
                llm_model_name="gpt-4o",
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.7,
            )

        """
        from elluminate.exceptions import ConflictError

        try:
            config = self._llm_configs.create(
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

    def get_llm_config(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
    ) -> LLMConfig:
        """Get an existing LLM config by name or id.

        Args:
            name: The name of the LLM config to get.
            id: The id of the LLM config to get.

        Returns:
            The LLM configuration.

        Raises:
            ValueError: If neither or both name and id are provided, or if not found.

        """
        return self._llm_configs.get(name=name, id=id)

    def get_or_create_llm_config(
        self,
        name: str,
        defaults: LLMConfigDefaults | None = None,
    ) -> tuple[LLMConfig, bool]:
        """Get an existing LLM config by name, or create it if it doesn't exist.

        Args:
            name: The name of the LLM config (lookup key).
            defaults: Dictionary of creation-only parameters. Only used when creating
                a new LLM config. Can be omitted if the config already exists.
                Required keys when creating:
                - llm_model_name: The model name (e.g., "gpt-4o", "claude-3-sonnet").
                - api_key: The API key for the LLM provider.
                Optional keys:
                - description: Description for the config.
                - llm_base_url: Base URL override for the LLM API.
                - api_version: API version (e.g., for Azure OpenAI).
                - temperature: Temperature setting.
                - max_tokens: Max tokens setting.
                - max_connections: Max concurrent connections (default 10).
                - max_retries: Max retries on failure.
                - timeout: Timeout in seconds.
                - system_message: Default system message.
                - top_p: Top-p sampling setting.
                - best_of: Best-of setting.
                - top_k: Top-k sampling setting.
                - logprobs: Whether to return log probabilities.
                - top_logprobs: Number of top log probabilities to return.
                - reasoning_effort: Reasoning effort level.
                - verbosity: Verbosity setting.
                - inference_type: Inference type (default "openai").
                - custom_api_config: Custom API configuration.
                - custom_response_parser: Custom response parser.

        Returns:
            Tuple of (config, created) where created is True if newly created.

        Raises:
            ValueError: If config doesn't exist and llm_model_name or api_key
                are not provided in defaults.

        Note:
            The 'defaults' parameters are only used when creating a new config.
            If the config already exists, defaults are ignored and the existing
            config is returned as-is.

        Example:
            config, created = client.get_or_create_llm_config(
                name="gpt-4o",
                defaults={
                    "llm_model_name": "gpt-4o",
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "temperature": 0.7,
                },
            )

        """
        defaults = defaults or {}

        llm_config, created = self._llm_configs.get_or_create(
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
        llm_config._client = self
        return llm_config, created

    def run_experiment(
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
        """Create and run an experiment in one call.

        This is the recommended way to run experiments. It creates the experiment
        and immediately generates responses and ratings, blocking until complete.

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
            experiment = client.run_experiment(
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
            criterion_set = self._criterion_sets.create(name=criterion_set_name)
            criterion_set.add_criteria(criteria)

        experiment = self._experiments.create(
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

    # ==================== Delete Methods ====================

    def delete_experiment(self, experiment: Experiment) -> None:
        """Delete an experiment.

        Args:
            experiment: The experiment to delete.

        """
        self._experiments.delete(experiment)

    def delete_collection(self, collection: TemplateVariablesCollection) -> None:
        """Delete a collection.

        Args:
            collection: The collection to delete.

        """
        self._collections.delete(collection)

    def delete_prompt_template(self, prompt_template: PromptTemplate) -> None:
        """Delete a prompt template.

        Args:
            prompt_template: The prompt template to delete.

        """
        self._prompt_templates.delete(prompt_template)

    def delete_criterion_set(self, criterion_set: CriterionSet) -> None:
        """Delete a criterion set.

        This will also delete all associated criteria.

        Args:
            criterion_set: The criterion set to delete.

        """
        self._criterion_sets.delete(criterion_set)

    def delete_llm_config(self, llm_config: LLMConfig) -> None:
        """Delete an LLM configuration.

        Args:
            llm_config: The LLM config to delete.

        """
        self._llm_configs.delete(llm_config)

    def list_comparison_samples(
        self,
        experiment_a: Experiment,
        experiment_b: Experiment,
        filter_samples_by: Literal["improved", "regressed"] | None = None,
        criterion_ids: list[int] | None = None,
    ) -> list[ResponsesSample]:
        """List comparison samples between two experiments.

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
        return self._responses.list_comparison_samples(
            experiment_a=experiment_a,
            experiment_b=experiment_b,
            filter_samples_by=filter_samples_by,
            criterion_ids=criterion_ids,
        )

    # Sync HTTP methods (use httpx.Client directly)
    def _get(self, path: str, **kwargs: Any) -> httpx.Response:
        response = self.sync_session.get(f"{self.project_route_prefix}/{path}", **kwargs)
        raise_for_status_with_detail(response)
        return response

    def _post(self, path: str, **kwargs: Any) -> httpx.Response:
        response = self.sync_session.post(f"{self.project_route_prefix}/{path}", **kwargs)
        raise_for_status_with_detail(response)
        return response

    def _put(self, path: str, **kwargs: Any) -> httpx.Response:
        response = self.sync_session.put(f"{self.project_route_prefix}/{path}", **kwargs)
        raise_for_status_with_detail(response)
        return response

    def _delete(self, path: str, **kwargs: Any) -> httpx.Response:
        response = self.sync_session.delete(f"{self.project_route_prefix}/{path}", **kwargs)
        raise_for_status_with_detail(response)
        return response

    def _patch(self, path: str, **kwargs: Any) -> httpx.Response:
        response = self.sync_session.patch(f"{self.project_route_prefix}/{path}", **kwargs)
        raise_for_status_with_detail(response)
        return response

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
