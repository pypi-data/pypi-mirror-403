from typing import Any

from loguru import logger

from elluminate.resources.base import BaseResource
from elluminate.schemas import InferenceType, LLMConfig


class LLMConfigsResource(BaseResource):
    # Sync methods (use httpx.Client directly)

    def get(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
    ) -> LLMConfig:
        """Get an LLM config by name or id.

        Args:
            name (str | None): Name of the LLM config.
            id (int | None): ID of the LLM config.

        Returns:
            (LLMConfig): The requested LLM config.

        Raises:
            ValueError: If neither or both name and id are provided, or if not found.

        """
        if name is not None and id is not None:
            raise ValueError("Provide either 'name' or 'id', not both")
        if name is None and id is None:
            raise ValueError("Either 'name' or 'id' must be provided")

        if id is not None:
            response = self._get(f"llm_configs/{id}")
            return LLMConfig.model_validate(response.json())

        response = self._get("llm_configs", params={"name": name})
        configs = [LLMConfig.model_validate(config) for config in response.json()["items"]]

        if not configs:
            raise ValueError(f"No LLM config found with name '{name}'")
        return configs[0]

    def create(
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
            name (str): Name for the LLM config.
            llm_model_name (str): Name of the LLM model.
            api_key (str): API key for the LLM service.
            description (str): Optional description for the LLM config.
            llm_base_url (str | None): Optional base URL for the LLM service.
            api_version (str | None): Optional API version.
            max_connections (int): Maximum number of concurrent connections to the LLM provider.
            max_retries (int | None): Optional maximum number of retries.
            timeout (int | None): Optional timeout in seconds.
            system_message (str | None): Optional system message for the LLM.
            max_tokens (int | None): Optional maximum tokens to generate.
            top_p (float | None): Optional nucleus sampling parameter.
            temperature (float | None): Optional temperature parameter.
            best_of (int | None): Optional number of completions to generate.
            top_k (int | None): Optional top-k sampling parameter.
            logprobs (bool | None): Optional flag to return log probabilities.
            top_logprobs (int | None): Optional number of top log probabilities to return.
            reasoning_effort (str | None): Optional reasoning effort parameter for o-series models.
            verbosity (str | None): Optional verbosity parameter for GPT-5 and newer models.
            inference_type (InferenceType): Type of Inference Provider to use.
            custom_api_config (dict | None): Optional configuration template for custom API providers.
            custom_response_parser (str | None): Optional Python code to parse custom API responses.

        Returns:
            (LLMConfig): The created LLM configuration.

        Raises:
            httpx.HTTPStatusError: If an LLM config with the same name already exists.

        """
        # The create request data is the same as the `LLMConfig`, just without the ID
        create_request_data = LLMConfig(
            name=name,
            description=description,
            llm_model_name=llm_model_name,
            api_key=api_key,
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
        ).model_dump(exclude={"id"})
        response = self._post("llm_configs", json=create_request_data)
        return LLMConfig.model_validate(response.json())

    def get_or_create(
        self,
        name: str,
        llm_model_name: str | None = None,
        api_key: str | None = None,
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
    ) -> tuple[LLMConfig, bool]:
        """Get an existing LLM config or create a new one.

        First attempts to get the config by name. If it doesn't exist, creates a new one
        using the provided parameters.

        Args:
            name (str): Name for the LLM config (lookup key).
            llm_model_name (str | None): Name of the LLM model. Required only if creating.
            api_key (str | None): API key for the LLM service. Required only if creating.
            description (str): Optional description for the LLM config.
            llm_base_url (str | None): Optional base URL for the LLM service.
            api_version (str | None): Optional API version.
            max_connections (int): Maximum number of concurrent connections to the LLM provider.
            max_retries (int | None): Optional maximum number of retries.
            timeout (int | None): Optional timeout in seconds.
            system_message (str | None): Optional system message for the LLM.
            max_tokens (int | None): Optional maximum tokens to generate.
            top_p (float | None): Optional nucleus sampling parameter.
            temperature (float | None): Optional temperature parameter.
            best_of (int | None): Optional number of completions to generate.
            top_k (int | None): Optional top-k sampling parameter.
            logprobs (bool | None): Optional flag to return log probabilities.
            top_logprobs (int | None): Optional number of top log probabilities to return.
            reasoning_effort (str | None): Optional reasoning effort parameter for o-series models.
            verbosity (str | None): Optional verbosity parameter for GPT-5 and newer models.
            inference_type (InferenceType): Type of Inference Provider to use.
            custom_api_config (dict | None): Optional configuration template for custom API providers.
            custom_response_parser (str | None): Optional Python code to parse custom API responses.

        Returns:
            tuple[LLMConfig, bool]: A tuple containing:
                - The LLM configuration
                - Boolean indicating if a new config was created (True) or existing one returned (False)

        Raises:
            ValueError: If config doesn't exist and llm_model_name or api_key are not provided.

        """
        # First attempt to get the existing config
        try:
            existing_config = self.get(name=name)
            logger.info(f"Found existing LLM config '{name}'")
            return existing_config, False
        except ValueError:
            # Config doesn't exist, validate required fields for creation
            if llm_model_name is None:
                raise ValueError("llm_model_name is required when creating a new LLM config")
            if api_key is None:
                raise ValueError("api_key is required when creating a new LLM config")

            # Create the config
            new_config = self.create(
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
            return new_config, True

    def delete(self, llm_config: LLMConfig) -> None:
        """Deletes an LLM configuration.

        Args:
            llm_config (LLMConfig): The LLM configuration to delete.

        Raises:
            httpx.HTTPStatusError: If the LLM config doesn't exist or belongs to a different project.

        """
        self._delete(f"llm_configs/{llm_config.id}")

    # ===== Async Methods =====

    async def alist(self) -> list[LLMConfig]:
        """List all LLM configs (async)."""
        return await self._paginate("llm_configs", model=LLMConfig, resource_name="LLM Configs")

    async def aget(self, *, name: str | None = None, id: int | None = None) -> LLMConfig:
        """Get an LLM config by name or id (async)."""
        if name is not None and id is not None:
            raise ValueError("Provide either 'name' or 'id', not both")
        if name is None and id is None:
            raise ValueError("Either 'name' or 'id' must be provided")

        if id is not None:
            response = await self._aget(f"llm_configs/{id}")
            return LLMConfig.model_validate(response.json())

        params = {"name": name}
        response = await self._aget("llm_configs", params=params)
        data = response.json()
        items = data.get("items", [])

        if not items:
            raise ValueError(f"No LLM config found with name '{name}'")

        return LLMConfig.model_validate(items[0])

    async def acreate(
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
        """Create a new LLM config (async)."""
        create_request_data = LLMConfig(
            name=name,
            description=description,
            llm_model_name=llm_model_name,
            api_key=api_key,
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
        ).model_dump(exclude={"id"})
        response = await self._apost("llm_configs", json=create_request_data)
        return LLMConfig.model_validate(response.json())

    async def aget_or_create(
        self,
        name: str,
        llm_model_name: str | None = None,
        **kwargs,
    ) -> tuple[LLMConfig, bool]:
        """Get or create an LLM config (async)."""
        from elluminate.exceptions import ConflictError

        try:
            if llm_model_name is None:
                raise ValueError("llm_model_name is required when creating a new LLM config")
            return await self.acreate(name=name, llm_model_name=llm_model_name, **kwargs), True
        except ConflictError:
            existing_config = await self.aget(name=name)
            if llm_model_name and existing_config.llm_model_name != llm_model_name:
                logger.warning(
                    f"LLM config '{name}' already exists with llm_model_name='{existing_config.llm_model_name}'. "
                    f"Returning existing config."
                )
            return existing_config, False

    async def adelete(self, llm_config: LLMConfig) -> None:
        """Delete an LLM config (async)."""
        await self._adelete(f"llm_configs/{llm_config.id}")
