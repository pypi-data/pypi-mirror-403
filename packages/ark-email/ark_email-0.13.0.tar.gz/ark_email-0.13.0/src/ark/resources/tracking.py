# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import tracking_create_params, tracking_update_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.tracking_list_response import TrackingListResponse
from ..types.tracking_create_response import TrackingCreateResponse
from ..types.tracking_delete_response import TrackingDeleteResponse
from ..types.tracking_update_response import TrackingUpdateResponse
from ..types.tracking_verify_response import TrackingVerifyResponse
from ..types.tracking_retrieve_response import TrackingRetrieveResponse

__all__ = ["TrackingResource", "AsyncTrackingResource"]


class TrackingResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> TrackingResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#accessing-raw-response-data-eg-headers
        """
        return TrackingResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TrackingResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#with_streaming_response
        """
        return TrackingResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        domain_id: int,
        name: str,
        ssl_enabled: Optional[bool] | Omit = omit,
        track_clicks: Optional[bool] | Omit = omit,
        track_opens: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TrackingCreateResponse:
        """
        Create a new track domain for open/click tracking.

        After creation, you must configure a CNAME record pointing to the provided DNS
        value before tracking will work.

        Args:
          domain_id: ID of the sending domain to attach this track domain to

          name: Subdomain name (e.g., 'track' for track.yourdomain.com)

          ssl_enabled: Enable SSL for tracking URLs (accepts null, defaults to true)

          track_clicks: Enable click tracking (accepts null, defaults to true)

          track_opens: Enable open tracking (tracking pixel, accepts null, defaults to true)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/tracking",
            body=maybe_transform(
                {
                    "domain_id": domain_id,
                    "name": name,
                    "ssl_enabled": ssl_enabled,
                    "track_clicks": track_clicks,
                    "track_opens": track_opens,
                },
                tracking_create_params.TrackingCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TrackingCreateResponse,
        )

    def retrieve(
        self,
        tracking_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TrackingRetrieveResponse:
        """
        Get details of a specific track domain including DNS configuration

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not tracking_id:
            raise ValueError(f"Expected a non-empty value for `tracking_id` but received {tracking_id!r}")
        return self._get(
            f"/tracking/{tracking_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TrackingRetrieveResponse,
        )

    def update(
        self,
        tracking_id: str,
        *,
        excluded_click_domains: Optional[str] | Omit = omit,
        ssl_enabled: Optional[bool] | Omit = omit,
        track_clicks: Optional[bool] | Omit = omit,
        track_opens: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TrackingUpdateResponse:
        """
        Update track domain settings.

        Use this to:

        - Enable/disable click tracking
        - Enable/disable open tracking
        - Enable/disable SSL
        - Set excluded click domains

        Args:
          excluded_click_domains: Comma-separated list of domains to exclude from click tracking (accepts null)

          ssl_enabled: Enable or disable SSL for tracking URLs (accepts null)

          track_clicks: Enable or disable click tracking (accepts null)

          track_opens: Enable or disable open tracking (accepts null)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not tracking_id:
            raise ValueError(f"Expected a non-empty value for `tracking_id` but received {tracking_id!r}")
        return self._patch(
            f"/tracking/{tracking_id}",
            body=maybe_transform(
                {
                    "excluded_click_domains": excluded_click_domains,
                    "ssl_enabled": ssl_enabled,
                    "track_clicks": track_clicks,
                    "track_opens": track_opens,
                },
                tracking_update_params.TrackingUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TrackingUpdateResponse,
        )

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TrackingListResponse:
        """List all track domains configured for your server.

        Track domains enable open and
        click tracking for your emails.
        """
        return self._get(
            "/tracking",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TrackingListResponse,
        )

    def delete(
        self,
        tracking_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TrackingDeleteResponse:
        """Delete a track domain.

        This will disable tracking for any emails using this
        domain.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not tracking_id:
            raise ValueError(f"Expected a non-empty value for `tracking_id` but received {tracking_id!r}")
        return self._delete(
            f"/tracking/{tracking_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TrackingDeleteResponse,
        )

    def verify(
        self,
        tracking_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TrackingVerifyResponse:
        """
        Check DNS configuration for the track domain.

        The track domain requires a CNAME record to be configured before open and click
        tracking will work. Use this endpoint to verify the DNS is correctly set up.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not tracking_id:
            raise ValueError(f"Expected a non-empty value for `tracking_id` but received {tracking_id!r}")
        return self._post(
            f"/tracking/{tracking_id}/verify",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TrackingVerifyResponse,
        )


class AsyncTrackingResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncTrackingResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#accessing-raw-response-data-eg-headers
        """
        return AsyncTrackingResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTrackingResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#with_streaming_response
        """
        return AsyncTrackingResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        domain_id: int,
        name: str,
        ssl_enabled: Optional[bool] | Omit = omit,
        track_clicks: Optional[bool] | Omit = omit,
        track_opens: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TrackingCreateResponse:
        """
        Create a new track domain for open/click tracking.

        After creation, you must configure a CNAME record pointing to the provided DNS
        value before tracking will work.

        Args:
          domain_id: ID of the sending domain to attach this track domain to

          name: Subdomain name (e.g., 'track' for track.yourdomain.com)

          ssl_enabled: Enable SSL for tracking URLs (accepts null, defaults to true)

          track_clicks: Enable click tracking (accepts null, defaults to true)

          track_opens: Enable open tracking (tracking pixel, accepts null, defaults to true)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/tracking",
            body=await async_maybe_transform(
                {
                    "domain_id": domain_id,
                    "name": name,
                    "ssl_enabled": ssl_enabled,
                    "track_clicks": track_clicks,
                    "track_opens": track_opens,
                },
                tracking_create_params.TrackingCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TrackingCreateResponse,
        )

    async def retrieve(
        self,
        tracking_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TrackingRetrieveResponse:
        """
        Get details of a specific track domain including DNS configuration

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not tracking_id:
            raise ValueError(f"Expected a non-empty value for `tracking_id` but received {tracking_id!r}")
        return await self._get(
            f"/tracking/{tracking_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TrackingRetrieveResponse,
        )

    async def update(
        self,
        tracking_id: str,
        *,
        excluded_click_domains: Optional[str] | Omit = omit,
        ssl_enabled: Optional[bool] | Omit = omit,
        track_clicks: Optional[bool] | Omit = omit,
        track_opens: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TrackingUpdateResponse:
        """
        Update track domain settings.

        Use this to:

        - Enable/disable click tracking
        - Enable/disable open tracking
        - Enable/disable SSL
        - Set excluded click domains

        Args:
          excluded_click_domains: Comma-separated list of domains to exclude from click tracking (accepts null)

          ssl_enabled: Enable or disable SSL for tracking URLs (accepts null)

          track_clicks: Enable or disable click tracking (accepts null)

          track_opens: Enable or disable open tracking (accepts null)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not tracking_id:
            raise ValueError(f"Expected a non-empty value for `tracking_id` but received {tracking_id!r}")
        return await self._patch(
            f"/tracking/{tracking_id}",
            body=await async_maybe_transform(
                {
                    "excluded_click_domains": excluded_click_domains,
                    "ssl_enabled": ssl_enabled,
                    "track_clicks": track_clicks,
                    "track_opens": track_opens,
                },
                tracking_update_params.TrackingUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TrackingUpdateResponse,
        )

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TrackingListResponse:
        """List all track domains configured for your server.

        Track domains enable open and
        click tracking for your emails.
        """
        return await self._get(
            "/tracking",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TrackingListResponse,
        )

    async def delete(
        self,
        tracking_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TrackingDeleteResponse:
        """Delete a track domain.

        This will disable tracking for any emails using this
        domain.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not tracking_id:
            raise ValueError(f"Expected a non-empty value for `tracking_id` but received {tracking_id!r}")
        return await self._delete(
            f"/tracking/{tracking_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TrackingDeleteResponse,
        )

    async def verify(
        self,
        tracking_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TrackingVerifyResponse:
        """
        Check DNS configuration for the track domain.

        The track domain requires a CNAME record to be configured before open and click
        tracking will work. Use this endpoint to verify the DNS is correctly set up.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not tracking_id:
            raise ValueError(f"Expected a non-empty value for `tracking_id` but received {tracking_id!r}")
        return await self._post(
            f"/tracking/{tracking_id}/verify",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TrackingVerifyResponse,
        )


class TrackingResourceWithRawResponse:
    def __init__(self, tracking: TrackingResource) -> None:
        self._tracking = tracking

        self.create = to_raw_response_wrapper(
            tracking.create,
        )
        self.retrieve = to_raw_response_wrapper(
            tracking.retrieve,
        )
        self.update = to_raw_response_wrapper(
            tracking.update,
        )
        self.list = to_raw_response_wrapper(
            tracking.list,
        )
        self.delete = to_raw_response_wrapper(
            tracking.delete,
        )
        self.verify = to_raw_response_wrapper(
            tracking.verify,
        )


class AsyncTrackingResourceWithRawResponse:
    def __init__(self, tracking: AsyncTrackingResource) -> None:
        self._tracking = tracking

        self.create = async_to_raw_response_wrapper(
            tracking.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            tracking.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            tracking.update,
        )
        self.list = async_to_raw_response_wrapper(
            tracking.list,
        )
        self.delete = async_to_raw_response_wrapper(
            tracking.delete,
        )
        self.verify = async_to_raw_response_wrapper(
            tracking.verify,
        )


class TrackingResourceWithStreamingResponse:
    def __init__(self, tracking: TrackingResource) -> None:
        self._tracking = tracking

        self.create = to_streamed_response_wrapper(
            tracking.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            tracking.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            tracking.update,
        )
        self.list = to_streamed_response_wrapper(
            tracking.list,
        )
        self.delete = to_streamed_response_wrapper(
            tracking.delete,
        )
        self.verify = to_streamed_response_wrapper(
            tracking.verify,
        )


class AsyncTrackingResourceWithStreamingResponse:
    def __init__(self, tracking: AsyncTrackingResource) -> None:
        self._tracking = tracking

        self.create = async_to_streamed_response_wrapper(
            tracking.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            tracking.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            tracking.update,
        )
        self.list = async_to_streamed_response_wrapper(
            tracking.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            tracking.delete,
        )
        self.verify = async_to_streamed_response_wrapper(
            tracking.verify,
        )
