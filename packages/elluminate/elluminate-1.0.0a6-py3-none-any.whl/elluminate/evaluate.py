"""Top-level evaluate() function for one-call experiment execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from elluminate.schemas import RatingMode

if TYPE_CHECKING:
    from elluminate.client import Client
    from elluminate.schemas import (
        CriterionSet,
        Experiment,
        LLMConfig,
        PromptTemplate,
        TemplateVariablesCollection,
    )

# Lazy singleton for auto-created client.
# Note: This singleton is shared across all evaluate() calls. Environment variable
# changes (ELLUMINATE_API_KEY, ELLUMINATE_BASE_URL) after the first evaluate() call
# will NOT be picked up. Use reset_default_client() to force re-initialization,
# or pass an explicit client parameter.
_default_client: Client | None = None


def _get_default_client() -> Client:
    """Get or create the default client from environment variables."""
    global _default_client
    if _default_client is None:
        from elluminate.client import Client

        _default_client = Client()
    return _default_client


def reset_default_client() -> None:
    """Reset the default client singleton.

    Call this to force re-initialization of the auto-created client on the
    next evaluate() call. Useful for:
    - Test cleanup between test cases
    - Picking up environment variable changes
    - Switching projects in multi-project scenarios

    Example:
        from elluminate.evaluate import reset_default_client

        # In test teardown
        reset_default_client()

    """
    global _default_client
    _default_client = None


def evaluate(
    prompt_template: PromptTemplate | str,
    collection: TemplateVariablesCollection | str,
    criterion_set: CriterionSet | str | None = None,
    llm_config: LLMConfig | str | None = None,
    *,
    name: str | None = None,
    rating_mode: RatingMode = RatingMode.DETAILED,
    client: Client | None = None,
) -> Experiment:
    """Run an evaluation experiment in one call.

    This is a convenience function for running experiments without explicit
    client management. It auto-creates a client from environment variables
    or uses an explicitly provided client.

    Note:
        The auto-created client is cached as a module-level singleton. This means:
        - All evaluate() calls share the same client (efficient connection reuse)
        - Environment variable changes after the first call are NOT picked up
        - Use reset_default_client() to force re-initialization if needed
        - Pass an explicit `client` parameter to avoid singleton behavior

    Args:
        prompt_template: PromptTemplate object or name to look up.
        collection: Collection object or name to look up.
        criterion_set: CriterionSet object or name. If None, uses template's
            linked criterion set. Raises ValueError if neither is available.
        llm_config: LLMConfig object or name. If None, uses platform default.
        name: Optional experiment name. Auto-generated if not provided.
        rating_mode: The rating mode (FAST or DETAILED). FAST is quicker but
            without reasoning. DETAILED provides reasoning. Defaults to DETAILED.
        client: Optional client override. If None, uses auto-created client.

    Returns:
        The completed Experiment with results.

    Raises:
        ValueError: If no criterion set is provided and template has no linked set.

    Example:
        from elluminate import evaluate

        # Simple - just works if ELLUMINATE_API_KEY is set
        result = evaluate(
            prompt_template="My Template",
            collection="Test Cases",
            criterion_set="Quality Checks",
        )

        # With explicit client
        client = Client(timeout=120)
        result = evaluate(
            prompt_template="My Template",
            collection="Test Cases",
            criterion_set="Quality Checks",
            client=client,
        )

    """
    # Get client (auto-create or use provided)
    client = client or _get_default_client()

    # Resolve prompt_template
    if isinstance(prompt_template, str):
        prompt_template = client.get_prompt_template(name=prompt_template)

    # Resolve collection
    if isinstance(collection, str):
        collection = client.get_collection(name=collection)

    # Resolve criterion_set
    resolved_criterion_set: CriterionSet | None = None
    if criterion_set is not None:
        if isinstance(criterion_set, str):
            resolved_criterion_set = client.get_criterion_set(name=criterion_set)
        else:
            resolved_criterion_set = criterion_set
    elif hasattr(prompt_template, "criterion_set_id") and prompt_template.criterion_set_id is not None:
        # Use template's linked criterion set
        resolved_criterion_set = client.get_criterion_set(id=prompt_template.criterion_set_id)
    else:
        raise ValueError(
            "No criterion set provided and template has no linked criterion set. "
            "evaluate() requires criteria for evaluation."
        )

    # Resolve llm_config
    resolved_llm_config: LLMConfig | None = None
    if llm_config is not None:
        if isinstance(llm_config, str):
            resolved_llm_config = client.get_llm_config(name=llm_config)
        else:
            resolved_llm_config = llm_config

    # Generate experiment name if not provided
    if name is None:
        import time

        name = f"evaluate-{int(time.time())}"

    # Run the experiment
    return client.run_experiment(
        name=name,
        prompt_template=prompt_template,
        collection=collection,
        criterion_set=resolved_criterion_set,
        llm_config=resolved_llm_config,
        rating_mode=rating_mode,
    )
