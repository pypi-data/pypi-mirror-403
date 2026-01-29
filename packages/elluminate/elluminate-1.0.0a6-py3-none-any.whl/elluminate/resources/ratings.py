import time
from typing import List

from elluminate.resources.base import BaseResource
from elluminate.schemas import (
    BatchCreateRatingRequest,
    CreateRatingRequest,
    PromptResponse,
    PromptResponseFilter,
    Rating,
    RatingMode,
)


class RatingsResource(BaseResource):
    # Sync methods (use httpx.Client directly)

    def list(
        self,
        prompt_response: PromptResponse,
    ) -> List[Rating]:
        """Gets the ratings for a prompt response.

        Args:
            prompt_response (PromptResponse): The prompt response to get ratings for.

        Returns:
            list[Rating]: List of rating objects for the prompt response.

        Raises:
            httpx.HTTPStatusError: If the prompt response doesn't exist or belongs to a different project.

        """
        params = {
            "prompt_response_id": prompt_response.id,
        }
        return self._paginate_sync(
            path="ratings",
            model=Rating,
            params=params,
            resource_name="Ratings",
        )

    def rate(
        self,
        prompt_response: PromptResponse,
        rating_mode: RatingMode = RatingMode.DETAILED,
    ) -> List[Rating]:
        """Rates a response against its prompt template's criteria using an LLM.

        This method evaluates a prompt response against all applicable criteria associated with its prompt template.
        If template variables were used for the response, it will consider both general criteria and criteria specific
        to those variables.

        Args:
            prompt_response (PromptResponse): The response to rate.
            rating_mode (RatingMode): Mode for rating generation:
                - FAST: Quick evaluation without detailed reasoning
                - DETAILED: Includes explanations for each rating

        Returns:
            list[Rating]: List of rating objects, one per criterion.

        Raises:
            httpx.HTTPStatusError: If no criteria exist for the prompt template

        """
        response = self._post(
            "ratings",
            json=CreateRatingRequest(
                prompt_response_id=prompt_response.id,
                rating_mode=rating_mode,
            ).model_dump(),
        )
        return [Rating.model_validate(rating) for rating in response.json()]

    def rate_many(
        self,
        prompt_responses: List[PromptResponse],
        rating_mode: RatingMode = RatingMode.DETAILED,
        timeout: float | None = None,
        polling_interval: float = 3.0,
    ) -> List[List[Rating]]:
        """Batch version of rate.

        Args:
            prompt_responses (list[PromptResponse]): List of prompt responses to rate.
            rating_mode (RatingMode): Mode for rating generation (FAST or DETAILED). If DETAILED a reasoning is added to the rating.
            timeout (float): Timeout in seconds for API requests. Defaults to no timeout.
            polling_interval (float): Time between status checks in seconds. Defaults to 3.0.

        Returns:
            List[List[Rating]]: List of lists of rating objects, one per criterion for each prompt response.

        """
        # Initiate batch rating operation
        response = self._post(
            "ratings/batches",
            json=BatchCreateRatingRequest(
                prompt_response_ids=[pr.id for pr in prompt_responses],
                rating_mode=rating_mode,
            ).model_dump(),
        )
        task_id = response.json()

        # No task was started by the backend
        if task_id is None:
            return []

        # Poll for completion
        start_time = time.time()
        while timeout is None or time.time() - start_time < timeout:
            status_response = self._get(f"ratings/batches/{task_id}")
            status_data = status_response.json()

            if status_data.get("status") == "FAILURE":
                raise RuntimeError(f"Batch rating failed: {status_data.get('error_msg')}")

            if status_data.get("status") == "SUCCESS":
                # Fetch the responses which will have ratings
                responses = self._client._responses.list(
                    filters=PromptResponseFilter(response_ids=[pr.id for pr in prompt_responses])
                )
                return [r.ratings for r in responses]

            time.sleep(polling_interval)

        raise TimeoutError(f"Batch rating timed out after {timeout} seconds")

    # ===== Async Methods =====

    async def alist(
        self,
        prompt_response: PromptResponse,
    ) -> List[Rating]:
        """Gets the ratings for a prompt response (async)."""
        params = {
            "prompt_response_id": prompt_response.id,
        }
        return await self._paginate(
            path="ratings",
            model=Rating,
            params=params,
            resource_name="Ratings",
        )

    async def arate(
        self,
        prompt_response: PromptResponse,
        rating_mode: RatingMode = RatingMode.DETAILED,
    ) -> List[Rating]:
        """Rates a response against its prompt template's criteria using an LLM (async)."""
        response = await self._apost(
            "ratings",
            json=CreateRatingRequest(
                prompt_response_id=prompt_response.id,
                rating_mode=rating_mode,
            ).model_dump(),
        )
        return [Rating.model_validate(rating) for rating in response.json()]

    async def arate_many(
        self,
        prompt_responses: List[PromptResponse],
        rating_mode: RatingMode = RatingMode.DETAILED,
        timeout: float | None = None,
        polling_interval: float = 3.0,
    ) -> List[List[Rating]]:
        """Batch version of rate (async)."""
        import asyncio

        # Initiate batch rating operation
        response = await self._apost(
            "ratings/batches",
            json=BatchCreateRatingRequest(
                prompt_response_ids=[pr.id for pr in prompt_responses],
                rating_mode=rating_mode,
            ).model_dump(),
        )
        task_id = response.json()

        if task_id is None:
            return []

        # Poll for completion
        start_time = time.time()
        while timeout is None or time.time() - start_time < timeout:
            status_response = await self._aget(f"ratings/batches/{task_id}")
            status_data = status_response.json()

            if status_data.get("status") == "FAILURE":
                raise RuntimeError(f"Batch rating failed: {status_data.get('error_msg')}")

            if status_data.get("status") == "SUCCESS":
                # Fetch the responses which will have ratings
                responses = await self._client._responses.alist(
                    filters=PromptResponseFilter(response_ids=[pr.id for pr in prompt_responses])
                )
                return [r.ratings for r in responses]

            await asyncio.sleep(polling_interval)

        raise TimeoutError(f"Batch rating timed out after {timeout} seconds")
