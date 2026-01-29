# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hammerhead import Hammerhead, AsyncHammerhead

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestWorkouts:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Hammerhead) -> None:
        workout = client.workouts.delete(
            "workoutId",
        )
        assert workout is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Hammerhead) -> None:
        response = client.workouts.with_raw_response.delete(
            "workoutId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workout = response.parse()
        assert workout is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Hammerhead) -> None:
        with client.workouts.with_streaming_response.delete(
            "workoutId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workout = response.parse()
            assert workout is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Hammerhead) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workout_id` but received ''"):
            client.workouts.with_raw_response.delete(
                "",
            )


class TestAsyncWorkouts:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncHammerhead) -> None:
        workout = await async_client.workouts.delete(
            "workoutId",
        )
        assert workout is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncHammerhead) -> None:
        response = await async_client.workouts.with_raw_response.delete(
            "workoutId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        workout = await response.parse()
        assert workout is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncHammerhead) -> None:
        async with async_client.workouts.with_streaming_response.delete(
            "workoutId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            workout = await response.parse()
            assert workout is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncHammerhead) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workout_id` but received ''"):
            await async_client.workouts.with_raw_response.delete(
                "",
            )
