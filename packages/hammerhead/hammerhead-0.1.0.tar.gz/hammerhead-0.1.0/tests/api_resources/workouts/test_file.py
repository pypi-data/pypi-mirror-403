# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hammerhead import Hammerhead, AsyncHammerhead
from tests.utils import assert_matches_type
from hammerhead.types.workouts import Workout

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestFile:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Hammerhead) -> None:
        file = client.workouts.file.create()
        assert_matches_type(Workout, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Hammerhead) -> None:
        file = client.workouts.file.create(
            planned_date="plannedDate",
            file=b"raw file contents",
        )
        assert_matches_type(Workout, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Hammerhead) -> None:
        response = client.workouts.file.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = response.parse()
        assert_matches_type(Workout, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Hammerhead) -> None:
        with client.workouts.file.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = response.parse()
            assert_matches_type(Workout, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Hammerhead) -> None:
        file = client.workouts.file.update(
            workout_id="workoutId",
        )
        assert_matches_type(Workout, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Hammerhead) -> None:
        file = client.workouts.file.update(
            workout_id="workoutId",
            planned_date="plannedDate",
            file=b"raw file contents",
        )
        assert_matches_type(Workout, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Hammerhead) -> None:
        response = client.workouts.file.with_raw_response.update(
            workout_id="workoutId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = response.parse()
        assert_matches_type(Workout, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Hammerhead) -> None:
        with client.workouts.file.with_streaming_response.update(
            workout_id="workoutId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = response.parse()
            assert_matches_type(Workout, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Hammerhead) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workout_id` but received ''"):
            client.workouts.file.with_raw_response.update(
                workout_id="",
            )


class TestAsyncFile:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncHammerhead) -> None:
        file = await async_client.workouts.file.create()
        assert_matches_type(Workout, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncHammerhead) -> None:
        file = await async_client.workouts.file.create(
            planned_date="plannedDate",
            file=b"raw file contents",
        )
        assert_matches_type(Workout, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHammerhead) -> None:
        response = await async_client.workouts.file.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = await response.parse()
        assert_matches_type(Workout, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHammerhead) -> None:
        async with async_client.workouts.file.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = await response.parse()
            assert_matches_type(Workout, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncHammerhead) -> None:
        file = await async_client.workouts.file.update(
            workout_id="workoutId",
        )
        assert_matches_type(Workout, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncHammerhead) -> None:
        file = await async_client.workouts.file.update(
            workout_id="workoutId",
            planned_date="plannedDate",
            file=b"raw file contents",
        )
        assert_matches_type(Workout, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncHammerhead) -> None:
        response = await async_client.workouts.file.with_raw_response.update(
            workout_id="workoutId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        file = await response.parse()
        assert_matches_type(Workout, file, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncHammerhead) -> None:
        async with async_client.workouts.file.with_streaming_response.update(
            workout_id="workoutId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            file = await response.parse()
            assert_matches_type(Workout, file, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncHammerhead) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `workout_id` but received ''"):
            await async_client.workouts.file.with_raw_response.update(
                workout_id="",
            )
