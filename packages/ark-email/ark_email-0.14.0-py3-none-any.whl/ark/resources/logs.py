# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Literal

import httpx

from ..types import log_list_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform
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
from ..types.log_entry import LogEntry
from ..types.log_retrieve_response import LogRetrieveResponse

__all__ = ["LogsResource", "AsyncLogsResource"]


class LogsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> LogsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#accessing-raw-response-data-eg-headers
        """
        return LogsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LogsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#with_streaming_response
        """
        return LogsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        request_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LogRetrieveResponse:
        """
        Retrieve detailed information about a specific API request log, including the
        full request and response bodies.

        **Body decryption:** Request and response bodies are stored encrypted and
        automatically decrypted when retrieved. Bodies larger than 25KB are truncated at
        storage time with a `... [truncated]` marker.

        **Use cases:**

        - Debug a specific failed request
        - Review the exact payload sent/received
        - Share request details with support

        **Related endpoints:**

        - `GET /logs` - List logs with filters

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not request_id:
            raise ValueError(f"Expected a non-empty value for `request_id` but received {request_id!r}")
        return self._get(
            f"/logs/{request_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LogRetrieveResponse,
        )

    def list(
        self,
        *,
        credential_id: str | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        endpoint: str | Omit = omit,
        page: int | Omit = omit,
        per_page: int | Omit = omit,
        request_id: str | Omit = omit,
        start_date: Union[str, datetime] | Omit = omit,
        status: Literal["success", "error"] | Omit = omit,
        status_code: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncPageNumberPagination[LogEntry]:
        """
        Retrieve a paginated list of API request logs for debugging and monitoring.
        Results are ordered by timestamp, newest first.

        **Use cases:**

        - Debug integration issues by reviewing recent requests
        - Monitor error rates and response times
        - Audit API usage patterns

        **Filters:**

        - `status` - Filter by success or error category
        - `statusCode` - Filter by exact HTTP status code
        - `endpoint` - Filter by endpoint name (e.g., `emails.send`)
        - `credentialId` - Filter by API key
        - `startDate`/`endDate` - Filter by date range

        **Note:** Request and response bodies are only included when retrieving a single
        log entry with `GET /logs/{requestId}`.

        **Related endpoints:**

        - `GET /logs/{requestId}` - Get full log details with request/response bodies

        Args:
          credential_id: Filter by API credential ID

          end_date: Filter logs before this date (ISO 8601 format)

          endpoint: Filter by endpoint name

          page: Page number

          per_page: Results per page (max 100)

          request_id: Filter by request ID (partial match)

          start_date: Filter logs after this date (ISO 8601 format)

          status:
              Filter by status category:

              - `success` - Status codes < 400
              - `error` - Status codes >= 400

          status_code: Filter by exact HTTP status code (100-599)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/logs",
            page=SyncPageNumberPagination[LogEntry],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "credential_id": credential_id,
                        "end_date": end_date,
                        "endpoint": endpoint,
                        "page": page,
                        "per_page": per_page,
                        "request_id": request_id,
                        "start_date": start_date,
                        "status": status,
                        "status_code": status_code,
                    },
                    log_list_params.LogListParams,
                ),
            ),
            model=LogEntry,
        )


class AsyncLogsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncLogsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#accessing-raw-response-data-eg-headers
        """
        return AsyncLogsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLogsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#with_streaming_response
        """
        return AsyncLogsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        request_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LogRetrieveResponse:
        """
        Retrieve detailed information about a specific API request log, including the
        full request and response bodies.

        **Body decryption:** Request and response bodies are stored encrypted and
        automatically decrypted when retrieved. Bodies larger than 25KB are truncated at
        storage time with a `... [truncated]` marker.

        **Use cases:**

        - Debug a specific failed request
        - Review the exact payload sent/received
        - Share request details with support

        **Related endpoints:**

        - `GET /logs` - List logs with filters

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not request_id:
            raise ValueError(f"Expected a non-empty value for `request_id` but received {request_id!r}")
        return await self._get(
            f"/logs/{request_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LogRetrieveResponse,
        )

    def list(
        self,
        *,
        credential_id: str | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        endpoint: str | Omit = omit,
        page: int | Omit = omit,
        per_page: int | Omit = omit,
        request_id: str | Omit = omit,
        start_date: Union[str, datetime] | Omit = omit,
        status: Literal["success", "error"] | Omit = omit,
        status_code: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[LogEntry, AsyncPageNumberPagination[LogEntry]]:
        """
        Retrieve a paginated list of API request logs for debugging and monitoring.
        Results are ordered by timestamp, newest first.

        **Use cases:**

        - Debug integration issues by reviewing recent requests
        - Monitor error rates and response times
        - Audit API usage patterns

        **Filters:**

        - `status` - Filter by success or error category
        - `statusCode` - Filter by exact HTTP status code
        - `endpoint` - Filter by endpoint name (e.g., `emails.send`)
        - `credentialId` - Filter by API key
        - `startDate`/`endDate` - Filter by date range

        **Note:** Request and response bodies are only included when retrieving a single
        log entry with `GET /logs/{requestId}`.

        **Related endpoints:**

        - `GET /logs/{requestId}` - Get full log details with request/response bodies

        Args:
          credential_id: Filter by API credential ID

          end_date: Filter logs before this date (ISO 8601 format)

          endpoint: Filter by endpoint name

          page: Page number

          per_page: Results per page (max 100)

          request_id: Filter by request ID (partial match)

          start_date: Filter logs after this date (ISO 8601 format)

          status:
              Filter by status category:

              - `success` - Status codes < 400
              - `error` - Status codes >= 400

          status_code: Filter by exact HTTP status code (100-599)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/logs",
            page=AsyncPageNumberPagination[LogEntry],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "credential_id": credential_id,
                        "end_date": end_date,
                        "endpoint": endpoint,
                        "page": page,
                        "per_page": per_page,
                        "request_id": request_id,
                        "start_date": start_date,
                        "status": status,
                        "status_code": status_code,
                    },
                    log_list_params.LogListParams,
                ),
            ),
            model=LogEntry,
        )


class LogsResourceWithRawResponse:
    def __init__(self, logs: LogsResource) -> None:
        self._logs = logs

        self.retrieve = to_raw_response_wrapper(
            logs.retrieve,
        )
        self.list = to_raw_response_wrapper(
            logs.list,
        )


class AsyncLogsResourceWithRawResponse:
    def __init__(self, logs: AsyncLogsResource) -> None:
        self._logs = logs

        self.retrieve = async_to_raw_response_wrapper(
            logs.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            logs.list,
        )


class LogsResourceWithStreamingResponse:
    def __init__(self, logs: LogsResource) -> None:
        self._logs = logs

        self.retrieve = to_streamed_response_wrapper(
            logs.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            logs.list,
        )


class AsyncLogsResourceWithStreamingResponse:
    def __init__(self, logs: AsyncLogsResource) -> None:
        self._logs = logs

        self.retrieve = async_to_streamed_response_wrapper(
            logs.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            logs.list,
        )
