from __future__ import annotations

import time
from typing import Any, Dict, List, Literal, overload

from loguru import logger
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
)

from elluminate.resources.base import BaseResource
from elluminate.schemas import (
    BatchCreatePromptResponseRequest,
    CreatePromptResponseRequest,
    Experiment,
    GenerationMetadata,
    GenerationParams,
    LLMConfig,
    PromptResponse,
    PromptResponseFilter,
    PromptTemplate,
    ResponsesSample,
    ResponsesSampleFilter,
    ResponsesSampleSortBy,
    ResponsesStats,
    TemplateVariables,
)
from elluminate.schemas.template_variables_collection import TemplateVariablesCollection


class ResponsesResource(BaseResource):
    # Sync methods (use httpx.Client directly)

    def list(
        self,
        prompt_template: PromptTemplate | None = None,
        template_variables: TemplateVariables | None = None,
        experiment: Experiment | None = None,
        collection: TemplateVariablesCollection | None = None,
        filters: PromptResponseFilter | None = None,
    ) -> list[PromptResponse]:
        """Returns the responses belonging to a prompt template, template variables, experiment, or collection.

        Args:
            prompt_template (PromptTemplate | None): The prompt template to get responses for.
            template_variables (TemplateVariables | None): The template variables to get responses for.
            experiment (Experiment | None): The experiment to get responses for.
            collection (TemplateVariablesCollection | None): The collection to get responses for.
            filters (PromptResponseFilter | None): The filters to apply to the responses.

        Returns:
            list[PromptResponse]: The list of prompt responses.

        """
        filters = filters or PromptResponseFilter()
        if prompt_template:
            filters.prompt_template_id = prompt_template.id
        if template_variables:
            filters.template_variables_id = template_variables.id
        if experiment:
            filters.experiment_id = experiment.id
        if collection:
            filters.collection_id = collection.id
        params = filters.model_dump(exclude_none=True)

        return self._paginate_sync(
            path="responses",
            model=PromptResponse,
            params=params,
            resource_name="Responses",
        )

    def list_samples(
        self,
        experiment: Experiment,
        exclude_perfect_responses: bool = False,
        show_only_annotated_responses: bool = False,
        filters: ResponsesSampleFilter | None = None,
        sort_by: ResponsesSampleSortBy | None = None,
    ) -> List[ResponsesSample]:
        """List samples for an experiment.

        Args:
            experiment (Experiment): The experiment to get samples for.
            exclude_perfect_responses (bool): Whether to exclude perfect responses.
            show_only_annotated_responses (bool): Whether to show only annotated responses.
            filters (ResponsesSampleFilter | None): The filters to apply to the samples.
            sort_by (ResponsesSampleSortBy | None): The sort order for the samples.

        Returns:
            List[ResponsesSample]: The list of samples.

        """
        filters = filters or ResponsesSampleFilter(
            experiment_id=experiment.id,
        )
        params = filters.model_dump(exclude_none=True)

        if exclude_perfect_responses:
            params["exclude_perfect_responses"] = True

        if show_only_annotated_responses:
            params["show_only_annotated_responses"] = True

        if sort_by:
            params["sort_by"] = sort_by.value

        response = self._get("responses/samples", params=params)
        return [ResponsesSample.model_validate(item) for item in response.json()]

    def list_comparison_samples(
        self,
        experiment_a: Experiment,
        experiment_b: Experiment,
        filter_samples_by: Literal["improved", "regressed"] | None = None,
        criterion_ids: list[int] | None = None,
        categorical_column_names: list[str] | None = None,
        categorical_column_values: list[str] | None = None,
    ) -> List[ResponsesSample]:
        """List comparison samples between two experiments.

        This returns representative response samples from both experiments grouped by
        template variables, enabling side-by-side comparison of results.

        Args:
            experiment_a (Experiment): The first experiment (baseline).
            experiment_b (Experiment): The second experiment to compare against baseline.
            filter_samples_by (str | None): Filter samples by performance difference.
                - "improved": Only show samples where B performs better than A
                - "regressed": Only show samples where B performs worse than A
            criterion_ids (list[int] | None): Optional list of criterion IDs to consider
                when computing scores. If not provided, all criteria are used.
            categorical_column_names (list[str] | None): Names of categorical columns to filter by.
            categorical_column_values (list[str] | None): Values to match for the specified columns.

        Returns:
            List[ResponsesSample]: Samples from both experiments for comparison.

        """
        params: Dict[str, Any] = {
            "experiment_a_id": experiment_a.id,
            "experiment_b_id": experiment_b.id,
        }

        if filter_samples_by:
            params["filter_samples_by"] = filter_samples_by

        if criterion_ids:
            params["criterion_ids"] = criterion_ids

        if categorical_column_names:
            params["categorical_column_names"] = categorical_column_names

        if categorical_column_values:
            params["categorical_column_values"] = categorical_column_values

        response = self._get("responses/comparison/samples", params=params)
        return [ResponsesSample.model_validate(item) for item in response.json()]

    def get_stats(
        self,
        llm_config: LLMConfig | None = None,
        days: int = 30,
    ) -> ResponsesStats:
        """Get usage statistics for responses in a project with optional LLM config filtering.

        Args:
            llm_config (LLMConfig | None): The LLM config to get stats of. If not provided, the project's default LLM config will be used.
            days (int): The number of days to get stats for. Defaults to 30. Must be between 1 and 90.

        Returns:
            ResponsesStats: The stats of the LLM config.

        """
        if days < 1 or days > 90:
            raise ValueError("Days must be between 1 and 90.")

        params = {
            "days": days,
        }
        if llm_config:
            params["llm_config_id"] = llm_config.id

        response = self._get("responses/stats", params=params)
        return ResponsesStats.model_validate(response.json())

    def add(
        self,
        response: str | List[ChatCompletionMessageParam],
        template_variables: TemplateVariables,
        experiment: Experiment,
        epoch: int = 1,
        metadata: LLMConfig | GenerationMetadata | None = None,
    ) -> PromptResponse:
        """Add a response to an experiment.

        Args:
            response (str | List[ChatCompletionMessageParam]): The response to add.
            template_variables (TemplateVariables): The template variables to use for the response.
            experiment (Experiment): The experiment this response belongs to.
            epoch (int): The epoch for the response within the experiment. Defaults to 1.
            metadata (LLMConfig | GenerationMetadata | None): Optional metadata to associate with the response.

        Returns:
            PromptResponse: The newly created prompt response object.

        """
        if isinstance(metadata, LLMConfig):
            metadata = GenerationMetadata(llm_model_config=metadata)

        if isinstance(response, str):
            messages = [ChatCompletionAssistantMessageParam(role="assistant", content=response, tool_calls=[])]
        elif not isinstance(response, list):
            messages = [response]
        else:
            messages = response

        prompt_response = CreatePromptResponseRequest(
            messages=messages,
            template_variables_id=template_variables.id,
            experiment_id=experiment.id,
            epoch=epoch,
            metadata=metadata,
        )

        server_response = self._post(
            "responses",
            json=prompt_response.model_dump(),
        )
        return PromptResponse.model_validate(server_response.json())

    def generate(
        self,
        template_variables: TemplateVariables,
        experiment: Experiment,
        llm_config: LLMConfig | None = None,
    ) -> PromptResponse:
        """Generate a response using an LLM.

        This method sends the prompt to an LLM for generation. If no LLM config is provided,
        the project's default LLM config will be used.

        Args:
            template_variables (TemplateVariables): The template variables to use for the response.
            experiment (Experiment): The experiment this response belongs to.
            llm_config (LLMConfig | None): Optional LLM configuration to use for generation.
                If not provided, the project's default config will be used.

        Returns:
            PromptResponse: The generated response object

        """
        if llm_config is not None and llm_config.id is None:
            logger.warning("The LLM config id is None. Default LLM config will be used.")

        prompt_response = CreatePromptResponseRequest(
            template_variables_id=template_variables.id,
            experiment_id=experiment.id,
            llm_config_id=llm_config.id if llm_config else None,
        )

        server_response = self._post(
            "responses",
            json=prompt_response.model_dump(),
        )
        return PromptResponse.model_validate(server_response.json())

    def add_many(
        self,
        responses: List[str | List[ChatCompletionMessageParam]],
        template_variables: List[TemplateVariables],
        experiment: Experiment,
        epoch: int = 1,
        metadata: List[LLMConfig | GenerationMetadata | None] | None = None,
        timeout: float | None = None,
        polling_interval: float = 3.0,
    ) -> List[PromptResponse]:
        """Add multiple responses to an experiment in bulk.

        Use this method when you have a list of responses to add, instead of adding them one by one with the add() method.

        Args:
            responses (list[str | List[ChatCompletionMessageParam]]): List of responses to add.
            template_variables (list[TemplateVariables]): List of template variables for each response.
            experiment (Experiment): The experiment these responses belong to.
            epoch (int): The epoch for the responses within the experiment. Defaults to 1.
            metadata (list[LLMConfig | GenerationMetadata | None] | None): Optional list of metadata for each response.
            timeout (float | None): Timeout in seconds for API requests. Defaults to no timeout.
            polling_interval (float): Time between status checks in seconds. Defaults to 3.0.

        Returns:
            list[PromptResponse]: List of newly created prompt response objects.

        """
        len_responses = len(responses)
        len_template_variables = len(template_variables)
        _metadata = metadata if metadata is not None else [None] * len_responses

        len_metadata = len(_metadata)
        if not (len_template_variables == len_responses == len_metadata):
            raise ValueError(
                f"All input lists must have the same length. Got {len_template_variables} for template_variables, "
                f"{len_responses} for responses, and {len_metadata} for metadata."
            )

        prompt_response_ins = []
        for resp, tmp_var, md in zip(responses, template_variables, _metadata):
            if isinstance(md, LLMConfig):
                md = GenerationMetadata(llm_model_config=md)

            if isinstance(resp, str):
                messages = [ChatCompletionAssistantMessageParam(role="assistant", content=resp, tool_calls=[])]
            elif not isinstance(resp, list):
                messages = [resp]
            else:
                messages = resp

            prompt_response_ins.append(
                CreatePromptResponseRequest(
                    messages=messages,
                    template_variables_id=tmp_var.id,
                    experiment_id=experiment.id,
                    epoch=epoch,
                    metadata=md,
                )
            )

        # Track existing responses before batch to identify new ones after completion.
        # NOTE: This requires fetching full response objects when we only need IDs.
        # A backend `list_ids` endpoint or batch API returning created IDs would reduce calls.
        existing_responses = self.list(experiment=experiment)
        existing_response_ids = {r.id for r in existing_responses}

        batch_request = BatchCreatePromptResponseRequest(
            prompt_response_ins=prompt_response_ins,
        )

        # Initiate batch operation
        response = self._post("responses/batches", json=batch_request.model_dump())
        task_id = response.json()

        # No task was started by the backend
        if task_id is None:
            return []

        # Poll for completion
        start_time = time.time()
        while timeout is None or time.time() - start_time < timeout:
            status_response = self._get(f"responses/batches/{task_id}")
            status_data = status_response.json()

            if status_data.get("status") == "FAILURE":
                raise RuntimeError(f"Batch creation failed: {status_data.get('error_msg')}")

            if status_data.get("status") == "SUCCESS":
                # Fetch all responses and return only new ones
                all_responses = self.list(experiment=experiment)
                return [r for r in all_responses if r.id not in existing_response_ids]

            time.sleep(polling_interval)

        raise TimeoutError(f"Batch operation timed out after {timeout} seconds")

    @overload
    def generate_many(
        self,
        experiment: Experiment,
        *,
        template_variables: List[TemplateVariables],
        llm_config: LLMConfig | None = None,
        timeout: float | None = None,
    ) -> List[PromptResponse]: ...

    @overload
    def generate_many(
        self,
        experiment: Experiment,
        *,
        collection: TemplateVariablesCollection,
        llm_config: LLMConfig | None = None,
        timeout: float | None = None,
    ) -> List[PromptResponse]: ...

    def generate_many(
        self,
        experiment: Experiment,
        *,
        template_variables: List[TemplateVariables] | None = None,
        collection: TemplateVariablesCollection | None = None,
        llm_config: LLMConfig | None = None,
        timeout: float | None = None,
        polling_interval: float = 3.0,
    ) -> List[PromptResponse]:
        """Generate multiple responses for an experiment.

        Use this method when you have a list of responses to generate, instead of generating them one by one with the generate() method.

        Either `template_variables` or `collection` can be provided:
        - If `template_variables` is given, it will use the provided list of template variables for each response.
        - If `collection` is given, it will use the template variables from the specified collection.

        Args:
            experiment (Experiment): The experiment these responses belong to.
            template_variables (list[TemplateVariables] | None): List of template variables for each response.
            collection (TemplateVariablesCollection | None): The collection to use for the template variables.
            llm_config (LLMConfig | None): Optional LLMConfig to use for generation.
            timeout (float): Timeout in seconds for API requests. Defaults to no timeout.
            polling_interval (float): Time between status checks in seconds. Defaults to 3.0.

        Returns:
            list[PromptResponse]: List of newly created prompt response objects.

        """
        if not any([template_variables, collection]):
            raise ValueError("Either template_variables or collection must be provided.")
        if all([template_variables, collection]):
            raise ValueError("Cannot provide both template_variables and collection.")

        if collection is not None:
            template_variables = self._client._template_variables.list(collection=collection)

        # This is just for the linter, the checks above should ensure this
        assert template_variables

        len_template_variables = len(template_variables)
        llm_configs = [llm_config] * len_template_variables

        prompt_response_ins = []
        for tmp_var, llm_conf in zip(template_variables, llm_configs):
            prompt_response_ins.append(
                CreatePromptResponseRequest(
                    template_variables_id=tmp_var.id,
                    experiment_id=experiment.id,
                    llm_config_id=llm_conf.id if llm_conf else None,
                )
            )

        batch_request = BatchCreatePromptResponseRequest(
            prompt_response_ins=prompt_response_ins,
        )

        # Initiate batch operation
        response = self._post("responses/batches", json=batch_request.model_dump())
        task_id = response.json()

        # No task was started by the backend
        if task_id is None:
            return []

        # Poll for completion
        start_time = time.time()
        while timeout is None or time.time() - start_time < timeout:
            status_response = self._get(f"responses/batches/{task_id}")
            status_data = status_response.json()

            if status_data.get("status") == "FAILURE":
                raise RuntimeError(f"Batch generation failed: {status_data.get('error_msg')}")

            if status_data.get("status") == "SUCCESS":
                # Fetch all responses for the experiment
                return self.list(experiment=experiment)

            time.sleep(polling_interval)

        raise TimeoutError(f"Batch operation timed out after {timeout} seconds")

    def delete(self, prompt_response: PromptResponse) -> None:
        """Delete a prompt response.

        Args:
            prompt_response (PromptResponse): The prompt response to delete.

        """
        self._delete(f"responses/{prompt_response.id}")

    def update_annotation(self, prompt_response: PromptResponse | int, annotation: str) -> PromptResponse:
        """Update the annotation of a prompt response.

        Annotations are useful for categorizing, labeling, or adding notes to responses,
        especially when reviewing failed responses or building golden answer sets.

        Args:
            prompt_response: The prompt response object or its ID
            annotation: The annotation text to set (empty string to clear)

        Returns:
            PromptResponse: The updated prompt response

        Example:
            ```python
            # Annotate a failed response
            response = client.responses.update_annotation(
                response_id=123,
                annotation="Failed due to incorrect entity extraction"
            )

            # Clear an annotation
            response = client.responses.update_annotation(response, "")
            ```

        """
        response_id = prompt_response.id if isinstance(prompt_response, PromptResponse) else prompt_response
        response = self._patch(f"responses/{response_id}", json={"annotation": annotation})
        return PromptResponse.model_validate(response.json())

    # ===== Async Methods =====

    async def alist(
        self,
        prompt_template: PromptTemplate | None = None,
        template_variables: TemplateVariables | None = None,
        experiment: Experiment | None = None,
        collection: TemplateVariablesCollection | None = None,
        filters: PromptResponseFilter | None = None,
    ) -> list[PromptResponse]:
        """Returns the responses belonging to a prompt template, template variables, experiment, or collection (async).

        Args:
            prompt_template: The prompt template to get responses for.
            template_variables: The template variables to get responses for.
            experiment: The experiment to get responses for.
            collection: The collection to get responses for.
            filters: The filters to apply to the responses.

        Returns:
            The list of prompt responses.

        """
        filters = filters or PromptResponseFilter()
        if prompt_template:
            filters.prompt_template_id = prompt_template.id
        if template_variables:
            filters.template_variables_id = template_variables.id
        if experiment:
            filters.experiment_id = experiment.id
        if collection:
            filters.collection_id = collection.id
        params = filters.model_dump(exclude_none=True)

        return await self._paginate(
            "responses",
            model=PromptResponse,
            params=params,
            resource_name="Responses",
        )

    async def alist_samples(
        self,
        experiment: Experiment,
        exclude_perfect_responses: bool = False,
        show_only_annotated_responses: bool = False,
        filters: ResponsesSampleFilter | None = None,
        sort_by: ResponsesSampleSortBy | None = None,
    ) -> list[ResponsesSample]:
        """List samples for an experiment (async).

        Args:
            experiment (Experiment): The experiment to get samples for.
            exclude_perfect_responses (bool): Whether to exclude perfect responses.
            show_only_annotated_responses (bool): Whether to show only annotated responses.
            filters (ResponsesSampleFilter | None): The filters to apply to the samples.
            sort_by (ResponsesSampleSortBy | None): The sort order for the samples.

        Returns:
            list[ResponsesSample]: The list of samples.

        """
        filters = filters or ResponsesSampleFilter(
            experiment_id=experiment.id,
        )
        params = filters.model_dump(exclude_none=True)

        if exclude_perfect_responses:
            params["exclude_perfect_responses"] = True

        if show_only_annotated_responses:
            params["show_only_annotated_responses"] = True

        if sort_by:
            params["sort_by"] = sort_by.value

        response = await self._aget("responses/samples", params=params)
        return [ResponsesSample.model_validate(item) for item in response.json()]

    async def alist_comparison_samples(
        self,
        experiment_a: Experiment,
        experiment_b: Experiment,
        filter_samples_by: Literal["improved", "regressed"] | None = None,
        criterion_ids: list[int] | None = None,
        categorical_column_names: list[str] | None = None,
        categorical_column_values: list[str] | None = None,
    ) -> list[ResponsesSample]:
        """List comparison samples between two experiments (async).

        This returns representative response samples from both experiments grouped by
        template variables, enabling side-by-side comparison of results.

        Args:
            experiment_a (Experiment): The first experiment (baseline).
            experiment_b (Experiment): The second experiment to compare against baseline.
            filter_samples_by (str | None): Filter samples by performance difference.
                - "improved": Only show samples where B performs better than A
                - "regressed": Only show samples where B performs worse than A
            criterion_ids (list[int] | None): Optional list of criterion IDs to consider
                when computing scores. If not provided, all criteria are used.
            categorical_column_names (list[str] | None): Names of categorical columns to filter by.
            categorical_column_values (list[str] | None): Values to match for the specified columns.

        Returns:
            list[ResponsesSample]: Samples from both experiments for comparison.

        """
        params: Dict[str, Any] = {
            "experiment_a_id": experiment_a.id,
            "experiment_b_id": experiment_b.id,
        }

        if filter_samples_by:
            params["filter_samples_by"] = filter_samples_by

        if criterion_ids:
            params["criterion_ids"] = criterion_ids

        if categorical_column_names:
            params["categorical_column_names"] = categorical_column_names

        if categorical_column_values:
            params["categorical_column_values"] = categorical_column_values

        response = await self._aget("responses/comparison/samples", params=params)
        return [ResponsesSample.model_validate(sample) for sample in response.json()]

    async def aget_stats(
        self,
        experiment_id: int,
    ) -> ResponsesStats:
        """Get response statistics for an experiment (async)."""
        params = {"experiment_id": experiment_id}
        response = await self._aget("responses/stats", params=params)
        return ResponsesStats.model_validate(response.json())

    async def aadd(
        self,
        experiment: Experiment,
        template_variables: TemplateVariables,
        messages: list[ChatCompletionMessageParam],
        generation_metadata: GenerationMetadata | None = None,
        error: str | None = None,
    ) -> PromptResponse:
        """Add a prompt response to an experiment (async)."""
        request = CreatePromptResponseRequest(
            experiment_id=experiment.id,
            template_variables_id=template_variables.id,
            messages=messages,
            generation_metadata=generation_metadata,
            error=error,
        )
        response = await self._apost("responses", json=request.model_dump(exclude_none=True))
        return PromptResponse.model_validate(response.json())

    async def agenerate(
        self,
        experiment: Experiment,
        template_variables: TemplateVariables,
        generation_params: GenerationParams | None = None,
    ) -> PromptResponse:
        """Generate a single prompt response for an experiment (async)."""
        payload = {
            "experiment_id": experiment.id,
            "template_variables_id": template_variables.id,
        }
        if generation_params is not None:
            payload["generation_params"] = generation_params.model_dump()

        response = await self._apost("responses/generate", json=payload)
        return PromptResponse.model_validate(response.json())

    async def aadd_many(
        self,
        experiment: Experiment,
        responses: list[
            tuple[
                TemplateVariables,
                list[ChatCompletionMessageParam],
                GenerationMetadata | None,
                str | None,
            ]
        ],
        timeout: float | None = None,
        polling_interval: float = 3.0,
    ) -> list[PromptResponse]:
        """Batch add responses to an experiment (async)."""
        import asyncio
        import time

        request_list = [
            CreatePromptResponseRequest(
                experiment_id=experiment.id,
                template_variables_id=tv.id,
                messages=msgs,
                generation_metadata=gen_meta,
                error=err,
            )
            for tv, msgs, gen_meta, err in responses
        ]

        response = await self._apost(
            "responses/batches",
            json=[r.model_dump(exclude_none=True) for r in request_list],
        )
        task_id = response.json()

        if task_id is None:
            return []

        start_time = time.time()
        while timeout is None or time.time() - start_time < timeout:
            status_response = await self._aget(f"responses/batches/{task_id}")
            status_data = status_response.json()

            if status_data.get("status") == "FAILURE":
                raise RuntimeError(f"Batch response creation failed: {status_data.get('error_msg')}")

            if status_data.get("status") == "SUCCESS":
                return await self.alist(filters=PromptResponseFilter(experiment_id=experiment.id))

            await asyncio.sleep(polling_interval)

        raise TimeoutError(f"Batch response creation timed out after {timeout} seconds")

    @overload
    async def agenerate_many(
        self,
        experiment: Experiment,
        template_variables: list[TemplateVariables],
        generation_params: GenerationParams | None = None,
        timeout: float | None = None,
        polling_interval: float = 3.0,
    ) -> list[PromptResponse]: ...

    @overload
    async def agenerate_many(
        self,
        experiment: Experiment,
        *,
        generation_params: GenerationParams | None = None,
        timeout: float | None = None,
        polling_interval: float = 3.0,
    ) -> list[PromptResponse]: ...

    async def agenerate_many(
        self,
        experiment: Experiment,
        template_variables: list[TemplateVariables] | None = None,
        generation_params: GenerationParams | None = None,
        timeout: float | None = None,
        polling_interval: float = 3.0,
    ) -> list[PromptResponse]:
        """Batch generate responses for an experiment (async)."""
        import asyncio
        import time

        payload: Dict[str, Any] = {"experiment_id": experiment.id}

        if template_variables is not None:
            payload["template_variables_ids"] = [tv.id for tv in template_variables]

        if generation_params is not None:
            payload["generation_params"] = generation_params.model_dump()

        response = await self._apost("responses/batches/generate", json=payload)
        task_id = response.json()

        if task_id is None:
            return []

        start_time = time.time()
        while timeout is None or time.time() - start_time < timeout:
            status_response = await self._aget(f"responses/batches/{task_id}")
            status_data = status_response.json()

            if status_data.get("status") == "FAILURE":
                raise RuntimeError(f"Batch generation failed: {status_data.get('error_msg')}")

            if status_data.get("status") == "SUCCESS":
                filter_params = PromptResponseFilter(experiment_id=experiment.id)
                if template_variables is not None:
                    filter_params.template_variables_ids = [tv.id for tv in template_variables]

                return await self.alist(filters=filter_params)

            await asyncio.sleep(polling_interval)

        raise TimeoutError(f"Batch generation timed out after {timeout} seconds")

    async def adelete(self, prompt_response: PromptResponse) -> None:
        """Delete a prompt response (async)."""
        await self._adelete(f"responses/{prompt_response.id}")

    async def aupdate_annotation(self, prompt_response: PromptResponse | int, annotation: str) -> PromptResponse:
        """Update the annotation for a prompt response (async)."""
        response_id = prompt_response.id if isinstance(prompt_response, PromptResponse) else prompt_response
        response = await self._apatch(f"responses/{response_id}", json={"annotation": annotation})
        return PromptResponse.model_validate(response.json())
