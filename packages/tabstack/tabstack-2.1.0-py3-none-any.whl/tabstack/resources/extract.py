# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import extract_json_params, extract_markdown_params
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
from ..types.extract_json_response import ExtractJsonResponse
from ..types.extract_markdown_response import ExtractMarkdownResponse

__all__ = ["ExtractResource", "AsyncExtractResource"]


class ExtractResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ExtractResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Mozilla-Ocho/tabstack-python#accessing-raw-response-data-eg-headers
        """
        return ExtractResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ExtractResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Mozilla-Ocho/tabstack-python#with_streaming_response
        """
        return ExtractResourceWithStreamingResponse(self)

    def json(
        self,
        *,
        json_schema: object,
        url: str,
        geo_target: extract_json_params.GeoTarget | Omit = omit,
        nocache: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExtractJsonResponse:
        """
        Fetches a URL and extracts structured data according to a provided JSON schema

        Args:
          json_schema: JSON schema definition that describes the structure of data to extract.

          url: URL to fetch and extract data from

          geo_target: Optional geotargeting parameters for proxy requests

          nocache: Bypass cache and force fresh data retrieval

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/extract/json",
            body=maybe_transform(
                {
                    "json_schema": json_schema,
                    "url": url,
                    "geo_target": geo_target,
                    "nocache": nocache,
                },
                extract_json_params.ExtractJsonParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExtractJsonResponse,
        )

    def markdown(
        self,
        *,
        url: str,
        geo_target: extract_markdown_params.GeoTarget | Omit = omit,
        metadata: bool | Omit = omit,
        nocache: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExtractMarkdownResponse:
        """
        Fetches a URL and converts its HTML content to clean Markdown format with
        optional metadata extraction

        Args:
          url: URL to fetch and convert to markdown

          geo_target: Optional geotargeting parameters for proxy requests

          metadata: Include extracted metadata (Open Graph and HTML metadata) as a separate field in
              the response

          nocache: Bypass cache and force fresh data retrieval

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/extract/markdown",
            body=maybe_transform(
                {
                    "url": url,
                    "geo_target": geo_target,
                    "metadata": metadata,
                    "nocache": nocache,
                },
                extract_markdown_params.ExtractMarkdownParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExtractMarkdownResponse,
        )


class AsyncExtractResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncExtractResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Mozilla-Ocho/tabstack-python#accessing-raw-response-data-eg-headers
        """
        return AsyncExtractResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncExtractResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Mozilla-Ocho/tabstack-python#with_streaming_response
        """
        return AsyncExtractResourceWithStreamingResponse(self)

    async def json(
        self,
        *,
        json_schema: object,
        url: str,
        geo_target: extract_json_params.GeoTarget | Omit = omit,
        nocache: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExtractJsonResponse:
        """
        Fetches a URL and extracts structured data according to a provided JSON schema

        Args:
          json_schema: JSON schema definition that describes the structure of data to extract.

          url: URL to fetch and extract data from

          geo_target: Optional geotargeting parameters for proxy requests

          nocache: Bypass cache and force fresh data retrieval

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/extract/json",
            body=await async_maybe_transform(
                {
                    "json_schema": json_schema,
                    "url": url,
                    "geo_target": geo_target,
                    "nocache": nocache,
                },
                extract_json_params.ExtractJsonParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExtractJsonResponse,
        )

    async def markdown(
        self,
        *,
        url: str,
        geo_target: extract_markdown_params.GeoTarget | Omit = omit,
        metadata: bool | Omit = omit,
        nocache: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExtractMarkdownResponse:
        """
        Fetches a URL and converts its HTML content to clean Markdown format with
        optional metadata extraction

        Args:
          url: URL to fetch and convert to markdown

          geo_target: Optional geotargeting parameters for proxy requests

          metadata: Include extracted metadata (Open Graph and HTML metadata) as a separate field in
              the response

          nocache: Bypass cache and force fresh data retrieval

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/extract/markdown",
            body=await async_maybe_transform(
                {
                    "url": url,
                    "geo_target": geo_target,
                    "metadata": metadata,
                    "nocache": nocache,
                },
                extract_markdown_params.ExtractMarkdownParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExtractMarkdownResponse,
        )


class ExtractResourceWithRawResponse:
    def __init__(self, extract: ExtractResource) -> None:
        self._extract = extract

        self.json = to_raw_response_wrapper(
            extract.json,
        )
        self.markdown = to_raw_response_wrapper(
            extract.markdown,
        )


class AsyncExtractResourceWithRawResponse:
    def __init__(self, extract: AsyncExtractResource) -> None:
        self._extract = extract

        self.json = async_to_raw_response_wrapper(
            extract.json,
        )
        self.markdown = async_to_raw_response_wrapper(
            extract.markdown,
        )


class ExtractResourceWithStreamingResponse:
    def __init__(self, extract: ExtractResource) -> None:
        self._extract = extract

        self.json = to_streamed_response_wrapper(
            extract.json,
        )
        self.markdown = to_streamed_response_wrapper(
            extract.markdown,
        )


class AsyncExtractResourceWithStreamingResponse:
    def __init__(self, extract: AsyncExtractResource) -> None:
        self._extract = extract

        self.json = async_to_streamed_response_wrapper(
            extract.json,
        )
        self.markdown = async_to_streamed_response_wrapper(
            extract.markdown,
        )
