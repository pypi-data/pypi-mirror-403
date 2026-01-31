# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.api.models import factor_infer_params, factor_train_params
from ....types.api.model_public import ModelPublic
from ....types.api.models.factor_infer_response import FactorInferResponse

__all__ = ["FactorsResource", "AsyncFactorsResource"]


class FactorsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> FactorsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Wood-Wide-AI/wwai-python-sdk#accessing-raw-response-data-eg-headers
        """
        return FactorsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> FactorsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Wood-Wide-AI/wwai-python-sdk#with_streaming_response
        """
        return FactorsResourceWithStreamingResponse(self)

    def infer(
        self,
        model_id: str,
        *,
        dataset_id: Optional[str] | Omit = omit,
        dataset_name: Optional[str] | Omit = omit,
        model_name: Optional[str] | Omit = omit,
        coerce_schema: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FactorInferResponse:
        """Generates human-interpretable factors that explain the data.

        Returns a list of
        human-readable factor descriptions.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not model_id:
            raise ValueError(f"Expected a non-empty value for `model_id` but received {model_id!r}")
        return self._post(
            f"/api/models/factors/{model_id}/infer",
            body=maybe_transform({"coerce_schema": coerce_schema}, factor_infer_params.FactorInferParams),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset_name,
                        "model_name": model_name,
                    },
                    factor_infer_params.FactorInferParams,
                ),
            ),
            cast_to=FactorInferResponse,
        )

    def train(
        self,
        *,
        model_name: str,
        dataset_id: Optional[str] | Omit = omit,
        dataset_name: Optional[str] | Omit = omit,
        hyperparameters: Optional[str] | Omit = omit,
        input_columns: Optional[SequenceNotStr[str]] | Omit = omit,
        overwrite: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ModelPublic:
        """Initiates training for a factors model.

        This is an asynchronous operation.
        Returns a model ID with PENDING status. Use GET /models/{model_id} to monitor
        progress. Once COMPLETE, inference is available via
        /models/factors/{model_id}/infer.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/models/factors/train",
            body=maybe_transform(
                {
                    "model_name": model_name,
                    "hyperparameters": hyperparameters,
                    "input_columns": input_columns,
                    "overwrite": overwrite,
                },
                factor_train_params.FactorTrainParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset_name,
                    },
                    factor_train_params.FactorTrainParams,
                ),
            ),
            cast_to=ModelPublic,
        )


class AsyncFactorsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncFactorsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Wood-Wide-AI/wwai-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncFactorsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncFactorsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Wood-Wide-AI/wwai-python-sdk#with_streaming_response
        """
        return AsyncFactorsResourceWithStreamingResponse(self)

    async def infer(
        self,
        model_id: str,
        *,
        dataset_id: Optional[str] | Omit = omit,
        dataset_name: Optional[str] | Omit = omit,
        model_name: Optional[str] | Omit = omit,
        coerce_schema: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FactorInferResponse:
        """Generates human-interpretable factors that explain the data.

        Returns a list of
        human-readable factor descriptions.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not model_id:
            raise ValueError(f"Expected a non-empty value for `model_id` but received {model_id!r}")
        return await self._post(
            f"/api/models/factors/{model_id}/infer",
            body=await async_maybe_transform({"coerce_schema": coerce_schema}, factor_infer_params.FactorInferParams),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset_name,
                        "model_name": model_name,
                    },
                    factor_infer_params.FactorInferParams,
                ),
            ),
            cast_to=FactorInferResponse,
        )

    async def train(
        self,
        *,
        model_name: str,
        dataset_id: Optional[str] | Omit = omit,
        dataset_name: Optional[str] | Omit = omit,
        hyperparameters: Optional[str] | Omit = omit,
        input_columns: Optional[SequenceNotStr[str]] | Omit = omit,
        overwrite: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ModelPublic:
        """Initiates training for a factors model.

        This is an asynchronous operation.
        Returns a model ID with PENDING status. Use GET /models/{model_id} to monitor
        progress. Once COMPLETE, inference is available via
        /models/factors/{model_id}/infer.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/models/factors/train",
            body=await async_maybe_transform(
                {
                    "model_name": model_name,
                    "hyperparameters": hyperparameters,
                    "input_columns": input_columns,
                    "overwrite": overwrite,
                },
                factor_train_params.FactorTrainParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset_name,
                    },
                    factor_train_params.FactorTrainParams,
                ),
            ),
            cast_to=ModelPublic,
        )


class FactorsResourceWithRawResponse:
    def __init__(self, factors: FactorsResource) -> None:
        self._factors = factors

        self.infer = to_raw_response_wrapper(
            factors.infer,
        )
        self.train = to_raw_response_wrapper(
            factors.train,
        )


class AsyncFactorsResourceWithRawResponse:
    def __init__(self, factors: AsyncFactorsResource) -> None:
        self._factors = factors

        self.infer = async_to_raw_response_wrapper(
            factors.infer,
        )
        self.train = async_to_raw_response_wrapper(
            factors.train,
        )


class FactorsResourceWithStreamingResponse:
    def __init__(self, factors: FactorsResource) -> None:
        self._factors = factors

        self.infer = to_streamed_response_wrapper(
            factors.infer,
        )
        self.train = to_streamed_response_wrapper(
            factors.train,
        )


class AsyncFactorsResourceWithStreamingResponse:
    def __init__(self, factors: AsyncFactorsResource) -> None:
        self._factors = factors

        self.infer = async_to_streamed_response_wrapper(
            factors.infer,
        )
        self.train = async_to_streamed_response_wrapper(
            factors.train,
        )
