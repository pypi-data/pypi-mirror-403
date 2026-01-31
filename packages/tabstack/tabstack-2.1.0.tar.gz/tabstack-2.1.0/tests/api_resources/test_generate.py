# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tabstack import Tabstack, AsyncTabstack
from tests.utils import assert_matches_type
from tabstack.types import GenerateJsonResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestGenerate:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_json(self, client: Tabstack) -> None:
        generate = client.generate.json(
            instructions="For each story, categorize it (tech/business/science/other) and write a one-sentence summary explaining what it's about in simple terms.",
            json_schema={
                "properties": {
                    "summaries": {
                        "items": {
                            "properties": {
                                "category": {
                                    "description": "Story category (tech/business/science/etc)",
                                    "type": "string",
                                },
                                "summary": {
                                    "description": "One-sentence summary of the story",
                                    "type": "string",
                                },
                                "title": {
                                    "description": "Story title",
                                    "type": "string",
                                },
                            },
                            "type": "object",
                        },
                        "type": "array",
                    }
                },
                "type": "object",
            },
            url="https://news.ycombinator.com",
        )
        assert_matches_type(GenerateJsonResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_json_with_all_params(self, client: Tabstack) -> None:
        generate = client.generate.json(
            instructions="For each story, categorize it (tech/business/science/other) and write a one-sentence summary explaining what it's about in simple terms.",
            json_schema={
                "properties": {
                    "summaries": {
                        "items": {
                            "properties": {
                                "category": {
                                    "description": "Story category (tech/business/science/etc)",
                                    "type": "string",
                                },
                                "summary": {
                                    "description": "One-sentence summary of the story",
                                    "type": "string",
                                },
                                "title": {
                                    "description": "Story title",
                                    "type": "string",
                                },
                            },
                            "type": "object",
                        },
                        "type": "array",
                    }
                },
                "type": "object",
            },
            url="https://news.ycombinator.com",
            geo_target={"country": "US"},
            nocache=False,
        )
        assert_matches_type(GenerateJsonResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_json(self, client: Tabstack) -> None:
        response = client.generate.with_raw_response.json(
            instructions="For each story, categorize it (tech/business/science/other) and write a one-sentence summary explaining what it's about in simple terms.",
            json_schema={
                "properties": {
                    "summaries": {
                        "items": {
                            "properties": {
                                "category": {
                                    "description": "Story category (tech/business/science/etc)",
                                    "type": "string",
                                },
                                "summary": {
                                    "description": "One-sentence summary of the story",
                                    "type": "string",
                                },
                                "title": {
                                    "description": "Story title",
                                    "type": "string",
                                },
                            },
                            "type": "object",
                        },
                        "type": "array",
                    }
                },
                "type": "object",
            },
            url="https://news.ycombinator.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generate = response.parse()
        assert_matches_type(GenerateJsonResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_json(self, client: Tabstack) -> None:
        with client.generate.with_streaming_response.json(
            instructions="For each story, categorize it (tech/business/science/other) and write a one-sentence summary explaining what it's about in simple terms.",
            json_schema={
                "properties": {
                    "summaries": {
                        "items": {
                            "properties": {
                                "category": {
                                    "description": "Story category (tech/business/science/etc)",
                                    "type": "string",
                                },
                                "summary": {
                                    "description": "One-sentence summary of the story",
                                    "type": "string",
                                },
                                "title": {
                                    "description": "Story title",
                                    "type": "string",
                                },
                            },
                            "type": "object",
                        },
                        "type": "array",
                    }
                },
                "type": "object",
            },
            url="https://news.ycombinator.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generate = response.parse()
            assert_matches_type(GenerateJsonResponse, generate, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncGenerate:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_json(self, async_client: AsyncTabstack) -> None:
        generate = await async_client.generate.json(
            instructions="For each story, categorize it (tech/business/science/other) and write a one-sentence summary explaining what it's about in simple terms.",
            json_schema={
                "properties": {
                    "summaries": {
                        "items": {
                            "properties": {
                                "category": {
                                    "description": "Story category (tech/business/science/etc)",
                                    "type": "string",
                                },
                                "summary": {
                                    "description": "One-sentence summary of the story",
                                    "type": "string",
                                },
                                "title": {
                                    "description": "Story title",
                                    "type": "string",
                                },
                            },
                            "type": "object",
                        },
                        "type": "array",
                    }
                },
                "type": "object",
            },
            url="https://news.ycombinator.com",
        )
        assert_matches_type(GenerateJsonResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_json_with_all_params(self, async_client: AsyncTabstack) -> None:
        generate = await async_client.generate.json(
            instructions="For each story, categorize it (tech/business/science/other) and write a one-sentence summary explaining what it's about in simple terms.",
            json_schema={
                "properties": {
                    "summaries": {
                        "items": {
                            "properties": {
                                "category": {
                                    "description": "Story category (tech/business/science/etc)",
                                    "type": "string",
                                },
                                "summary": {
                                    "description": "One-sentence summary of the story",
                                    "type": "string",
                                },
                                "title": {
                                    "description": "Story title",
                                    "type": "string",
                                },
                            },
                            "type": "object",
                        },
                        "type": "array",
                    }
                },
                "type": "object",
            },
            url="https://news.ycombinator.com",
            geo_target={"country": "US"},
            nocache=False,
        )
        assert_matches_type(GenerateJsonResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_json(self, async_client: AsyncTabstack) -> None:
        response = await async_client.generate.with_raw_response.json(
            instructions="For each story, categorize it (tech/business/science/other) and write a one-sentence summary explaining what it's about in simple terms.",
            json_schema={
                "properties": {
                    "summaries": {
                        "items": {
                            "properties": {
                                "category": {
                                    "description": "Story category (tech/business/science/etc)",
                                    "type": "string",
                                },
                                "summary": {
                                    "description": "One-sentence summary of the story",
                                    "type": "string",
                                },
                                "title": {
                                    "description": "Story title",
                                    "type": "string",
                                },
                            },
                            "type": "object",
                        },
                        "type": "array",
                    }
                },
                "type": "object",
            },
            url="https://news.ycombinator.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generate = await response.parse()
        assert_matches_type(GenerateJsonResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_json(self, async_client: AsyncTabstack) -> None:
        async with async_client.generate.with_streaming_response.json(
            instructions="For each story, categorize it (tech/business/science/other) and write a one-sentence summary explaining what it's about in simple terms.",
            json_schema={
                "properties": {
                    "summaries": {
                        "items": {
                            "properties": {
                                "category": {
                                    "description": "Story category (tech/business/science/etc)",
                                    "type": "string",
                                },
                                "summary": {
                                    "description": "One-sentence summary of the story",
                                    "type": "string",
                                },
                                "title": {
                                    "description": "Story title",
                                    "type": "string",
                                },
                            },
                            "type": "object",
                        },
                        "type": "array",
                    }
                },
                "type": "object",
            },
            url="https://news.ycombinator.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generate = await response.parse()
            assert_matches_type(GenerateJsonResponse, generate, path=["response"])

        assert cast(Any, response.is_closed) is True
