from datetime import datetime
from typing import TYPE_CHECKING, Dict, Iterator, List

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, ConfigDict, PrivateAttr

from elluminate.exceptions import ModelNotBoundError
from elluminate.schemas.generation_metadata import GenerationMetadata
from elluminate.schemas.generation_params import GenerationParams
from elluminate.schemas.llm_config import LLMConfig
from elluminate.schemas.prompt_template import PromptTemplate
from elluminate.schemas.rating import Rating, RatingMode
from elluminate.schemas.response import PromptResponse
from elluminate.schemas.template_variables import TemplateVariables
from elluminate.schemas.template_variables_collection import TemplateVariablesCollection

if TYPE_CHECKING:
    from elluminate.async_client import AsyncClient
    from elluminate.client import Client
    from elluminate.schemas.criterion_set import CriterionSet

_EXPERIMENT_HINT = (
    "This experiment is not connected to a client. "
    "To use model methods, obtain experiments through: "
    "client.get_experiment(), client.create_experiment(), or client.run_experiment()."
)


class MeanRating(BaseModel):
    """Schema for mean rating scores."""

    yes: float
    no: float


class ExperimentResults(BaseModel):
    """Schema for experiment results."""

    mean_all_ratings: MeanRating
    mean_rating_by_criterion_id: Dict[int, MeanRating]
    mean_duration_seconds: float
    mean_input_tokens: float
    mean_output_tokens: float
    input_tokens_per_response: List[int]
    output_tokens_per_response: List[int]
    duration_seconds_per_response: List[float]
    num_rated_responses: int
    num_failed_responses: int

    def print_summary(self, criterion_names: Dict[int, str] | None = None) -> None:
        """Print a human-readable summary of the experiment results.

        Args:
            criterion_names: Optional mapping of criterion IDs to their descriptions

        """
        print("\n===== Experiment Results Summary =====")
        print(f"Number of rated responses: {self.num_rated_responses}")
        print(f"Number of failed responses: {self.num_failed_responses}")
        print(f"\nOverall Success Rate: {self.mean_all_ratings.yes:.2%}")

        print("\nResponse Generation Metrics:")
        print(f"  Mean Duration: {self.mean_duration_seconds:.2f} seconds")
        print(f"  Mean Input Tokens: {self.mean_input_tokens:.1f}")
        print(f"  Mean Output Tokens: {self.mean_output_tokens:.1f}")

        if self.mean_rating_by_criterion_id:
            print("\nSuccess Rate by Criterion:")
            for criterion_id, rating in self.mean_rating_by_criterion_id.items():
                criterion_name = (
                    criterion_names.get(criterion_id, f"Criterion {criterion_id}")
                    if criterion_names
                    else f"Criterion {criterion_id}"
                )
                print(f"  {criterion_name}: {rating.yes:.2%}")

        print("=====================================")

    def get_criterion_summary(self, criterion_id: int) -> str:
        """Get a summary for a specific criterion.

        Args:
            criterion_id: The ID of the criterion to summarize

        Returns:
            A formatted string with the criterion's success rate

        """
        rating = self.mean_rating_by_criterion_id.get(criterion_id)
        if not rating:
            return f"No data for Criterion {criterion_id}"

        return f"Success rate: {rating.yes:.2%} (Yes: {rating.yes:.2%}, No: {rating.no:.2%})"


