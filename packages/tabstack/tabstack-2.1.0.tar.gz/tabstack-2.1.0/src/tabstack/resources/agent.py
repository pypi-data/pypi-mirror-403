# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..types import agent_automate_params, agent_research_params
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
from .._streaming import Stream, AsyncStream
from .._base_client import make_request_options
from ..types.automate_event import AutomateEvent
from ..types.research_event import ResearchEvent

__all__ = ["AgentResource", "AsyncAgentResource"]


class AgentResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AgentResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Mozilla-Ocho/tabstack-python#accessing-raw-response-data-eg-headers
        """
        return AgentResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AgentResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Mozilla-Ocho/tabstack-python#with_streaming_response
        """
        return AgentResourceWithStreamingResponse(self)

    def automate(
        self,
        *,
        task: str,
        data: object | Omit = omit,
        geo_target: agent_automate_params.GeoTarget | Omit = omit,
        guardrails: str | Omit = omit,
        max_iterations: int | Omit = omit,
        max_validation_attempts: int | Omit = omit,
        url: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Stream[AutomateEvent]:
        """
        Execute AI-powered browser automation tasks using natural language with optional
        geotargeting. This endpoint **always streams** responses using Server-Sent
        Events (SSE).

        **Streaming Response:**

        - All responses are streamed using Server-Sent Events (`text/event-stream`)
        - Real-time progress updates and results as they're generated

        **Geotargeting:**

        - Optionally specify a country code for geotargeted browsing

        **Use Cases:**

        - Web scraping and data extraction
        - Form filling and interaction
        - Navigation and information gathering
        - Multi-step web workflows
        - Content analysis from web pages

        Args:
          task: The task description in natural language

          data: JSON data to provide context for form filling or complex tasks

          geo_target: Optional geotargeting parameters for proxy requests

          guardrails: Safety constraints for execution

          max_iterations: Maximum task iterations

          max_validation_attempts: Maximum validation attempts

          url: Starting URL for the task

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "text/event-stream", **(extra_headers or {})}
        return self._post(
            "/automate",
            body=maybe_transform(
                {
                    "task": task,
                    "data": data,
                    "geo_target": geo_target,
                    "guardrails": guardrails,
                    "max_iterations": max_iterations,
                    "max_validation_attempts": max_validation_attempts,
                    "url": url,
                },
                agent_automate_params.AgentAutomateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AutomateEvent,
            stream=True,
            stream_cls=Stream[AutomateEvent],
        )

    def research(
        self,
        *,
        query: str,
        fetch_timeout: int | Omit = omit,
        mode: Literal["fast", "balanced"] | Omit = omit,
        nocache: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Stream[ResearchEvent]:
        """
        Execute AI-powered research queries that search the web, analyze sources, and
        synthesize comprehensive answers. This endpoint **always streams** responses
        using Server-Sent Events (SSE).

        **Streaming Response:**

        - All responses are streamed using Server-Sent Events (`text/event-stream`)
        - Real-time progress updates as research progresses through phases

        **Research Modes:**

        - `fast` - Quick answers with minimal web searches
        - `balanced` - Standard research with multiple iterations (default)

        **Use Cases:**

        - Answering complex questions with cited sources
        - Synthesizing information from multiple web sources
        - Research reports on specific topics
        - Fact-checking and verification tasks

        Args:
          query: The research query or question to answer

          fetch_timeout: Timeout in seconds for fetching web pages

          mode: Research mode: fast (quick answers), balanced (standard research, default)

          nocache: Skip cache and force fresh research

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "text/event-stream", **(extra_headers or {})}
        return self._post(
            "/research",
            body=maybe_transform(
                {
                    "query": query,
                    "fetch_timeout": fetch_timeout,
                    "mode": mode,
                    "nocache": nocache,
                },
                agent_research_params.AgentResearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResearchEvent,
            stream=True,
            stream_cls=Stream[ResearchEvent],
        )


class AsyncAgentResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAgentResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Mozilla-Ocho/tabstack-python#accessing-raw-response-data-eg-headers
        """
        return AsyncAgentResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAgentResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Mozilla-Ocho/tabstack-python#with_streaming_response
        """
        return AsyncAgentResourceWithStreamingResponse(self)

    async def automate(
        self,
        *,
        task: str,
        data: object | Omit = omit,
        geo_target: agent_automate_params.GeoTarget | Omit = omit,
        guardrails: str | Omit = omit,
        max_iterations: int | Omit = omit,
        max_validation_attempts: int | Omit = omit,
        url: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncStream[AutomateEvent]:
        """
        Execute AI-powered browser automation tasks using natural language with optional
        geotargeting. This endpoint **always streams** responses using Server-Sent
        Events (SSE).

        **Streaming Response:**

        - All responses are streamed using Server-Sent Events (`text/event-stream`)
        - Real-time progress updates and results as they're generated

        **Geotargeting:**

        - Optionally specify a country code for geotargeted browsing

        **Use Cases:**

        - Web scraping and data extraction
        - Form filling and interaction
        - Navigation and information gathering
        - Multi-step web workflows
        - Content analysis from web pages

        Args:
          task: The task description in natural language

          data: JSON data to provide context for form filling or complex tasks

          geo_target: Optional geotargeting parameters for proxy requests

          guardrails: Safety constraints for execution

          max_iterations: Maximum task iterations

          max_validation_attempts: Maximum validation attempts

          url: Starting URL for the task

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "text/event-stream", **(extra_headers or {})}
        return await self._post(
            "/automate",
            body=await async_maybe_transform(
                {
                    "task": task,
                    "data": data,
                    "geo_target": geo_target,
                    "guardrails": guardrails,
                    "max_iterations": max_iterations,
                    "max_validation_attempts": max_validation_attempts,
                    "url": url,
                },
                agent_automate_params.AgentAutomateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AutomateEvent,
            stream=True,
            stream_cls=AsyncStream[AutomateEvent],
        )

    async def research(
        self,
        *,
        query: str,
        fetch_timeout: int | Omit = omit,
        mode: Literal["fast", "balanced"] | Omit = omit,
        nocache: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncStream[ResearchEvent]:
        """
        Execute AI-powered research queries that search the web, analyze sources, and
        synthesize comprehensive answers. This endpoint **always streams** responses
        using Server-Sent Events (SSE).

        **Streaming Response:**

        - All responses are streamed using Server-Sent Events (`text/event-stream`)
        - Real-time progress updates as research progresses through phases

        **Research Modes:**

        - `fast` - Quick answers with minimal web searches
        - `balanced` - Standard research with multiple iterations (default)

        **Use Cases:**

        - Answering complex questions with cited sources
        - Synthesizing information from multiple web sources
        - Research reports on specific topics
        - Fact-checking and verification tasks

        Args:
          query: The research query or question to answer

          fetch_timeout: Timeout in seconds for fetching web pages

          mode: Research mode: fast (quick answers), balanced (standard research, default)

          nocache: Skip cache and force fresh research

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "text/event-stream", **(extra_headers or {})}
        return await self._post(
            "/research",
            body=await async_maybe_transform(
                {
                    "query": query,
                    "fetch_timeout": fetch_timeout,
                    "mode": mode,
                    "nocache": nocache,
                },
                agent_research_params.AgentResearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResearchEvent,
            stream=True,
            stream_cls=AsyncStream[ResearchEvent],
        )


class AgentResourceWithRawResponse:
    def __init__(self, agent: AgentResource) -> None:
        self._agent = agent

        self.automate = to_raw_response_wrapper(
            agent.automate,
        )
        self.research = to_raw_response_wrapper(
            agent.research,
        )


class AsyncAgentResourceWithRawResponse:
    def __init__(self, agent: AsyncAgentResource) -> None:
        self._agent = agent

        self.automate = async_to_raw_response_wrapper(
            agent.automate,
        )
        self.research = async_to_raw_response_wrapper(
            agent.research,
        )


class AgentResourceWithStreamingResponse:
    def __init__(self, agent: AgentResource) -> None:
        self._agent = agent

        self.automate = to_streamed_response_wrapper(
            agent.automate,
        )
        self.research = to_streamed_response_wrapper(
            agent.research,
        )


class AsyncAgentResourceWithStreamingResponse:
    def __init__(self, agent: AsyncAgentResource) -> None:
        self._agent = agent

        self.automate = async_to_streamed_response_wrapper(
            agent.automate,
        )
        self.research = async_to_streamed_response_wrapper(
            agent.research,
        )
