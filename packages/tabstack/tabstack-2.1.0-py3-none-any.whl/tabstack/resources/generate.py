# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import generate_json_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.generate_json_response import GenerateJsonResponse

__all__ = ["GenerateResource", "AsyncGenerateResource"]


class GenerateResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> GenerateResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Mozilla-Ocho/tabstack-python#accessing-raw-response-data-eg-headers
        """
        return GenerateResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> GenerateResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Mozilla-Ocho/tabstack-python#with_streaming_response
        """
        return GenerateResourceWithStreamingResponse(self)

    def json(
        self,
        *,
        instructions: str,
        json_schema: object,
        url: str,
        geo_target: generate_json_params.GeoTarget | Omit = omit,
        nocache: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GenerateJsonResponse:
        """
        Fetches URL content, extracts data, and transforms it using AI based on custom
        instructions. Use this to generate new content, summaries, or restructured data.

        Args:
          instructions: Instructions describing how to transform the data

          json_schema: JSON schema defining the structure of the transformed output

          url: URL to fetch content from

          geo_target: Optional geotargeting parameters for proxy requests

          nocache: Bypass cache and force fresh data retrieval

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/generate/json",
            body=maybe_transform(
                {
                    "instructions": instructions,
                    "json_schema": json_schema,
                    "url": url,
                    "geo_target": geo_target,
                    "nocache": nocache,
                },
                generate_json_params.GenerateJsonParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GenerateJsonResponse,
        )


class AsyncGenerateResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncGenerateResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Mozilla-Ocho/tabstack-python#accessing-raw-response-data-eg-headers
        """
        return AsyncGenerateResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncGenerateResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Mozilla-Ocho/tabstack-python#with_streaming_response
        """
        return AsyncGenerateResourceWithStreamingResponse(self)

    async def json(
        self,
        *,
        instructions: str,
        json_schema: object,
        url: str,
        geo_target: generate_json_params.GeoTarget | Omit = omit,
        nocache: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> GenerateJsonResponse:
        """
        Fetches URL content, extracts data, and transforms it using AI based on custom
        instructions. Use this to generate new content, summaries, or restructured data.

        Args:
          instructions: Instructions describing how to transform the data

          json_schema: JSON schema defining the structure of the transformed output

          url: URL to fetch content from

          geo_target: Optional geotargeting parameters for proxy requests

          nocache: Bypass cache and force fresh data retrieval

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/generate/json",
            body=await async_maybe_transform(
                {
                    "instructions": instructions,
                    "json_schema": json_schema,
                    "url": url,
                    "geo_target": geo_target,
                    "nocache": nocache,
                },
                generate_json_params.GenerateJsonParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GenerateJsonResponse,
        )


class GenerateResourceWithRawResponse:
    def __init__(self, generate: GenerateResource) -> None:
        self._generate = generate

        self.json = to_raw_response_wrapper(
            generate.json,
        )


class AsyncGenerateResourceWithRawResponse:
    def __init__(self, generate: AsyncGenerateResource) -> None:
        self._generate = generate

        self.json = async_to_raw_response_wrapper(
            generate.json,
        )


class GenerateResourceWithStreamingResponse:
    def __init__(self, generate: GenerateResource) -> None:
        self._generate = generate

        self.json = to_streamed_response_wrapper(
            generate.json,
        )


class AsyncGenerateResourceWithStreamingResponse:
    def __init__(self, generate: AsyncGenerateResource) -> None:
        self._generate = generate

        self.json = async_to_streamed_response_wrapper(
            generate.json,
        )