class Experiment(BaseModel):
    """Schema for an experiment with rich model methods.

    This class represents an experiment returned from the Elluminate API.
    Experiments have rich methods like run(), clone(), and fetch_responses()
    that require a connection to the API client.

    Important:
        Do NOT instantiate this class directly. Rich model methods will not work
        on manually constructed instances because they lack the internal client
        connection. Always obtain experiments through the client:

        - client.get_experiment(name="...")
        - client.create_experiment(...)
        - client.run_experiment(...)
        - client.list_experiments()

    Example:
        # ✓ Correct - obtained through client
        experiment = client.get_experiment(name="My Experiment")
        experiment.run()  # Works because it has client connection

        # ✗ Wrong - manually constructed
        experiment = Experiment(id=1, name="Test", ...)
        experiment.run()  # Raises ModelNotBoundError

    Attributes:
        id: Unique identifier for the experiment
        name: Name of the experiment
        description: Optional description
        prompt_template: The prompt template used (if any)
        collection: Collection of test inputs
        criterion_set: Set of evaluation criteria
        llm_config: LLM configuration used
        rated_responses: List of responses with ratings
        created_at: When the experiment was created
        updated_at: When the experiment was last updated
        generation_task_id: Celery task ID if generation is running
        results: Aggregated experiment results (if available)
        logs: Execution logs (if available)

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    name: str
    description: str | None = None
    prompt_template: PromptTemplate | None = None
    collection: TemplateVariablesCollection
    criterion_set: "CriterionSet"
    llm_config: LLMConfig | None
    rating_version: str | None = None
    rated_responses: List[PromptResponse] = []
    created_at: datetime
    updated_at: datetime
    generation_task_id: str | None = None
    generation_params: GenerationParams | None = None
    results: ExperimentResults | None = None
    logs: str | None = None
    _client: "Client | AsyncClient | None" = PrivateAttr(default=None)

    def __eq__(self, other: object) -> bool:
        """Compare experiments by data fields only, ignoring _client."""
        if not isinstance(other, Experiment):
            return NotImplemented
        return self.model_dump() == other.model_dump()

    def __hash__(self) -> int:
        """Make Experiment hashable based on id."""
        return hash(self.id)

    def print_results_summary(self) -> None:
        """Print a summary of the experiment results if available.

        If results are not available, prints a message indicating why.
        """
        if not self.results:
            if not self.rated_responses:
                print("\nNo results available - experiment has no rated responses.")
            else:
                print(
                    f"\nNo aggregated results available, but experiment has {len(self.rated_responses)} rated responses."
                )
                print("Consider fetching the experiment again to get the latest results.")
            return

        # Build a dictionary of criterion names from the rated responses
        criterion_names = {
            rating.criterion.id: rating.criterion.criterion_str for rating in self.rated_responses[0].ratings
        }

        # Print the summary with criterion names
        print(f"\nResults for experiment '{self.name}':")
        self.results.print_summary(criterion_names)

    def responses(self) -> Iterator[PromptResponse]:
        """Iterate over the responses in this experiment.

        Returns:
            Iterator over PromptResponse objects.

        Example:
            for response in experiment.responses():
                print(response.response_str)

        """
        return iter(self.rated_responses)

    def fetch_responses(self) -> "Experiment":
        """Fetch responses for this experiment from the server.

        Use this method when you have an experiment from list_experiments()
        that doesn't include responses. After calling this method, you can
        access responses via experiment.responses() or experiment.rated_responses.

        Returns:
            This experiment with rated_responses populated.

        Raises:
            ModelNotBoundError: If no client is associated with this experiment.

        Example:
            # Experiments from list_experiments() don't include responses
            experiments = client.list_experiments()
            for exp in experiments:
                exp.fetch_responses()  # Now exp.rated_responses is populated
                for response in exp.responses():
                    print(response.response_str)

        """
        if self._client is None:
            raise ModelNotBoundError("Experiment", _EXPERIMENT_HINT)

        self.rated_responses = self._client._responses.list(experiment=self)
        return self

    @property
    def result(self) -> ExperimentResults | None:
        """Access the experiment results.

        Returns:
            ExperimentResults with aggregated statistics, or None if not available.

        Example:
            if experiment.result:
                print(f"Success rate: {experiment.result.mean_all_ratings.yes:.2%}")

        """
        return self.results

    def run(
        self,
        rating_mode: RatingMode = RatingMode.DETAILED,
        n_epochs: int = 1,
        timeout: float | None = None,
        generation_params: GenerationParams | None = None,
    ) -> "Experiment":
        """Run this experiment to generate responses and ratings.

        This method can only be called on experiments that haven't been run yet.
        For experiments that have already been run, use clone() to create a new
        experiment and run that instead.

        Args:
            rating_mode: The rating mode (FAST or DETAILED). Defaults to DETAILED.
            n_epochs: Number of times to run for each input. Defaults to 1.
            timeout: Optional timeout in seconds for the experiment execution.
            generation_params: Optional sampling parameters to override LLMConfig defaults.

        Returns:
            This experiment with results populated.

        Raises:
            ModelNotBoundError: If no client is associated with this experiment.

        Example:
            # Create and then run
            experiment = client.create_experiment(name="Test", ...)
            experiment.run()

            # Or with options
            experiment.run(n_epochs=3, rating_mode=RatingMode.FAST)

            # With custom generation params
            experiment.run(generation_params=GenerationParams(temperature=0.7))

        """
        if self._client is None:
            raise ModelNotBoundError("Experiment", _EXPERIMENT_HINT)

        # Use provided generation_params, or fall back to experiment's stored params
        params_to_use = generation_params if generation_params is not None else self.generation_params

        # Call the new /run endpoint
        result = self._client._experiments.run(
            experiment=self,
            rating_mode=rating_mode,
            n_epochs=n_epochs,
            block=True,
            timeout=timeout,
            generation_params=params_to_use,
        )

        # Update this experiment object with the results
        self.rated_responses = result.rated_responses
        self.results = result.results
        self.generation_task_id = result.generation_task_id
        self.updated_at = result.updated_at

        return self

    def clone(
        self,
        name: str,
        llm_config: LLMConfig | None = None,
        criterion_set: "CriterionSet | None" = None,
        description: str | None = None,
    ) -> "Experiment":
        """Create a copy of this experiment with a new name.

        The cloned experiment will have the same configuration but no results.
        You can optionally override specific settings.

        Args:
            name: The name for the new experiment (required).
            llm_config: Optional different LLM config. Uses original if not specified.
            criterion_set: Optional different criterion set. Uses original if not specified.
            description: Optional different description. Uses original if not specified.

        Returns:
            A new unrun experiment with the specified configuration.

        Raises:
            ModelNotBoundError: If no client is associated with this experiment.

        Example:
            # Simple clone
            new_exp = experiment.clone(name="Experiment v2")

            # Clone with different LLM
            new_exp = experiment.clone(
                name="Experiment - GPT4",
                llm_config=gpt4_config,
            )

            # Clone and run
            new_exp = experiment.clone(name="Experiment v2").run()

        """
        if self._client is None:
            raise ModelNotBoundError("Experiment", _EXPERIMENT_HINT)

        return self._client.create_experiment(
            name=name,
            prompt_template=self.prompt_template,
            collection=self.collection,
            llm_config=llm_config if llm_config is not None else self.llm_config,
            criterion_set=criterion_set if criterion_set is not None else self.criterion_set,
            description=description if description is not None else (self.description or ""),
        )

    # ===== Async Methods =====

    async def afetch_responses(self) -> "Experiment":
        """Fetch responses for this experiment from the server (async).

        Use this method when you have an experiment from list_experiments()
        that doesn't include responses. After calling this method, you can
        access responses via experiment.responses() or experiment.rated_responses.

        Returns:
            This experiment with rated_responses populated.

        Raises:
            ModelNotBoundError: If no client is associated with this experiment.

        Example:
            # Experiments from list_experiments() don't include responses
            experiments = await client.list_experiments()
            for exp in experiments:
                await exp.afetch_responses()  # Now exp.rated_responses is populated
                for response in exp.responses():
                    print(response.response_str)

        """
        if self._client is None:
            raise ModelNotBoundError("Experiment", _EXPERIMENT_HINT)

        self.rated_responses = await self._client._responses.alist(experiment=self)
        return self

    async def arun(
        self,
        rating_mode: RatingMode = RatingMode.DETAILED,
        n_epochs: int = 1,
        timeout: float | None = None,
        generation_params: GenerationParams | None = None,
    ) -> "Experiment":
        """Run this experiment to generate responses and ratings (async).

        This method can only be called on experiments that haven't been run yet.
        For experiments that have already been run, use clone() to create a new
        experiment and run that instead.

        Args:
            rating_mode: The rating mode (FAST or DETAILED). Defaults to DETAILED.
            n_epochs: Number of times to run for each input. Defaults to 1.
            timeout: Optional timeout in seconds for the experiment execution.
            generation_params: Optional sampling parameters to override LLMConfig defaults.

        Returns:
            This experiment with results populated.

        Raises:
            ModelNotBoundError: If no client is associated with this experiment.

        Example:
            # Create and then run
            experiment = await client.create_experiment(name="Test", ...)
            await experiment.arun()

            # Or with options
            await experiment.arun(n_epochs=3, rating_mode=RatingMode.FAST)

            # With custom generation params
            await experiment.arun(generation_params=GenerationParams(temperature=0.7))

        """
        if self._client is None:
            raise ModelNotBoundError("Experiment", _EXPERIMENT_HINT)

        # Use provided generation_params, or fall back to experiment's stored params
        params_to_use = generation_params if generation_params is not None else self.generation_params

        # Call the new /run endpoint
        result = await self._client._experiments.arun(
            experiment=self,
            rating_mode=rating_mode,
            n_epochs=n_epochs,
            block=True,
            timeout=timeout,
            generation_params=params_to_use,
        )

        # Update this experiment object with the results
        self.rated_responses = result.rated_responses
        self.results = result.results
        self.generation_task_id = result.generation_task_id
        self.updated_at = result.updated_at

        return self

    async def aclone(
        self,
        name: str,
        llm_config: LLMConfig | None = None,
        criterion_set: "CriterionSet | None" = None,
        description: str | None = None,
    ) -> "Experiment":
        """Create a copy of this experiment with a new name (async).

        The cloned experiment will have the same configuration but no results.
        You can optionally override specific settings.

        Args:
            name: The name for the new experiment (required).
            llm_config: Optional different LLM config. Uses original if not specified.
            criterion_set: Optional different criterion set. Uses original if not specified.
            description: Optional different description. Uses original if not specified.

        Returns:
            A new unrun experiment with the specified configuration.

        Raises:
            ModelNotBoundError: If no client is associated with this experiment.

        Example:
            # Simple clone
            new_exp = await experiment.aclone(name="Experiment v2")

            # Clone with different LLM
            new_exp = await experiment.aclone(
                name="Experiment - GPT4",
                llm_config=gpt4_config,
            )

            # Clone and run
            new_exp = await (await experiment.aclone(name="Experiment v2")).arun()

        """
        if self._client is None:
            raise ModelNotBoundError("Experiment", _EXPERIMENT_HINT)

        return await self._client.create_experiment(
            name=name,
            prompt_template=self.prompt_template,
            collection=self.collection,
            llm_config=llm_config if llm_config is not None else self.llm_config,
            criterion_set=criterion_set if criterion_set is not None else self.criterion_set,
            description=description if description is not None else (self.description or ""),
        )

    def add_responses(
        self,
        responses: List[str | List[ChatCompletionMessageParam]],
        template_variables: List[TemplateVariables],
        epoch: int = 1,
        metadata: List[LLMConfig | GenerationMetadata | None] | None = None,
        timeout: float | None = None,
    ) -> List[PromptResponse]:
        """Add externally-generated responses to this experiment.

        Use this method when evaluating an external agent or LLM that is not
        controlled by elluminate. You generate the responses yourself, then
        upload them to the experiment for rating.

        Args:
            responses: List of response strings or message lists. Each response
                corresponds to one template variable.
            template_variables: List of TemplateVariables that the responses are for.
                Must have the same length as responses.
            epoch: The epoch number for these responses. Defaults to 1.
            metadata: Optional list of metadata (LLMConfig or GenerationMetadata)
                for each response. Useful for tracking which model generated each
                response and token usage.
            timeout: Optional timeout in seconds for the API request.

        Returns:
            List of newly created PromptResponse objects.

        Raises:
            ModelNotBoundError: If no client is associated with this experiment.
            ValueError: If responses and template_variables have different lengths.

        Example:
            # Create experiment without auto-generation
            experiment = client.create_experiment(
                name="External Agent Eval",
                prompt_template=template,
                collection=collection,
                criterion_set=criterion_set,
            )

            # Generate responses with your external agent
            responses = []
            for tv in collection.variables:
                response = my_agent.chat(tv.input_values["query"])
                responses.append(response)

            # Upload responses to elluminate
            prompt_responses = experiment.add_responses(
                responses=responses,
                template_variables=list(collection.variables),
            )

            # Rate the responses
            client._ratings.rate_many(prompt_responses=prompt_responses)

        """
        if self._client is None:
            raise ModelNotBoundError("Experiment", _EXPERIMENT_HINT)

        added = self._client._responses.add_many(
            responses=responses,
            template_variables=template_variables,
            experiment=self,
            epoch=epoch,
            metadata=metadata,
            timeout=timeout,
        )

        # Update local state
        self.rated_responses.extend(added)

        return added

    async def aadd_responses(
        self,
        responses: List[str | List[ChatCompletionMessageParam]],
        template_variables: List[TemplateVariables],
        epoch: int = 1,
        metadata: List[LLMConfig | GenerationMetadata | None] | None = None,
        timeout: float | None = None,
    ) -> List[PromptResponse]:
        """Add externally-generated responses to this experiment (async).

        Use this method when evaluating an external agent or LLM that is not
        controlled by elluminate. You generate the responses yourself, then
        upload them to the experiment for rating.

        Args:
            responses: List of response strings or message lists. Each response
                corresponds to one template variable.
            template_variables: List of TemplateVariables that the responses are for.
                Must have the same length as responses.
            epoch: The epoch number for these responses. Defaults to 1.
            metadata: Optional list of metadata (LLMConfig or GenerationMetadata)
                for each response. Useful for tracking which model generated each
                response and token usage.
            timeout: Optional timeout in seconds for the API request.

        Returns:
            List of newly created PromptResponse objects.

        Raises:
            ModelNotBoundError: If no client is associated with this experiment.
            ValueError: If responses and template_variables have different lengths.

        Example:
            # Create experiment without auto-generation
            experiment = await client.create_experiment(
                name="External Agent Eval",
                prompt_template=template,
                collection=collection,
                criterion_set=criterion_set,
            )

            # Generate responses with your external agent
            responses = []
            for tv in collection.variables:
                response = await my_agent.chat(tv.input_values["query"])
                responses.append(response)

            # Upload responses to elluminate
            prompt_responses = await experiment.aadd_responses(
                responses=responses,
                template_variables=list(collection.variables),
            )

            # Rate the responses
            await experiment.arate_responses(prompt_responses=prompt_responses)

        """
        if self._client is None:
            raise ModelNotBoundError("Experiment", _EXPERIMENT_HINT)

        added = await self._client._responses.aadd_many(
            responses=responses,
            template_variables=template_variables,
            experiment=self,
            epoch=epoch,
            metadata=metadata,
            timeout=timeout,
        )

        # Update local state
        self.rated_responses.extend(added)

        return added

    def rate_responses(
        self,
        prompt_responses: List[PromptResponse] | None = None,
        rating_mode: RatingMode = RatingMode.DETAILED,
        timeout: float | None = None,
    ) -> List[List[Rating]]:
        """Rate responses in this experiment against the criterion set.

        Use this method after add_responses() to evaluate externally-generated
        responses against the experiment's criteria.

        Args:
            prompt_responses: List of responses to rate. If None, rates all
                responses in self.rated_responses.
            rating_mode: The rating mode (FAST or DETAILED). DETAILED includes
                reasoning for each rating. Defaults to DETAILED.
            timeout: Optional timeout in seconds for the API request.

        Returns:
            List of rating lists, one list per response. Each inner list contains
            one Rating per criterion.

        Raises:
            ModelNotBoundError: If no client is associated with this experiment.
            ValueError: If no responses to rate (none provided and none in experiment).

        Example:
            # Full external agent workflow
            experiment = client.create_experiment(...)

            # Generate and upload responses
            prompt_responses = experiment.add_responses(
                responses=my_responses,
                template_variables=template_vars,
            )

            # Rate all uploaded responses
            ratings = experiment.rate_responses()

            # Or rate specific responses
            ratings = experiment.rate_responses(prompt_responses=prompt_responses[:5])

        """
        if self._client is None:
            raise ModelNotBoundError("Experiment", _EXPERIMENT_HINT)

        responses_to_rate = prompt_responses if prompt_responses is not None else self.rated_responses

        if not responses_to_rate:
            raise ValueError(
                "No responses to rate. Either provide prompt_responses or add responses first with add_responses()."
            )

        ratings = self._client._ratings.rate_many(
            prompt_responses=responses_to_rate,
            rating_mode=rating_mode,
            timeout=timeout,
        )

        # Update local state
        experiment = self._client.get_experiment(id=self.id)
        self.rated_responses = experiment.rated_responses
        self.results = experiment.results
        self.updated_at = experiment.updated_at

        return ratings

    async def arate_responses(
        self,
        prompt_responses: List[PromptResponse] | None = None,
        rating_mode: RatingMode = RatingMode.DETAILED,
        timeout: float | None = None,
    ) -> List[List[Rating]]:
        """Rate responses in this experiment against the criterion set (async).

        Use this method after add_responses() to evaluate externally-generated
        responses against the experiment's criteria.

        Args:
            prompt_responses: List of responses to rate. If None, rates all
                responses in self.rated_responses.
            rating_mode: The rating mode (FAST or DETAILED). DETAILED includes
                reasoning for each rating. Defaults to DETAILED.
            timeout: Optional timeout in seconds for the API request.

        Returns:
            List of rating lists, one list per response. Each inner list contains
            one Rating per criterion.

        Raises:
            ModelNotBoundError: If no client is associated with this experiment.
            ValueError: If no responses to rate (none provided and none in experiment).

        Example:
            # Full external agent workflow (async)
            experiment = await client.create_experiment(...)

            # Generate and upload responses
            prompt_responses = await experiment.aadd_responses(
                responses=my_responses,
                template_variables=template_vars,
            )

            # Rate all uploaded responses
            ratings = await experiment.arate_responses()

            # Or rate specific responses
            ratings = await experiment.arate_responses(prompt_responses=prompt_responses[:5])

        """
        if self._client is None:
            raise ModelNotBoundError("Experiment", _EXPERIMENT_HINT)

        responses_to_rate = prompt_responses if prompt_responses is not None else self.rated_responses

        if not responses_to_rate:
            raise ValueError(
                "No responses to rate. Either provide prompt_responses or add responses first with add_responses()."
            )

        ratings = await self._client._ratings.arate_many(
            prompt_responses=responses_to_rate,
            rating_mode=rating_mode,
            timeout=timeout,
        )

        # Update local state
        experiment = await self._client.get_experiment(id=self.id)
        self.rated_responses = experiment.rated_responses
        self.results = experiment.results
        self.updated_at = experiment.updated_at

        return ratings


class ExperimentGenerationStatus(BaseModel):
    """Schema for generation status response."""

    status: str
    error_msg: str | None = None
    completed_responses: int | None = None
    completed_ratings: int | None = None
    total_responses: int | None = None


class CreateExperimentRequest(BaseModel):
    """Request to create a new experiment."""

    name: str
    description: str
    prompt_template_id: int | None = None
    collection_id: int
    criterion_set_id: int | None = None
    llm_config_id: int | None = None
    generate: bool = False
    rating_mode: RatingMode = RatingMode.DETAILED
    n_epochs: int = 1
    generation_params: GenerationParams | None = None
    rating_version: str | None = None


class RunExperimentRequest(BaseModel):
    """Request to run an existing unrun experiment."""

    rating_mode: RatingMode = RatingMode.DETAILED
    n_epochs: int = 1
    generation_params: GenerationParams | None = None


class ExperimentFilter(BaseModel):
    """Filter for experiments."""

    experiment_name: str | None = None
    experiment_name_search: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    prompt_template_id: int | None = None
    prompt_template_name: str | None = None
    collection_id: int | None = None
    llm_config_id: int | None = None
    created_by_schedule_id: int | None = None
