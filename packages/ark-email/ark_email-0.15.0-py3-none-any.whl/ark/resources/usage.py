# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .._types import Body, Query, Headers, NotGiven, not_given
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.usage_retrieve_response import UsageRetrieveResponse

__all__ = ["UsageResource", "AsyncUsageResource"]


class UsageResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> UsageResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#accessing-raw-response-data-eg-headers
        """
        return UsageResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> UsageResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#with_streaming_response
        """
        return UsageResourceWithStreamingResponse(self)

    def retrieve(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UsageRetrieveResponse:
        """
        Returns current usage and limit information for your account.

        This endpoint is designed for:

        - **AI agents/MCP servers:** Check constraints before planning batch operations
        - **Monitoring dashboards:** Display current usage status
        - **Rate limit awareness:** Know remaining capacity before making requests

        **Response includes:**

        - `rateLimit` - API request rate limit (requests per second)
        - `sendLimit` - Email sending limit (emails per hour)
        - `billing` - Credit balance and auto-recharge configuration

        **Notes:**

        - This request counts against your rate limit
        - `sendLimit` may be null if Postal is temporarily unavailable
        - `billing` is null if billing is not configured
        - Send limit resets at the top of each hour
        """
        return self._get(
            "/usage",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UsageRetrieveResponse,
        )


class AsyncUsageResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncUsageResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#accessing-raw-response-data-eg-headers
        """
        return AsyncUsageResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncUsageResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#with_streaming_response
        """
        return AsyncUsageResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UsageRetrieveResponse:
        """
        Returns current usage and limit information for your account.

        This endpoint is designed for:

        - **AI agents/MCP servers:** Check constraints before planning batch operations
        - **Monitoring dashboards:** Display current usage status
        - **Rate limit awareness:** Know remaining capacity before making requests

        **Response includes:**

        - `rateLimit` - API request rate limit (requests per second)
        - `sendLimit` - Email sending limit (emails per hour)
        - `billing` - Credit balance and auto-recharge configuration

        **Notes:**

        - This request counts against your rate limit
        - `sendLimit` may be null if Postal is temporarily unavailable
        - `billing` is null if billing is not configured
        - Send limit resets at the top of each hour
        """
        return await self._get(
            "/usage",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UsageRetrieveResponse,
        )


class UsageResourceWithRawResponse:
    def __init__(self, usage: UsageResource) -> None:
        self._usage = usage

        self.retrieve = to_raw_response_wrapper(
            usage.retrieve,
        )


class AsyncUsageResourceWithRawResponse:
    def __init__(self, usage: AsyncUsageResource) -> None:
        self._usage = usage

        self.retrieve = async_to_raw_response_wrapper(
            usage.retrieve,
        )


class UsageResourceWithStreamingResponse:
    def __init__(self, usage: UsageResource) -> None:
        self._usage = usage

        self.retrieve = to_streamed_response_wrapper(
            usage.retrieve,
        )


class AsyncUsageResourceWithStreamingResponse:
    def __init__(self, usage: AsyncUsageResource) -> None:
        self._usage = usage

        self.retrieve = async_to_streamed_response_wrapper(
            usage.retrieve,
        )
