# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tabstack import Tabstack, AsyncTabstack

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAgent:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    def test_method_automate(self, client: Tabstack) -> None:
        agent_stream = client.agent.automate(
            task="Find the top 3 trending repositories and extract their names, descriptions, and star counts",
        )
        agent_stream.response.close()

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    def test_method_automate_with_all_params(self, client: Tabstack) -> None:
        agent_stream = client.agent.automate(
            task="Find the top 3 trending repositories and extract their names, descriptions, and star counts",
            data={},
            geo_target={"country": "US"},
            guardrails="browse and extract only, don't interact with repositories",
            max_iterations=50,
            max_validation_attempts=3,
            url="https://github.com/trending",
        )
        agent_stream.response.close()

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    def test_raw_response_automate(self, client: Tabstack) -> None:
        response = client.agent.with_raw_response.automate(
            task="Find the top 3 trending repositories and extract their names, descriptions, and star counts",
        )

        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stream = response.parse()
        stream.close()

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    def test_streaming_response_automate(self, client: Tabstack) -> None:
        with client.agent.with_streaming_response.automate(
            task="Find the top 3 trending repositories and extract their names, descriptions, and star counts",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stream = response.parse()
            stream.close()

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    def test_method_research(self, client: Tabstack) -> None:
        agent_stream = client.agent.research(
            query="What are the latest developments in quantum computing?",
        )
        agent_stream.response.close()

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    def test_method_research_with_all_params(self, client: Tabstack) -> None:
        agent_stream = client.agent.research(
            query="What are the latest developments in quantum computing?",
            fetch_timeout=30,
            mode="balanced",
            nocache=False,
        )
        agent_stream.response.close()

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    def test_raw_response_research(self, client: Tabstack) -> None:
        response = client.agent.with_raw_response.research(
            query="What are the latest developments in quantum computing?",
        )

        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stream = response.parse()
        stream.close()

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    def test_streaming_response_research(self, client: Tabstack) -> None:
        with client.agent.with_streaming_response.research(
            query="What are the latest developments in quantum computing?",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stream = response.parse()
            stream.close()

        assert cast(Any, response.is_closed) is True


class TestAsyncAgent:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    async def test_method_automate(self, async_client: AsyncTabstack) -> None:
        agent_stream = await async_client.agent.automate(
            task="Find the top 3 trending repositories and extract their names, descriptions, and star counts",
        )
        await agent_stream.response.aclose()

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    async def test_method_automate_with_all_params(self, async_client: AsyncTabstack) -> None:
        agent_stream = await async_client.agent.automate(
            task="Find the top 3 trending repositories and extract their names, descriptions, and star counts",
            data={},
            geo_target={"country": "US"},
            guardrails="browse and extract only, don't interact with repositories",
            max_iterations=50,
            max_validation_attempts=3,
            url="https://github.com/trending",
        )
        await agent_stream.response.aclose()

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    async def test_raw_response_automate(self, async_client: AsyncTabstack) -> None:
        response = await async_client.agent.with_raw_response.automate(
            task="Find the top 3 trending repositories and extract their names, descriptions, and star counts",
        )

        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stream = await response.parse()
        await stream.close()

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    async def test_streaming_response_automate(self, async_client: AsyncTabstack) -> None:
        async with async_client.agent.with_streaming_response.automate(
            task="Find the top 3 trending repositories and extract their names, descriptions, and star counts",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stream = await response.parse()
            await stream.close()

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    async def test_method_research(self, async_client: AsyncTabstack) -> None:
        agent_stream = await async_client.agent.research(
            query="What are the latest developments in quantum computing?",
        )
        await agent_stream.response.aclose()

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    async def test_method_research_with_all_params(self, async_client: AsyncTabstack) -> None:
        agent_stream = await async_client.agent.research(
            query="What are the latest developments in quantum computing?",
            fetch_timeout=30,
            mode="balanced",
            nocache=False,
        )
        await agent_stream.response.aclose()

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    async def test_raw_response_research(self, async_client: AsyncTabstack) -> None:
        response = await async_client.agent.with_raw_response.research(
            query="What are the latest developments in quantum computing?",
        )

        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stream = await response.parse()
        await stream.close()

    @pytest.mark.skip(reason="Prism doesn't support text/event-stream responses")
    @parametrize
    async def test_streaming_response_research(self, async_client: AsyncTabstack) -> None:
        async with async_client.agent.with_streaming_response.research(
            query="What are the latest developments in quantum computing?",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stream = await response.parse()
            await stream.close()

        assert cast(Any, response.is_closed) is True
