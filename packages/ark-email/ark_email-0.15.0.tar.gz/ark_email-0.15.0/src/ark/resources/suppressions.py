# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional

import httpx

from ..types import suppression_list_params, suppression_create_params, suppression_bulk_create_params
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
from ..pagination import SyncPageNumberPagination, AsyncPageNumberPagination
from .._base_client import AsyncPaginator, make_request_options
from ..types.suppression_list_response import SuppressionListResponse
from ..types.suppression_create_response import SuppressionCreateResponse
from ..types.suppression_delete_response import SuppressionDeleteResponse
from ..types.suppression_retrieve_response import SuppressionRetrieveResponse
from ..types.suppression_bulk_create_response import SuppressionBulkCreateResponse

__all__ = ["SuppressionsResource", "AsyncSuppressionsResource"]


class SuppressionsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SuppressionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#accessing-raw-response-data-eg-headers
        """
        return SuppressionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SuppressionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#with_streaming_response
        """
        return SuppressionsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        address: str,
        reason: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SuppressionCreateResponse:
        """Add an email address to the suppression list.

        The address will not receive any
        emails until removed.

        Args:
          address: Email address to suppress

          reason: Reason for suppression (accepts null)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/suppressions",
            body=maybe_transform(
                {
                    "address": address,
                    "reason": reason,
                },
                suppression_create_params.SuppressionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SuppressionCreateResponse,
        )

    def retrieve(
        self,
        email: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SuppressionRetrieveResponse:
        """
        Check if a specific email address is on the suppression list

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not email:
            raise ValueError(f"Expected a non-empty value for `email` but received {email!r}")
        return self._get(
            f"/suppressions/{email}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SuppressionRetrieveResponse,
        )

    def list(
        self,
        *,
        page: int | Omit = omit,
        per_page: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncPageNumberPagination[SuppressionListResponse]:
        """Get all email addresses on the suppression list.

        These addresses will not
        receive any emails.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/suppressions",
            page=SyncPageNumberPagination[SuppressionListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "page": page,
                        "per_page": per_page,
                    },
                    suppression_list_params.SuppressionListParams,
                ),
            ),
            model=SuppressionListResponse,
        )

    def delete(
        self,
        email: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SuppressionDeleteResponse:
        """Remove an email address from the suppression list.

        The address will be able to
        receive emails again.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not email:
            raise ValueError(f"Expected a non-empty value for `email` but received {email!r}")
        return self._delete(
            f"/suppressions/{email}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SuppressionDeleteResponse,
        )

    def bulk_create(
        self,
        *,
        suppressions: Iterable[suppression_bulk_create_params.Suppression],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SuppressionBulkCreateResponse:
        """
        Add up to 1000 email addresses to the suppression list at once

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/suppressions/bulk",
            body=maybe_transform(
                {"suppressions": suppressions}, suppression_bulk_create_params.SuppressionBulkCreateParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SuppressionBulkCreateResponse,
        )


class AsyncSuppressionsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSuppressionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSuppressionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSuppressionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#with_streaming_response
        """
        return AsyncSuppressionsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        address: str,
        reason: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SuppressionCreateResponse:
        """Add an email address to the suppression list.

        The address will not receive any
        emails until removed.

        Args:
          address: Email address to suppress

          reason: Reason for suppression (accepts null)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/suppressions",
            body=await async_maybe_transform(
                {
                    "address": address,
                    "reason": reason,
                },
                suppression_create_params.SuppressionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SuppressionCreateResponse,
        )

    async def retrieve(
        self,
        email: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SuppressionRetrieveResponse:
        """
        Check if a specific email address is on the suppression list

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not email:
            raise ValueError(f"Expected a non-empty value for `email` but received {email!r}")
        return await self._get(
            f"/suppressions/{email}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SuppressionRetrieveResponse,
        )

    def list(
        self,
        *,
        page: int | Omit = omit,
        per_page: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[SuppressionListResponse, AsyncPageNumberPagination[SuppressionListResponse]]:
        """Get all email addresses on the suppression list.

        These addresses will not
        receive any emails.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/suppressions",
            page=AsyncPageNumberPagination[SuppressionListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "page": page,
                        "per_page": per_page,
                    },
                    suppression_list_params.SuppressionListParams,
                ),
            ),
            model=SuppressionListResponse,
        )

    async def delete(
        self,
        email: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SuppressionDeleteResponse:
        """Remove an email address from the suppression list.

        The address will be able to
        receive emails again.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not email:
            raise ValueError(f"Expected a non-empty value for `email` but received {email!r}")
        return await self._delete(
            f"/suppressions/{email}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SuppressionDeleteResponse,
        )

    async def bulk_create(
        self,
        *,
        suppressions: Iterable[suppression_bulk_create_params.Suppression],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SuppressionBulkCreateResponse:
        """
        Add up to 1000 email addresses to the suppression list at once

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/suppressions/bulk",
            body=await async_maybe_transform(
                {"suppressions": suppressions}, suppression_bulk_create_params.SuppressionBulkCreateParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SuppressionBulkCreateResponse,
        )


class SuppressionsResourceWithRawResponse:
    def __init__(self, suppressions: SuppressionsResource) -> None:
        self._suppressions = suppressions

        self.create = to_raw_response_wrapper(
            suppressions.create,
        )
        self.retrieve = to_raw_response_wrapper(
            suppressions.retrieve,
        )
        self.list = to_raw_response_wrapper(
            suppressions.list,
        )
        self.delete = to_raw_response_wrapper(
            suppressions.delete,
        )
        self.bulk_create = to_raw_response_wrapper(
            suppressions.bulk_create,
        )


class AsyncSuppressionsResourceWithRawResponse:
    def __init__(self, suppressions: AsyncSuppressionsResource) -> None:
        self._suppressions = suppressions

        self.create = async_to_raw_response_wrapper(
            suppressions.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            suppressions.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            suppressions.list,
        )
        self.delete = async_to_raw_response_wrapper(
            suppressions.delete,
        )
        self.bulk_create = async_to_raw_response_wrapper(
            suppressions.bulk_create,
        )


class SuppressionsResourceWithStreamingResponse:
    def __init__(self, suppressions: SuppressionsResource) -> None:
        self._suppressions = suppressions

        self.create = to_streamed_response_wrapper(
            suppressions.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            suppressions.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            suppressions.list,
        )
        self.delete = to_streamed_response_wrapper(
            suppressions.delete,
        )
        self.bulk_create = to_streamed_response_wrapper(
            suppressions.bulk_create,
        )


class AsyncSuppressionsResourceWithStreamingResponse:
    def __init__(self, suppressions: AsyncSuppressionsResource) -> None:
        self._suppressions = suppressions

        self.create = async_to_streamed_response_wrapper(
            suppressions.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            suppressions.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            suppressions.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            suppressions.delete,
        )
        self.bulk_create = async_to_streamed_response_wrapper(
            suppressions.bulk_create,
        )
