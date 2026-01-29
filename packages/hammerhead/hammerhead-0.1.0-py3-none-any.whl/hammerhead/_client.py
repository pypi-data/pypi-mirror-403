# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Mapping
from typing_extensions import Self, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    Omit,
    Headers,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    not_given,
)
from ._utils import is_given, get_async_library
from ._compat import cached_property
from ._version import __version__
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import oauth, routes, workouts, activities
    from .resources.oauth import OAuthResource, AsyncOAuthResource
    from .resources.activities import ActivitiesResource, AsyncActivitiesResource
    from .resources.routes.routes import RoutesResource, AsyncRoutesResource
    from .resources.workouts.workouts import WorkoutsResource, AsyncWorkoutsResource

__all__ = [
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "Hammerhead",
    "AsyncHammerhead",
    "Client",
    "AsyncClient",
]


class Hammerhead(SyncAPIClient):
    # client options
    webhook_signature: str | None

    def __init__(
        self,
        *,
        webhook_signature: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous Hammerhead client instance.

        This automatically infers the `webhook_signature` argument from the `HAMMERHEAD_WEBHOOK_SIGNATURE` environment variable if it is not provided.
        """
        if webhook_signature is None:
            webhook_signature = os.environ.get("HAMMERHEAD_WEBHOOK_SIGNATURE")
        self.webhook_signature = webhook_signature

        if base_url is None:
            base_url = os.environ.get("HAMMERHEAD_BASE_URL")
        self._base_url_overridden = base_url is not None
        if base_url is None:
            base_url = f"https://api.hammerhead.io/v1/api/"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def oauth(self) -> OAuthResource:
        from .resources.oauth import OAuthResource

        return OAuthResource(self)

    @cached_property
    def activities(self) -> ActivitiesResource:
        from .resources.activities import ActivitiesResource

        return ActivitiesResource(self)

    @cached_property
    def routes(self) -> RoutesResource:
        from .resources.routes import RoutesResource

        return RoutesResource(self)

    @cached_property
    def workouts(self) -> WorkoutsResource:
        from .resources.workouts import WorkoutsResource

        return WorkoutsResource(self)

    @cached_property
    def with_raw_response(self) -> HammerheadWithRawResponse:
        return HammerheadWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> HammerheadWithStreamedResponse:
        return HammerheadWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        webhook_signature = self.webhook_signature
        if webhook_signature is None:
            return {}
        return {"X-Hmac-Signature": webhook_signature}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    @override
    def _validate_headers(self, headers: Headers, custom_headers: Headers) -> None:
        if headers.get("X-Hmac-Signature") or isinstance(custom_headers.get("X-Hmac-Signature"), Omit):
            return

        raise TypeError(
            '"Could not resolve authentication method. Expected the webhook_signature to be set. Or for the `X-Hmac-Signature` headers to be explicitly omitted"'
        )

    def copy(
        self,
        *,
        webhook_signature: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        client = self.__class__(
            webhook_signature=webhook_signature or self.webhook_signature,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )
        client._base_url_overridden = self._base_url_overridden or base_url is not None
        return client

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncHammerhead(AsyncAPIClient):
    # client options
    webhook_signature: str | None

    def __init__(
        self,
        *,
        webhook_signature: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async AsyncHammerhead client instance.

        This automatically infers the `webhook_signature` argument from the `HAMMERHEAD_WEBHOOK_SIGNATURE` environment variable if it is not provided.
        """
        if webhook_signature is None:
            webhook_signature = os.environ.get("HAMMERHEAD_WEBHOOK_SIGNATURE")
        self.webhook_signature = webhook_signature

        if base_url is None:
            base_url = os.environ.get("HAMMERHEAD_BASE_URL")
        self._base_url_overridden = base_url is not None
        if base_url is None:
            base_url = f"https://api.hammerhead.io/v1/api/"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def oauth(self) -> AsyncOAuthResource:
        from .resources.oauth import AsyncOAuthResource

        return AsyncOAuthResource(self)

    @cached_property
    def activities(self) -> AsyncActivitiesResource:
        from .resources.activities import AsyncActivitiesResource

        return AsyncActivitiesResource(self)

    @cached_property
    def routes(self) -> AsyncRoutesResource:
        from .resources.routes import AsyncRoutesResource

        return AsyncRoutesResource(self)

    @cached_property
    def workouts(self) -> AsyncWorkoutsResource:
        from .resources.workouts import AsyncWorkoutsResource

        return AsyncWorkoutsResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncHammerheadWithRawResponse:
        return AsyncHammerheadWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncHammerheadWithStreamedResponse:
        return AsyncHammerheadWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        webhook_signature = self.webhook_signature
        if webhook_signature is None:
            return {}
        return {"X-Hmac-Signature": webhook_signature}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    @override
    def _validate_headers(self, headers: Headers, custom_headers: Headers) -> None:
        if headers.get("X-Hmac-Signature") or isinstance(custom_headers.get("X-Hmac-Signature"), Omit):
            return

        raise TypeError(
            '"Could not resolve authentication method. Expected the webhook_signature to be set. Or for the `X-Hmac-Signature` headers to be explicitly omitted"'
        )

    def copy(
        self,
        *,
        webhook_signature: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        client = self.__class__(
            webhook_signature=webhook_signature or self.webhook_signature,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )
        client._base_url_overridden = self._base_url_overridden or base_url is not None
        return client

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class HammerheadWithRawResponse:
    _client: Hammerhead

    def __init__(self, client: Hammerhead) -> None:
        self._client = client

    @cached_property
    def oauth(self) -> oauth.OAuthResourceWithRawResponse:
        from .resources.oauth import OAuthResourceWithRawResponse

        return OAuthResourceWithRawResponse(self._client.oauth)

    @cached_property
    def activities(self) -> activities.ActivitiesResourceWithRawResponse:
        from .resources.activities import ActivitiesResourceWithRawResponse

        return ActivitiesResourceWithRawResponse(self._client.activities)

    @cached_property
    def routes(self) -> routes.RoutesResourceWithRawResponse:
        from .resources.routes import RoutesResourceWithRawResponse

        return RoutesResourceWithRawResponse(self._client.routes)

    @cached_property
    def workouts(self) -> workouts.WorkoutsResourceWithRawResponse:
        from .resources.workouts import WorkoutsResourceWithRawResponse

        return WorkoutsResourceWithRawResponse(self._client.workouts)


class AsyncHammerheadWithRawResponse:
    _client: AsyncHammerhead

    def __init__(self, client: AsyncHammerhead) -> None:
        self._client = client

    @cached_property
    def oauth(self) -> oauth.AsyncOAuthResourceWithRawResponse:
        from .resources.oauth import AsyncOAuthResourceWithRawResponse

        return AsyncOAuthResourceWithRawResponse(self._client.oauth)

    @cached_property
    def activities(self) -> activities.AsyncActivitiesResourceWithRawResponse:
        from .resources.activities import AsyncActivitiesResourceWithRawResponse

        return AsyncActivitiesResourceWithRawResponse(self._client.activities)

    @cached_property
    def routes(self) -> routes.AsyncRoutesResourceWithRawResponse:
        from .resources.routes import AsyncRoutesResourceWithRawResponse

        return AsyncRoutesResourceWithRawResponse(self._client.routes)

    @cached_property
    def workouts(self) -> workouts.AsyncWorkoutsResourceWithRawResponse:
        from .resources.workouts import AsyncWorkoutsResourceWithRawResponse

        return AsyncWorkoutsResourceWithRawResponse(self._client.workouts)


class HammerheadWithStreamedResponse:
    _client: Hammerhead

    def __init__(self, client: Hammerhead) -> None:
        self._client = client

    @cached_property
    def oauth(self) -> oauth.OAuthResourceWithStreamingResponse:
        from .resources.oauth import OAuthResourceWithStreamingResponse

        return OAuthResourceWithStreamingResponse(self._client.oauth)

    @cached_property
    def activities(self) -> activities.ActivitiesResourceWithStreamingResponse:
        from .resources.activities import ActivitiesResourceWithStreamingResponse

        return ActivitiesResourceWithStreamingResponse(self._client.activities)

    @cached_property
    def routes(self) -> routes.RoutesResourceWithStreamingResponse:
        from .resources.routes import RoutesResourceWithStreamingResponse

        return RoutesResourceWithStreamingResponse(self._client.routes)

    @cached_property
    def workouts(self) -> workouts.WorkoutsResourceWithStreamingResponse:
        from .resources.workouts import WorkoutsResourceWithStreamingResponse

        return WorkoutsResourceWithStreamingResponse(self._client.workouts)


class AsyncHammerheadWithStreamedResponse:
    _client: AsyncHammerhead

    def __init__(self, client: AsyncHammerhead) -> None:
        self._client = client

    @cached_property
    def oauth(self) -> oauth.AsyncOAuthResourceWithStreamingResponse:
        from .resources.oauth import AsyncOAuthResourceWithStreamingResponse

        return AsyncOAuthResourceWithStreamingResponse(self._client.oauth)

    @cached_property
    def activities(self) -> activities.AsyncActivitiesResourceWithStreamingResponse:
        from .resources.activities import AsyncActivitiesResourceWithStreamingResponse

        return AsyncActivitiesResourceWithStreamingResponse(self._client.activities)

    @cached_property
    def routes(self) -> routes.AsyncRoutesResourceWithStreamingResponse:
        from .resources.routes import AsyncRoutesResourceWithStreamingResponse

        return AsyncRoutesResourceWithStreamingResponse(self._client.routes)

    @cached_property
    def workouts(self) -> workouts.AsyncWorkoutsResourceWithStreamingResponse:
        from .resources.workouts import AsyncWorkoutsResourceWithStreamingResponse

        return AsyncWorkoutsResourceWithStreamingResponse(self._client.workouts)


Client = Hammerhead

AsyncClient = AsyncHammerhead
