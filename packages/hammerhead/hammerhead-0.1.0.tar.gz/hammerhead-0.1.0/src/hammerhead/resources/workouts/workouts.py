# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .file import (
    FileResource,
    AsyncFileResource,
    FileResourceWithRawResponse,
    AsyncFileResourceWithRawResponse,
    FileResourceWithStreamingResponse,
    AsyncFileResourceWithStreamingResponse,
)
from ..._types import Body, Query, Headers, NoneType, NotGiven, not_given
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options

__all__ = ["WorkoutsResource", "AsyncWorkoutsResource"]


class WorkoutsResource(SyncAPIResource):
    @cached_property
    def file(self) -> FileResource:
        return FileResource(self._client)

    @cached_property
    def with_raw_response(self) -> WorkoutsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/rchowell/hammerhead-python#accessing-raw-response-data-eg-headers
        """
        return WorkoutsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> WorkoutsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/rchowell/hammerhead-python#with_streaming_response
        """
        return WorkoutsResourceWithStreamingResponse(self)

    def delete(
        self,
        workout_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """Delete a workout by ID.

        Can only delete workouts created by your client.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workout_id:
            raise ValueError(f"Expected a non-empty value for `workout_id` but received {workout_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/workouts/{workout_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncWorkoutsResource(AsyncAPIResource):
    @cached_property
    def file(self) -> AsyncFileResource:
        return AsyncFileResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncWorkoutsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/rchowell/hammerhead-python#accessing-raw-response-data-eg-headers
        """
        return AsyncWorkoutsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWorkoutsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/rchowell/hammerhead-python#with_streaming_response
        """
        return AsyncWorkoutsResourceWithStreamingResponse(self)

    async def delete(
        self,
        workout_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """Delete a workout by ID.

        Can only delete workouts created by your client.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not workout_id:
            raise ValueError(f"Expected a non-empty value for `workout_id` but received {workout_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/workouts/{workout_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class WorkoutsResourceWithRawResponse:
    def __init__(self, workouts: WorkoutsResource) -> None:
        self._workouts = workouts

        self.delete = to_raw_response_wrapper(
            workouts.delete,
        )

    @cached_property
    def file(self) -> FileResourceWithRawResponse:
        return FileResourceWithRawResponse(self._workouts.file)


class AsyncWorkoutsResourceWithRawResponse:
    def __init__(self, workouts: AsyncWorkoutsResource) -> None:
        self._workouts = workouts

        self.delete = async_to_raw_response_wrapper(
            workouts.delete,
        )

    @cached_property
    def file(self) -> AsyncFileResourceWithRawResponse:
        return AsyncFileResourceWithRawResponse(self._workouts.file)


class WorkoutsResourceWithStreamingResponse:
    def __init__(self, workouts: WorkoutsResource) -> None:
        self._workouts = workouts

        self.delete = to_streamed_response_wrapper(
            workouts.delete,
        )

    @cached_property
    def file(self) -> FileResourceWithStreamingResponse:
        return FileResourceWithStreamingResponse(self._workouts.file)


class AsyncWorkoutsResourceWithStreamingResponse:
    def __init__(self, workouts: AsyncWorkoutsResource) -> None:
        self._workouts = workouts

        self.delete = async_to_streamed_response_wrapper(
            workouts.delete,
        )

    @cached_property
    def file(self) -> AsyncFileResourceWithStreamingResponse:
        return AsyncFileResourceWithStreamingResponse(self._workouts.file)
