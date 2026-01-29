# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import httpx
import pytest
from respx import MockRouter

from hammerhead import Hammerhead, AsyncHammerhead
from tests.utils import assert_matches_type
from hammerhead.types import ActivityListResponse, ActivityRetrieveResponse
from hammerhead._utils import parse_date
from hammerhead._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestActivities:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Hammerhead) -> None:
        activity = client.activities.retrieve(
            "activityId",
        )
        assert_matches_type(ActivityRetrieveResponse, activity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Hammerhead) -> None:
        response = client.activities.with_raw_response.retrieve(
            "activityId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        activity = response.parse()
        assert_matches_type(ActivityRetrieveResponse, activity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Hammerhead) -> None:
        with client.activities.with_streaming_response.retrieve(
            "activityId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            activity = response.parse()
            assert_matches_type(ActivityRetrieveResponse, activity, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Hammerhead) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `activity_id` but received ''"):
            client.activities.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Hammerhead) -> None:
        activity = client.activities.list()
        assert_matches_type(ActivityListResponse, activity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Hammerhead) -> None:
        activity = client.activities.list(
            page=1,
            per_page=1,
            start_date=parse_date("2025-05-31"),
        )
        assert_matches_type(ActivityListResponse, activity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Hammerhead) -> None:
        response = client.activities.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        activity = response.parse()
        assert_matches_type(ActivityListResponse, activity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Hammerhead) -> None:
        with client.activities.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            activity = response.parse()
            assert_matches_type(ActivityListResponse, activity, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_retrieve_file(self, client: Hammerhead, respx_mock: MockRouter) -> None:
        respx_mock.get("/activities/activityId/file").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        activity = client.activities.retrieve_file(
            "activityId",
        )
        assert activity.is_closed
        assert activity.json() == {"foo": "bar"}
        assert cast(Any, activity.is_closed) is True
        assert isinstance(activity, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_raw_response_retrieve_file(self, client: Hammerhead, respx_mock: MockRouter) -> None:
        respx_mock.get("/activities/activityId/file").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        activity = client.activities.with_raw_response.retrieve_file(
            "activityId",
        )

        assert activity.is_closed is True
        assert activity.http_request.headers.get("X-Stainless-Lang") == "python"
        assert activity.json() == {"foo": "bar"}
        assert isinstance(activity, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_streaming_response_retrieve_file(self, client: Hammerhead, respx_mock: MockRouter) -> None:
        respx_mock.get("/activities/activityId/file").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        with client.activities.with_streaming_response.retrieve_file(
            "activityId",
        ) as activity:
            assert not activity.is_closed
            assert activity.http_request.headers.get("X-Stainless-Lang") == "python"

            assert activity.json() == {"foo": "bar"}
            assert cast(Any, activity.is_closed) is True
            assert isinstance(activity, StreamedBinaryAPIResponse)

        assert cast(Any, activity.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_path_params_retrieve_file(self, client: Hammerhead) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `activity_id` but received ''"):
            client.activities.with_raw_response.retrieve_file(
                "",
            )


class TestAsyncActivities:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncHammerhead) -> None:
        activity = await async_client.activities.retrieve(
            "activityId",
        )
        assert_matches_type(ActivityRetrieveResponse, activity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncHammerhead) -> None:
        response = await async_client.activities.with_raw_response.retrieve(
            "activityId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        activity = await response.parse()
        assert_matches_type(ActivityRetrieveResponse, activity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncHammerhead) -> None:
        async with async_client.activities.with_streaming_response.retrieve(
            "activityId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            activity = await response.parse()
            assert_matches_type(ActivityRetrieveResponse, activity, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncHammerhead) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `activity_id` but received ''"):
            await async_client.activities.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncHammerhead) -> None:
        activity = await async_client.activities.list()
        assert_matches_type(ActivityListResponse, activity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncHammerhead) -> None:
        activity = await async_client.activities.list(
            page=1,
            per_page=1,
            start_date=parse_date("2025-05-31"),
        )
        assert_matches_type(ActivityListResponse, activity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncHammerhead) -> None:
        response = await async_client.activities.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        activity = await response.parse()
        assert_matches_type(ActivityListResponse, activity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncHammerhead) -> None:
        async with async_client.activities.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            activity = await response.parse()
            assert_matches_type(ActivityListResponse, activity, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_retrieve_file(self, async_client: AsyncHammerhead, respx_mock: MockRouter) -> None:
        respx_mock.get("/activities/activityId/file").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        activity = await async_client.activities.retrieve_file(
            "activityId",
        )
        assert activity.is_closed
        assert await activity.json() == {"foo": "bar"}
        assert cast(Any, activity.is_closed) is True
        assert isinstance(activity, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_raw_response_retrieve_file(self, async_client: AsyncHammerhead, respx_mock: MockRouter) -> None:
        respx_mock.get("/activities/activityId/file").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        activity = await async_client.activities.with_raw_response.retrieve_file(
            "activityId",
        )

        assert activity.is_closed is True
        assert activity.http_request.headers.get("X-Stainless-Lang") == "python"
        assert await activity.json() == {"foo": "bar"}
        assert isinstance(activity, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_streaming_response_retrieve_file(
        self, async_client: AsyncHammerhead, respx_mock: MockRouter
    ) -> None:
        respx_mock.get("/activities/activityId/file").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        async with async_client.activities.with_streaming_response.retrieve_file(
            "activityId",
        ) as activity:
            assert not activity.is_closed
            assert activity.http_request.headers.get("X-Stainless-Lang") == "python"

            assert await activity.json() == {"foo": "bar"}
            assert cast(Any, activity.is_closed) is True
            assert isinstance(activity, AsyncStreamedBinaryAPIResponse)

        assert cast(Any, activity.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_path_params_retrieve_file(self, async_client: AsyncHammerhead) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `activity_id` but received ''"):
            await async_client.activities.with_raw_response.retrieve_file(
                "",
            )
