from __future__ import annotations

from loguru import logger
from pydantic import BaseModel

from elluminate.resources.base import BaseResource
from elluminate.schemas import (
    CreateExperimentRequest,
    CriterionSet,
    Experiment,
    ExperimentFilter,
    GenerationParams,
    LLMConfig,
    PromptTemplate,
    RatingMode,
    TemplateVariablesCollection,
)


class ExperimentsResource(BaseResource):
    # Sync methods (use httpx.Client directly)

    def get(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
        fetch_responses: bool = True,
    ) -> Experiment:
        """Get an experiment by name or id.

        Args:
            name: The name of the experiment to get.
            id: The id of the experiment to get.
            fetch_responses: Whether to fetch responses for the experiment.
                Defaults to True for backward compatibility. Set to False to save
                API calls when responses aren't needed.

        Returns:
            Experiment: The experiment object.

        Raises:
            ValueError: If neither or both name and id are provided, or if not found.

        """
        if name is not None and id is not None:
            raise ValueError("Provide either 'name' or 'id', not both")
        if name is None and id is None:
            raise ValueError("Either 'name' or 'id' must be provided")

        if id is not None:
            response = self._get(f"experiments/{id}")
            experiment = Experiment.model_validate(response.json())
            experiment._client = self._client
        else:
            response = self._get("experiments", params={"experiment_name": name})
            experiments = []
            for e in response.json()["items"]:
                exp = Experiment.model_validate(e)
                exp._client = self._client
                experiments.append(exp)

            if not experiments:
                raise ValueError(f"No experiment found with name '{name}'")

            # Since experiment names are unique per project, there should be only one if `experiments` is nonempty.
            experiment = experiments[0]

        if fetch_responses:
            responses = self._client._responses.list(experiment=experiment)
            experiment.rated_responses = responses

        return experiment

    def list(
        self,
        prompt_template: PromptTemplate | None = None,
        collection: TemplateVariablesCollection | None = None,
        llm_config: LLMConfig | None = None,
    ) -> list[Experiment]:
        """Get a list of experiments sorted by creation date.

        Args:
            prompt_template (PromptTemplate | None): The prompt template to filter by.
            collection (TemplateVariablesCollection | None): The collection to filter by.
            llm_config (LLMConfig | None): The LLM config to filter by.

        Returns:
            list[Experiment]: A list of experiments.

        """
        return self._paginate_sync(
            "experiments",
            model=Experiment,
            params=ExperimentFilter(
                prompt_template_id=prompt_template.id if prompt_template else None,
                collection_id=collection.id if collection else None,
                llm_config_id=llm_config.id if llm_config else None,
            ).model_dump(exclude_none=True),
        )

    def create(
        self,
        name: str,
        prompt_template: PromptTemplate | None,
        collection: TemplateVariablesCollection,
        llm_config: LLMConfig | None = None,
        criterion_set: CriterionSet | None = None,
        description: str = "",
        generate: bool = False,
        rating_mode: RatingMode = RatingMode.DETAILED,
        n_epochs: int = 1,
        block: bool = False,
        timeout: float | None = None,
        generation_params: GenerationParams | None = None,
        rating_version: str | None = None,
    ) -> Experiment:
        """Creates a new experiment.

        Note: When block=True with generate=True, this method uses async streaming
        internally and falls back to the async implementation.

        Args:
            name (str): The name of the experiment.
            prompt_template (PromptTemplate | None): Optional prompt template to use for the experiment. If omitted, the collection must contain a Conversation or Raw Input column.
            collection (TemplateVariablesCollection): The collection of template variables to use for the experiment.
            llm_config (LLMConfig | None): Optional LLMConfig to use for the experiment. Uses platform default if not specified.
            criterion_set (CriterionSet | None): Optional criterion set to evaluate against. If omitted, falls back to the prompt template's linked criterion set (if template is provided).
            description (str): Optional description for the experiment.
            generate (bool): Whether to generate responses and ratings immediately. Defaults to False.
            rating_mode (RatingMode): The rating mode to use if generating responses (Only used if generate=True). Defaults to RatingMode.DETAILED.
            n_epochs (int): Number of times to run the experiment for each input. Defaults to 1.
            block (bool): Whether to block until the experiment is executed, only relevant if generate=True. Defaults to False.
            timeout (float | None): The timeout for the experiment execution, only relevant if generate=True and block=True. Defaults to None.
            generation_params (GenerationParams | None): Optional sampling parameters to override LLMConfig defaults for this experiment. Defaults to None (uses LLMConfig defaults).
            rating_version (str | None): Version of core rating to use. If not provided, uses project's default_rating_version. Use "mock" in test environments to avoid actual LLM calls for ratings.

        Returns:
            Experiment: The newly created experiment object. If generate=True,
            responses and ratings will be generated. The returned experiment object will
            then include a generation task ID that can be used to check the status of the
            generation.

        Raises:
            httpx.HTTPStatusError: If the experiment with the same name already exists

        """
        if not generate and block:
            logger.warning(
                "The block=True parameter has no effect when generate=False. The experiment will be created but no response/rating generation will occur. Set generate=True to enable blocking behavior."
            )

        response = self._post(
            "experiments",
            json=CreateExperimentRequest(
                name=name,
                description=description,
                prompt_template_id=prompt_template.id if prompt_template else None,
                collection_id=collection.id,
                llm_config_id=llm_config.id if llm_config else None,
                criterion_set_id=criterion_set.id if criterion_set else None,
                generate=generate,
                rating_mode=rating_mode,
                n_epochs=n_epochs,
                generation_params=generation_params,
                rating_version=rating_version,
            ).model_dump(),
        )

        experiment = Experiment.model_validate(response.json())
        experiment._client = self._client

        # If blocking is requested, poll until generation completes
        if generate and block and experiment.generation_task_id:
            import time

            start_time = time.time()
            polling_interval = 3.0

            while timeout is None or time.time() - start_time < timeout:
                status_response = self._get(
                    f"experiments/{experiment.id}/generation/{experiment.generation_task_id}"
                )
                status_data = status_response.json()

                if status_data.get("status") == "FAILURE":
                    raise RuntimeError(f"Generation failed: {status_data.get('error_msg')}")

                if status_data.get("status") == "SUCCESS":
                    # Fetch the full experiment with responses
                    return self.get(id=experiment.id)

                time.sleep(polling_interval)

            raise TimeoutError(f"Experiment generation timed out after {timeout} seconds")

        return experiment

    def get_or_create(
        self,
        name: str,
        prompt_template: PromptTemplate | None,
        collection: TemplateVariablesCollection,
        llm_config: LLMConfig | None = None,
        criterion_set: CriterionSet | None = None,
        description: str = "",
        generate: bool = False,
        rating_mode: RatingMode = RatingMode.DETAILED,
        n_epochs: int = 1,
        block: bool = False,
        timeout: float | None = None,
        generation_params: GenerationParams | None = None,
        rating_version: str | None = None,
    ) -> tuple[Experiment, bool]:
        """Gets an existing experiment by name or creates a new one if it doesn't exist.

        The existence of an experiment is determined solely by its name. If an experiment with the given name exists,
        it will be returned regardless of its other properties. If no experiment exists with that name, a new one
        will be created with the provided parameters.

        Args:
            name (str): The name of the experiment to get or create.
            prompt_template (PromptTemplate | None): Optional prompt template to use if creating a new experiment. If omitted, the collection must contain a Conversation or Raw Input column.
            collection (TemplateVariablesCollection): The collection of template variables to use if creating a new experiment.
            llm_config (LLMConfig | None): Optional LLMConfig to use if creating a new experiment.
            criterion_set (CriterionSet | None): Optional criterion set to use if creating a new experiment. If omitted, falls back to the prompt template's linked criterion set (if template is provided).
            description (str): Optional description if creating a new experiment.
            generate (bool): Whether to generate responses and ratings immediately. Defaults to False.
            rating_mode (RatingMode): The rating mode to use if generating responses. Defaults to RatingMode.DETAILED.
            n_epochs (int): Number of times to run the experiment for each input. Defaults to 1.
            block (bool): Whether to block until the experiment is executed when creating a new experiment, only relevant if generate=True. Defaults to False.
            timeout (float | None): The timeout for the experiment execution when creating a new experiment, only relevant if generate=True and block=True. Defaults to None.
            generation_params (GenerationParams | None): Optional sampling parameters to override LLMConfig defaults for this experiment. Defaults to None (uses LLMConfig defaults).
            rating_version (str | None): Version of core rating to use. If not provided, uses project's default_rating_version. Use "mock" in test environments to avoid actual LLM calls for ratings.

        Returns:
            tuple[Experiment | ExperimentGenerationStatus, bool]: A tuple containing:
                - The experiment object (either existing or newly created)
                - Boolean indicating if a new experiment was created (True) or existing one returned (False)

        """
        from elluminate.exceptions import ConflictError

        # Create a dict of the requested parameters (excluding None values)
        requested_dict = {
            k: v
            for k, v in {
                "name": name,
                "prompt_template": prompt_template,
                "collection": collection,
                "llm_config": llm_config,
                "criterion_set": criterion_set,
                "description": description,
                "generate": generate,
                "rating_mode": rating_mode,
                "n_epochs": n_epochs,
                "generation_params": generation_params,
                "rating_version": rating_version,
            }.items()
            if v is not None
        }

        try:
            experiment = self.create(
                name=name,
                prompt_template=prompt_template,
                collection=collection,
                llm_config=llm_config,
                criterion_set=criterion_set,
                description=description,
                generate=generate,
                rating_mode=rating_mode,
                n_epochs=n_epochs,
                block=block,
                timeout=timeout,
                generation_params=generation_params,
                rating_version=rating_version,
            )
            return experiment, True
        except ConflictError:
            # Try to get existing experiment (skip fetching responses for efficiency)
            existing_config = self.get(name=name, fetch_responses=False)
            existing_dict = existing_config.model_dump()

            differences = []
            for k, v in requested_dict.items():
                # Normalize both sides for comparison (BaseModel -> dict)
                v_normalized = v.model_dump() if isinstance(v, BaseModel) else v
                existing_v = existing_dict.get(k)
                existing_normalized = existing_v.model_dump() if isinstance(existing_v, BaseModel) else existing_v

                if k != "name" and v_normalized != existing_normalized:
                    differences.append(k)

            if differences:
                logger.warning(
                    f"Experiment with name '{name}' already exists with different values for: {', '.join(differences)}. Returning existing experiment."
                )

            return existing_config, False

    def delete(self, experiment: Experiment) -> None:
        """Deletes an experiment.

        Args:
            experiment (Experiment): The experiment to delete.

        Raises:
            httpx.HTTPStatusError: If the experiment doesn't exist or belongs to a different project.

        """
        self._delete(f"experiments/{experiment.id}")

    def run(
        self,
        experiment: Experiment,
        rating_mode: RatingMode = RatingMode.DETAILED,
        n_epochs: int = 1,
        block: bool = True,
        timeout: float | None = None,
        generation_params: GenerationParams | None = None,
    ) -> Experiment:
        """Run an existing unrun experiment to generate responses and ratings.

        This method triggers generation for an experiment that was created without
        running it (i.e., using client.create_experiment() without generate=True).

        Args:
            experiment: The experiment to run.
            rating_mode: The rating mode to use (FAST or DETAILED). Defaults to DETAILED.
            n_epochs: Number of times to run for each input. Defaults to 1.
            block: Whether to block until generation completes. Defaults to True.
            timeout: Optional timeout in seconds. Only relevant if block=True.
            generation_params: Optional sampling parameters to override LLMConfig defaults.

        Returns:
            The experiment with generation_task_id set. If block=True, the experiment
            will include the generated responses and ratings.

        Raises:
            httpx.HTTPStatusError: If the experiment has already been run or doesn't exist.

        """
        # Build request payload
        payload = {
            "rating_mode": rating_mode.value if isinstance(rating_mode, RatingMode) else rating_mode,
            "n_epochs": n_epochs,
        }
        if generation_params is not None:
            payload["generation_params"] = generation_params.model_dump()

        response = self._post(f"experiments/{experiment.id}/run", json=payload)
        updated_experiment = Experiment.model_validate(response.json())
        updated_experiment._client = self._client

        # If blocking is requested, poll until generation completes
        if block and updated_experiment.generation_task_id:
            import time

            start_time = time.time()
            polling_interval = 3.0

            while timeout is None or time.time() - start_time < timeout:
                status_response = self._get(
                    f"experiments/{updated_experiment.id}/generation/{updated_experiment.generation_task_id}"
                )
                status_data = status_response.json()

                if status_data.get("status") == "FAILURE":
                    raise RuntimeError(f"Generation failed: {status_data.get('error_msg')}")

                if status_data.get("status") == "SUCCESS":
                    # Fetch the full experiment with responses
                    return self.get(id=updated_experiment.id)

                time.sleep(polling_interval)

            raise TimeoutError(f"Experiment generation timed out after {timeout} seconds")

        return updated_experiment

    # ===== Async Methods =====

    async def aget(
        self,
        *,
        name: str | None = None,
        id: int | None = None,
        fetch_responses: bool = True,
    ) -> Experiment:
        """Get an experiment by name or id (async).

        Args:
            name: The name of the experiment to get.
            id: The id of the experiment to get.
            fetch_responses: Whether to fetch responses for the experiment.
                Defaults to True for backward compatibility. Set to False to save
                API calls when responses aren't needed.

        Returns:
            Experiment: The experiment object.

        Raises:
            ValueError: If neither or both name and id are provided, or if not found.

        """
        if name is not None and id is not None:
            raise ValueError("Provide either 'name' or 'id', not both")
        if name is None and id is None:
            raise ValueError("Either 'name' or 'id' must be provided")

        if id is not None:
            if fetch_responses:
                response = await self._aget(f"experiments/{id}?include_responses=true")
            else:
                response = await self._aget(f"experiments/{id}")

            experiment = Experiment.model_validate(response.json())
            experiment._client = self._client
            return experiment

        # Get by name
        params = {"experiment_name": name}
        response = await self._aget("experiments", params=params)
        data = response.json()
        items = data.get("items", [])

        if not items:
            raise ValueError(f"No experiment found with name '{name}'")

        experiment = Experiment.model_validate(items[0])
        experiment._client = self._client

        if fetch_responses and experiment.responses_generated:
            # Refetch by id to get responses
            return await self.aget(id=experiment.id, fetch_responses=True)

        return experiment

    async def alist(
        self,
        prompt_template: PromptTemplate | None = None,
        collection: TemplateVariablesCollection | None = None,
        llm_config: LLMConfig | None = None,
    ) -> list[Experiment]:
        """Get a list of experiments sorted by creation date (async).

        Args:
            prompt_template: The prompt template to filter by.
            collection: The collection to filter by.
            llm_config: The LLM config to filter by.

        Returns:
            List of experiments.

        """
        return await self._paginate(
            "experiments",
            model=Experiment,
            params=ExperimentFilter(
                prompt_template_id=prompt_template.id if prompt_template else None,
                collection_id=collection.id if collection else None,
                llm_config_id=llm_config.id if llm_config else None,
            ).model_dump(exclude_none=True),
            resource_name="Experiments",
        )

    async def acreate(
        self,
        name: str,
        prompt_template: PromptTemplate | None,
        collection: TemplateVariablesCollection,
        llm_config: LLMConfig | None = None,
        criterion_set: CriterionSet | None = None,
        description: str = "",
        rating_mode: RatingMode = RatingMode.DETAILED,
        n_epochs: int = 1,
        generate: bool = False,
        block: bool = False,
        timeout: float | None = None,
        generation_params: GenerationParams | None = None,
        rating_version: str | None = None,
    ) -> Experiment:
        """Create a new experiment (async)."""
        from elluminate.schemas.experiments import CreateExperimentRequest

        if not generate and block:
            logger.warning(
                "The block=True parameter has no effect when generate=False. The experiment will be created but no response/rating generation will occur. Set generate=True to enable blocking behavior."
            )

        response = await self._apost(
            "experiments",
            json=CreateExperimentRequest(
                name=name,
                description=description,
                prompt_template_id=prompt_template.id if prompt_template else None,
                collection_id=collection.id,
                llm_config_id=llm_config.id if llm_config else None,
                criterion_set_id=criterion_set.id if criterion_set else None,
                generate=generate,
                rating_mode=rating_mode,
                n_epochs=n_epochs,
                generation_params=generation_params,
                rating_version=rating_version,
            ).model_dump(),
        )
        experiment = Experiment.model_validate(response.json())
        experiment._client = self._client

        if generate and block and experiment.generation_task_id:
            import asyncio
            import time

            start_time = time.time()
            polling_interval = 3.0

            while timeout is None or time.time() - start_time < timeout:
                status_response = await self._aget(
                    f"experiments/{experiment.id}/generation/{experiment.generation_task_id}"
                )
                status_data = status_response.json()

                if status_data.get("status") == "FAILURE":
                    raise RuntimeError(f"Generation failed: {status_data.get('error_msg')}")

                if status_data.get("status") == "SUCCESS":
                    return await self.aget(id=experiment.id)

                await asyncio.sleep(polling_interval)

            raise TimeoutError(f"Experiment generation timed out after {timeout} seconds")

        return experiment

    async def aget_or_create(
        self,
        name: str,
        prompt_template: PromptTemplate | None,
        collection: TemplateVariablesCollection,
        llm_config: LLMConfig | None = None,
        criterion_set: CriterionSet | None = None,
        description: str = "",
        rating_mode: RatingMode = RatingMode.DETAILED,
        n_epochs: int = 1,
        generate: bool = False,
        block: bool = False,
        timeout: float | None = None,
        generation_params: GenerationParams | None = None,
        rating_version: str | None = None,
    ) -> tuple[Experiment, bool]:
        """Get or create an experiment (async)."""
        from elluminate.exceptions import ConflictError

        try:
            return await self.acreate(
                name=name,
                prompt_template=prompt_template,
                collection=collection,
                llm_config=llm_config,
                criterion_set=criterion_set,
                description=description,
                rating_mode=rating_mode,
                n_epochs=n_epochs,
                generate=generate,
                block=block,
                timeout=timeout,
                generation_params=generation_params,
                rating_version=rating_version,
            ), True
        except ConflictError:
            existing_experiment = await self.aget(name=name)
            if description and existing_experiment.description != description:
                logger.warning(
                    f"Experiment '{name}' already exists with different description. Returning existing experiment."
                )
            return existing_experiment, False

    async def adelete(self, experiment: Experiment) -> None:
        """Delete an experiment (async)."""
        await self._adelete(f"experiments/{experiment.id}")

    async def arun(
        self,
        experiment: Experiment,
        rating_mode: RatingMode = RatingMode.DETAILED,
        n_epochs: int = 1,
        block: bool = True,
        timeout: float | None = None,
        generation_params: GenerationParams | None = None,
    ) -> Experiment:
        """Run an existing unrun experiment to generate responses and ratings (async)."""
        import asyncio
        import time

        payload = {
            "rating_mode": rating_mode.value if isinstance(rating_mode, RatingMode) else rating_mode,
            "n_epochs": n_epochs,
        }
        if generation_params is not None:
            payload["generation_params"] = generation_params.model_dump()

        response = await self._apost(f"experiments/{experiment.id}/run", json=payload)
        updated_experiment = Experiment.model_validate(response.json())
        updated_experiment._client = self._client

        if block and updated_experiment.generation_task_id:
            start_time = time.time()
            polling_interval = 3.0

            while timeout is None or time.time() - start_time < timeout:
                status_response = await self._aget(
                    f"experiments/{updated_experiment.id}/generation/{updated_experiment.generation_task_id}"
                )
                status_data = status_response.json()

                if status_data.get("status") == "FAILURE":
                    raise RuntimeError(f"Generation failed: {status_data.get('error_msg')}")

                if status_data.get("status") == "SUCCESS":
                    return await self.aget(id=updated_experiment.id)

                await asyncio.sleep(polling_interval)

            raise TimeoutError(f"Experiment generation timed out after {timeout} seconds")

        return updated_experiment
