# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hammerhead import Hammerhead, AsyncHammerhead
from tests.utils import assert_matches_type
from hammerhead.types import (
    OAuthExchangeTokenResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestOAuth:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism doesn't properly handle redirects")
    @parametrize
    def test_method_authorize(self, client: Hammerhead) -> None:
        oauth = client.oauth.authorize(
            client_id="client_id",
            redirect_uri="redirect_uri",
            response_type="code",
            scope="scope",
            state="state",
        )
        assert oauth is None

    @pytest.mark.skip(reason="Prism doesn't properly handle redirects")
    @parametrize
    def test_raw_response_authorize(self, client: Hammerhead) -> None:
        response = client.oauth.with_raw_response.authorize(
            client_id="client_id",
            redirect_uri="redirect_uri",
            response_type="code",
            scope="scope",
            state="state",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        oauth = response.parse()
        assert oauth is None

    @pytest.mark.skip(reason="Prism doesn't properly handle redirects")
    @parametrize
    def test_streaming_response_authorize(self, client: Hammerhead) -> None:
        with client.oauth.with_streaming_response.authorize(
            client_id="client_id",
            redirect_uri="redirect_uri",
            response_type="code",
            scope="scope",
            state="state",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            oauth = response.parse()
            assert oauth is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_deauthorize(self, client: Hammerhead) -> None:
        oauth = client.oauth.deauthorize(
            token="token",
            client_id="client_id",
            client_secret="client_secret",
        )
        assert oauth is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_deauthorize(self, client: Hammerhead) -> None:
        response = client.oauth.with_raw_response.deauthorize(
            token="token",
            client_id="client_id",
            client_secret="client_secret",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        oauth = response.parse()
        assert oauth is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_deauthorize(self, client: Hammerhead) -> None:
        with client.oauth.with_streaming_response.deauthorize(
            token="token",
            client_id="client_id",
            client_secret="client_secret",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            oauth = response.parse()
            assert oauth is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_exchange_token(self, client: Hammerhead) -> None:
        oauth = client.oauth.exchange_token(
            client_id="client_id",
            client_secret="client_secret",
            grant_type="authorization_code",
        )
        assert_matches_type(OAuthExchangeTokenResponse, oauth, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_exchange_token_with_all_params(self, client: Hammerhead) -> None:
        oauth = client.oauth.exchange_token(
            client_id="client_id",
            client_secret="client_secret",
            grant_type="authorization_code",
            code="code",
            redirect_uri="redirect_uri",
            refresh_token="refresh_token",
        )
        assert_matches_type(OAuthExchangeTokenResponse, oauth, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_exchange_token(self, client: Hammerhead) -> None:
        response = client.oauth.with_raw_response.exchange_token(
            client_id="client_id",
            client_secret="client_secret",
            grant_type="authorization_code",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        oauth = response.parse()
        assert_matches_type(OAuthExchangeTokenResponse, oauth, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_exchange_token(self, client: Hammerhead) -> None:
        with client.oauth.with_streaming_response.exchange_token(
            client_id="client_id",
            client_secret="client_secret",
            grant_type="authorization_code",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            oauth = response.parse()
            assert_matches_type(OAuthExchangeTokenResponse, oauth, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncOAuth:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism doesn't properly handle redirects")
    @parametrize
    async def test_method_authorize(self, async_client: AsyncHammerhead) -> None:
        oauth = await async_client.oauth.authorize(
            client_id="client_id",
            redirect_uri="redirect_uri",
            response_type="code",
            scope="scope",
            state="state",
        )
        assert oauth is None

    @pytest.mark.skip(reason="Prism doesn't properly handle redirects")
    @parametrize
    async def test_raw_response_authorize(self, async_client: AsyncHammerhead) -> None:
        response = await async_client.oauth.with_raw_response.authorize(
            client_id="client_id",
            redirect_uri="redirect_uri",
            response_type="code",
            scope="scope",
            state="state",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        oauth = await response.parse()
        assert oauth is None

    @pytest.mark.skip(reason="Prism doesn't properly handle redirects")
    @parametrize
    async def test_streaming_response_authorize(self, async_client: AsyncHammerhead) -> None:
        async with async_client.oauth.with_streaming_response.authorize(
            client_id="client_id",
            redirect_uri="redirect_uri",
            response_type="code",
            scope="scope",
            state="state",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            oauth = await response.parse()
            assert oauth is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_deauthorize(self, async_client: AsyncHammerhead) -> None:
        oauth = await async_client.oauth.deauthorize(
            token="token",
            client_id="client_id",
            client_secret="client_secret",
        )
        assert oauth is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_deauthorize(self, async_client: AsyncHammerhead) -> None:
        response = await async_client.oauth.with_raw_response.deauthorize(
            token="token",
            client_id="client_id",
            client_secret="client_secret",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        oauth = await response.parse()
        assert oauth is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_deauthorize(self, async_client: AsyncHammerhead) -> None:
        async with async_client.oauth.with_streaming_response.deauthorize(
            token="token",
            client_id="client_id",
            client_secret="client_secret",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            oauth = await response.parse()
            assert oauth is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_exchange_token(self, async_client: AsyncHammerhead) -> None:
        oauth = await async_client.oauth.exchange_token(
            client_id="client_id",
            client_secret="client_secret",
            grant_type="authorization_code",
        )
        assert_matches_type(OAuthExchangeTokenResponse, oauth, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_exchange_token_with_all_params(self, async_client: AsyncHammerhead) -> None:
        oauth = await async_client.oauth.exchange_token(
            client_id="client_id",
            client_secret="client_secret",
            grant_type="authorization_code",
            code="code",
            redirect_uri="redirect_uri",
            refresh_token="refresh_token",
        )
        assert_matches_type(OAuthExchangeTokenResponse, oauth, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_exchange_token(self, async_client: AsyncHammerhead) -> None:
        response = await async_client.oauth.with_raw_response.exchange_token(
            client_id="client_id",
            client_secret="client_secret",
            grant_type="authorization_code",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        oauth = await response.parse()
        assert_matches_type(OAuthExchangeTokenResponse, oauth, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_exchange_token(self, async_client: AsyncHammerhead) -> None:
        async with async_client.oauth.with_streaming_response.exchange_token(
            client_id="client_id",
            client_secret="client_secret",
            grant_type="authorization_code",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            oauth = await response.parse()
            assert_matches_type(OAuthExchangeTokenResponse, oauth, path=["response"])

        assert cast(Any, response.is_closed) is True
