# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import date

import httpx

from ..types import activity_list_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    to_custom_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_custom_streamed_response_wrapper,
    async_to_custom_raw_response_wrapper,
    async_to_custom_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.activity_list_response import ActivityListResponse
from ..types.activity_retrieve_response import ActivityRetrieveResponse

__all__ = ["ActivitiesResource", "AsyncActivitiesResource"]


class ActivitiesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ActivitiesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/rchowell/hammerhead-python#accessing-raw-response-data-eg-headers
        """
        return ActivitiesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ActivitiesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/rchowell/hammerhead-python#with_streaming_response
        """
        return ActivitiesResourceWithStreamingResponse(self)

    def retrieve(
        self,
        activity_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ActivityRetrieveResponse:
        """
        Get detailed information about a single activity by ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not activity_id:
            raise ValueError(f"Expected a non-empty value for `activity_id` but received {activity_id!r}")
        return self._get(
            f"/activities/{activity_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ActivityRetrieveResponse,
        )

    def list(
        self,
        *,
        page: int | Omit = omit,
        per_page: int | Omit = omit,
        start_date: Union[str, date] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ActivityListResponse:
        """
        Get a paginated list of user activity summaries.

        Args:
          page: Requested page of activities

          per_page: Number of activities per page

          start_date: A starting date in the form `YYYY-MM-DD`

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/activities",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "page": page,
                        "per_page": per_page,
                        "start_date": start_date,
                    },
                    activity_list_params.ActivityListParams,
                ),
            ),
            cast_to=ActivityListResponse,
        )

    def retrieve_file(
        self,
        activity_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BinaryAPIResponse:
        """
        Get the FIT file of a single activity by ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not activity_id:
            raise ValueError(f"Expected a non-empty value for `activity_id` but received {activity_id!r}")
        extra_headers = {"Accept": "application/vnd.ant.fit", **(extra_headers or {})}
        return self._get(
            f"/activities/{activity_id}/file",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BinaryAPIResponse,
        )


class AsyncActivitiesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncActivitiesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/rchowell/hammerhead-python#accessing-raw-response-data-eg-headers
        """
        return AsyncActivitiesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncActivitiesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/rchowell/hammerhead-python#with_streaming_response
        """
        return AsyncActivitiesResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        activity_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ActivityRetrieveResponse:
        """
        Get detailed information about a single activity by ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not activity_id:
            raise ValueError(f"Expected a non-empty value for `activity_id` but received {activity_id!r}")
        return await self._get(
            f"/activities/{activity_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ActivityRetrieveResponse,
        )

    async def list(
        self,
        *,
        page: int | Omit = omit,
        per_page: int | Omit = omit,
        start_date: Union[str, date] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ActivityListResponse:
        """
        Get a paginated list of user activity summaries.

        Args:
          page: Requested page of activities

          per_page: Number of activities per page

          start_date: A starting date in the form `YYYY-MM-DD`

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/activities",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "page": page,
                        "per_page": per_page,
                        "start_date": start_date,
                    },
                    activity_list_params.ActivityListParams,
                ),
            ),
            cast_to=ActivityListResponse,
        )

    async def retrieve_file(
        self,
        activity_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncBinaryAPIResponse:
        """
        Get the FIT file of a single activity by ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not activity_id:
            raise ValueError(f"Expected a non-empty value for `activity_id` but received {activity_id!r}")
        extra_headers = {"Accept": "application/vnd.ant.fit", **(extra_headers or {})}
        return await self._get(
            f"/activities/{activity_id}/file",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AsyncBinaryAPIResponse,
        )


class ActivitiesResourceWithRawResponse:
    def __init__(self, activities: ActivitiesResource) -> None:
        self._activities = activities

        self.retrieve = to_raw_response_wrapper(
            activities.retrieve,
        )
        self.list = to_raw_response_wrapper(
            activities.list,
        )
        self.retrieve_file = to_custom_raw_response_wrapper(
            activities.retrieve_file,
            BinaryAPIResponse,
        )


class AsyncActivitiesResourceWithRawResponse:
    def __init__(self, activities: AsyncActivitiesResource) -> None:
        self._activities = activities

        self.retrieve = async_to_raw_response_wrapper(
            activities.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            activities.list,
        )
        self.retrieve_file = async_to_custom_raw_response_wrapper(
            activities.retrieve_file,
            AsyncBinaryAPIResponse,
        )


class ActivitiesResourceWithStreamingResponse:
    def __init__(self, activities: ActivitiesResource) -> None:
        self._activities = activities

        self.retrieve = to_streamed_response_wrapper(
            activities.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            activities.list,
        )
        self.retrieve_file = to_custom_streamed_response_wrapper(
            activities.retrieve_file,
            StreamedBinaryAPIResponse,
        )


class AsyncActivitiesResourceWithStreamingResponse:
    def __init__(self, activities: AsyncActivitiesResource) -> None:
        self._activities = activities

        self.retrieve = async_to_streamed_response_wrapper(
            activities.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            activities.list,
        )
        self.retrieve_file = async_to_custom_streamed_response_wrapper(
            activities.retrieve_file,
            AsyncStreamedBinaryAPIResponse,
        )
