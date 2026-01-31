# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable, Optional
from typing_extensions import Literal

import httpx

from ..types import (
    email_list_params,
    email_send_params,
    email_retrieve_params,
    email_send_raw_params,
    email_send_batch_params,
)
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from .._utils import maybe_transform, strip_not_given, async_maybe_transform
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
from ..types.email_list_response import EmailListResponse
from ..types.email_send_response import EmailSendResponse
from ..types.email_retry_response import EmailRetryResponse
from ..types.email_retrieve_response import EmailRetrieveResponse
from ..types.email_send_raw_response import EmailSendRawResponse
from ..types.email_send_batch_response import EmailSendBatchResponse
from ..types.email_retrieve_deliveries_response import EmailRetrieveDeliveriesResponse

__all__ = ["EmailsResource", "AsyncEmailsResource"]


class EmailsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> EmailsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#accessing-raw-response-data-eg-headers
        """
        return EmailsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> EmailsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#with_streaming_response
        """
        return EmailsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        email_id: str,
        *,
        expand: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmailRetrieveResponse:
        """
        Retrieve detailed information about a specific email including delivery status,
        timestamps, and optionally the email content.

        Use the `expand` parameter to include additional data like the HTML/text body,
        headers, or delivery attempts.

        Args:
          expand:
              Comma-separated list of fields to include:

              - `full` - Include all expanded fields in a single request
              - `content` - HTML and plain text body
              - `headers` - Email headers
              - `deliveries` - Delivery attempt history
              - `activity` - Opens and clicks tracking data
              - `attachments` - File attachments with content (base64 encoded)
              - `raw` - Complete raw MIME message (base64 encoded)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not email_id:
            raise ValueError(f"Expected a non-empty value for `email_id` but received {email_id!r}")
        return self._get(
            f"/emails/{email_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"expand": expand}, email_retrieve_params.EmailRetrieveParams),
            ),
            cast_to=EmailRetrieveResponse,
        )

    def list(
        self,
        *,
        after: str | Omit = omit,
        before: str | Omit = omit,
        from_: str | Omit = omit,
        page: int | Omit = omit,
        per_page: int | Omit = omit,
        status: Literal["pending", "sent", "softfail", "hardfail", "bounced", "held"] | Omit = omit,
        tag: str | Omit = omit,
        to: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncPageNumberPagination[EmailListResponse]:
        """Retrieve a paginated list of sent emails.

        Results are ordered by send time,
        newest first.

        Use filters to narrow down results by status, recipient, sender, or tag.

        **Related endpoints:**

        - `GET /emails/{id}` - Get full details of a specific email
        - `POST /emails` - Send a new email

        Args:
          after: Return emails sent after this timestamp (Unix seconds or ISO 8601)

          before: Return emails sent before this timestamp

          from_: Filter by sender email address

          page: Page number (starts at 1)

          per_page: Results per page (max 100)

          status:
              Filter by delivery status:

              - `pending` - Email accepted, waiting to be processed
              - `sent` - Email transmitted to recipient's mail server
              - `softfail` - Temporary delivery failure, will retry
              - `hardfail` - Permanent delivery failure
              - `bounced` - Email bounced back
              - `held` - Held for manual review

          tag: Filter by tag

          to: Filter by recipient email address

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/emails",
            page=SyncPageNumberPagination[EmailListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "before": before,
                        "from_": from_,
                        "page": page,
                        "per_page": per_page,
                        "status": status,
                        "tag": tag,
                        "to": to,
                    },
                    email_list_params.EmailListParams,
                ),
            ),
            model=EmailListResponse,
        )

    def retrieve_deliveries(
        self,
        email_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmailRetrieveDeliveriesResponse:
        """
        Get the complete delivery history for an email, including SMTP response codes,
        timestamps, and current retry state.

        ## Response Fields

        ### Status

        The current status of the email:

        - `pending` - Awaiting first delivery attempt
        - `sent` - Successfully delivered to recipient server
        - `softfail` - Temporary failure, automatic retry scheduled
        - `hardfail` - Permanent failure, will not retry
        - `held` - Held for manual review
        - `bounced` - Bounced by recipient server

        ### Retry State

        When the email is in the delivery queue (`pending` or `softfail` status),
        `retryState` provides information about the retry schedule:

        - `attempt` - Current attempt number (0 = first attempt)
        - `maxAttempts` - Maximum attempts before hard-fail (typically 18)
        - `attemptsRemaining` - Attempts left before hard-fail
        - `nextRetryAt` - When the next retry is scheduled (Unix timestamp)
        - `processing` - Whether the email is currently being processed
        - `manual` - Whether this was triggered by a manual retry

        When the email has finished processing (`sent`, `hardfail`, `held`, `bounced`),
        `retryState` is `null`.

        ### Can Retry Manually

        Indicates whether you can call `POST /emails/{emailId}/retry` to manually retry
        the email. This is `true` when the raw message content is still available (not
        expired due to retention policy).

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not email_id:
            raise ValueError(f"Expected a non-empty value for `email_id` but received {email_id!r}")
        return self._get(
            f"/emails/{email_id}/deliveries",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmailRetrieveDeliveriesResponse,
        )

    def retry(
        self,
        email_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmailRetryResponse:
        """Retry delivery of a failed or soft-bounced email.

        Creates a new delivery
        attempt.

        Only works for emails that have failed or are in a retryable state.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not email_id:
            raise ValueError(f"Expected a non-empty value for `email_id` but received {email_id!r}")
        return self._post(
            f"/emails/{email_id}/retry",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmailRetryResponse,
        )

    def send(
        self,
        *,
        from_: str,
        subject: str,
        to: SequenceNotStr[str],
        attachments: Optional[Iterable[email_send_params.Attachment]] | Omit = omit,
        bcc: Optional[SequenceNotStr[str]] | Omit = omit,
        cc: Optional[SequenceNotStr[str]] | Omit = omit,
        headers: Optional[Dict[str, str]] | Omit = omit,
        html: Optional[str] | Omit = omit,
        metadata: Optional[Dict[str, str]] | Omit = omit,
        reply_to: Optional[str] | Omit = omit,
        tag: Optional[str] | Omit = omit,
        text: Optional[str] | Omit = omit,
        idempotency_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmailSendResponse:
        """Send a single email message.

        The email is accepted for immediate delivery and
        typically delivered within seconds.

        **Example use case:** Send a password reset email to a user.

        **Required fields:** `from`, `to`, `subject`, and either `html` or `text`

        **Idempotency:** Supports `Idempotency-Key` header for safe retries.

        **Related endpoints:**

        - `GET /emails/{id}` - Track delivery status
        - `GET /emails/{id}/deliveries` - View delivery attempts
        - `POST /emails/{id}/retry` - Retry failed delivery

        Args:
          from_: Sender email address. Must be from a verified domain OR use sandbox mode.

              **Supported formats:**

              - Email only: `hello@yourdomain.com`
              - With display name: `Acme <hello@yourdomain.com>`
              - With quoted name: `"Acme Support" <support@yourdomain.com>`

              The domain portion must match a verified sending domain in your account.

              **Sandbox mode:** Use `sandbox@arkhq.io` to send test emails without domain
              verification. Sandbox emails can only be sent to organization members and are
              limited to 10 per day.

          subject: Email subject line

          to: Recipient email addresses (max 50)

          attachments: File attachments (accepts null)

          bcc: BCC recipients (accepts null)

          cc: CC recipients (accepts null)

          headers: Custom email headers (accepts null)

          html: HTML body content (accepts null). Maximum 5MB (5,242,880 characters). Combined
              with attachments, the total message must not exceed 14MB.

          metadata: Custom key-value pairs attached to an email for webhook correlation.

              When you send an email with metadata, these key-value pairs are:

              - **Stored** with the message
              - **Returned** in all webhook event payloads (MessageSent, MessageBounced, etc.)
              - **Never visible** to email recipients

              This is useful for correlating webhook events with your internal systems (e.g.,
              user IDs, order IDs, campaign identifiers).

              **Validation Rules:**

              - Maximum 10 keys per email
              - Keys: 1-40 characters, must start with a letter, only alphanumeric and
                underscores (`^[a-zA-Z][a-zA-Z0-9_]*$`)
              - Values: 1-500 characters, no control characters (newlines, tabs, etc.)
              - Total size: 4KB maximum (JSON-encoded)

          reply_to: Reply-to address (accepts null)

          tag: Tag for categorization and filtering (accepts null)

          text: Plain text body (accepts null, auto-generated from HTML if not provided).
              Maximum 5MB (5,242,880 characters).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"Idempotency-Key": idempotency_key}), **(extra_headers or {})}
        return self._post(
            "/emails",
            body=maybe_transform(
                {
                    "from_": from_,
                    "subject": subject,
                    "to": to,
                    "attachments": attachments,
                    "bcc": bcc,
                    "cc": cc,
                    "headers": headers,
                    "html": html,
                    "metadata": metadata,
                    "reply_to": reply_to,
                    "tag": tag,
                    "text": text,
                },
                email_send_params.EmailSendParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmailSendResponse,
        )

    def send_batch(
        self,
        *,
        emails: Iterable[email_send_batch_params.Email],
        from_: str,
        idempotency_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmailSendBatchResponse:
        """Send up to 100 emails in a single request.

        Useful for sending personalized
        emails to multiple recipients efficiently.

        Each email in the batch can have different content and recipients. Failed emails
        don't affect other emails in the batch.

        **Idempotency:** Supports `Idempotency-Key` header for safe retries.

        Args:
          from_: Sender email for all messages

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"Idempotency-Key": idempotency_key}), **(extra_headers or {})}
        return self._post(
            "/emails/batch",
            body=maybe_transform(
                {
                    "emails": emails,
                    "from_": from_,
                },
                email_send_batch_params.EmailSendBatchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmailSendBatchResponse,
        )

    def send_raw(
        self,
        *,
        from_: str,
        raw_message: str,
        to: SequenceNotStr[str],
        bounce: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmailSendRawResponse:
        """Send a pre-formatted RFC 2822 MIME message.

        Use this for advanced use cases or
        when migrating from systems that generate raw email content.

        **Important:** The `rawMessage` field must be base64-encoded. Your raw MIME
        message (with headers like From, To, Subject, Content-Type, followed by a blank
        line and the body) must be encoded to base64 before sending.

        Args:
          from_: Sender email address. Must be from a verified domain.

              **Supported formats:**

              - Email only: `hello@yourdomain.com`
              - With display name: `Acme <hello@yourdomain.com>`
              - With quoted name: `"Acme Support" <support@yourdomain.com>`

              The domain portion must match a verified sending domain in your account.

          raw_message: Base64-encoded RFC 2822 MIME message.

              **You must base64-encode your raw email before sending.** The raw email should
              include headers (From, To, Subject, Content-Type, etc.) followed by a blank line
              and the message body.

          to: Recipient email addresses

          bounce: Whether this is a bounce message (accepts null)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/emails/raw",
            body=maybe_transform(
                {
                    "from_": from_,
                    "raw_message": raw_message,
                    "to": to,
                    "bounce": bounce,
                },
                email_send_raw_params.EmailSendRawParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmailSendRawResponse,
        )


class AsyncEmailsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncEmailsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#accessing-raw-response-data-eg-headers
        """
        return AsyncEmailsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncEmailsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#with_streaming_response
        """
        return AsyncEmailsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        email_id: str,
        *,
        expand: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmailRetrieveResponse:
        """
        Retrieve detailed information about a specific email including delivery status,
        timestamps, and optionally the email content.

        Use the `expand` parameter to include additional data like the HTML/text body,
        headers, or delivery attempts.

        Args:
          expand:
              Comma-separated list of fields to include:

              - `full` - Include all expanded fields in a single request
              - `content` - HTML and plain text body
              - `headers` - Email headers
              - `deliveries` - Delivery attempt history
              - `activity` - Opens and clicks tracking data
              - `attachments` - File attachments with content (base64 encoded)
              - `raw` - Complete raw MIME message (base64 encoded)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not email_id:
            raise ValueError(f"Expected a non-empty value for `email_id` but received {email_id!r}")
        return await self._get(
            f"/emails/{email_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"expand": expand}, email_retrieve_params.EmailRetrieveParams),
            ),
            cast_to=EmailRetrieveResponse,
        )

    def list(
        self,
        *,
        after: str | Omit = omit,
        before: str | Omit = omit,
        from_: str | Omit = omit,
        page: int | Omit = omit,
        per_page: int | Omit = omit,
        status: Literal["pending", "sent", "softfail", "hardfail", "bounced", "held"] | Omit = omit,
        tag: str | Omit = omit,
        to: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[EmailListResponse, AsyncPageNumberPagination[EmailListResponse]]:
        """Retrieve a paginated list of sent emails.

        Results are ordered by send time,
        newest first.

        Use filters to narrow down results by status, recipient, sender, or tag.

        **Related endpoints:**

        - `GET /emails/{id}` - Get full details of a specific email
        - `POST /emails` - Send a new email

        Args:
          after: Return emails sent after this timestamp (Unix seconds or ISO 8601)

          before: Return emails sent before this timestamp

          from_: Filter by sender email address

          page: Page number (starts at 1)

          per_page: Results per page (max 100)

          status:
              Filter by delivery status:

              - `pending` - Email accepted, waiting to be processed
              - `sent` - Email transmitted to recipient's mail server
              - `softfail` - Temporary delivery failure, will retry
              - `hardfail` - Permanent delivery failure
              - `bounced` - Email bounced back
              - `held` - Held for manual review

          tag: Filter by tag

          to: Filter by recipient email address

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/emails",
            page=AsyncPageNumberPagination[EmailListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "before": before,
                        "from_": from_,
                        "page": page,
                        "per_page": per_page,
                        "status": status,
                        "tag": tag,
                        "to": to,
                    },
                    email_list_params.EmailListParams,
                ),
            ),
            model=EmailListResponse,
        )

    async def retrieve_deliveries(
        self,
        email_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmailRetrieveDeliveriesResponse:
        """
        Get the complete delivery history for an email, including SMTP response codes,
        timestamps, and current retry state.

        ## Response Fields

        ### Status

        The current status of the email:

        - `pending` - Awaiting first delivery attempt
        - `sent` - Successfully delivered to recipient server
        - `softfail` - Temporary failure, automatic retry scheduled
        - `hardfail` - Permanent failure, will not retry
        - `held` - Held for manual review
        - `bounced` - Bounced by recipient server

        ### Retry State

        When the email is in the delivery queue (`pending` or `softfail` status),
        `retryState` provides information about the retry schedule:

        - `attempt` - Current attempt number (0 = first attempt)
        - `maxAttempts` - Maximum attempts before hard-fail (typically 18)
        - `attemptsRemaining` - Attempts left before hard-fail
        - `nextRetryAt` - When the next retry is scheduled (Unix timestamp)
        - `processing` - Whether the email is currently being processed
        - `manual` - Whether this was triggered by a manual retry

        When the email has finished processing (`sent`, `hardfail`, `held`, `bounced`),
        `retryState` is `null`.

        ### Can Retry Manually

        Indicates whether you can call `POST /emails/{emailId}/retry` to manually retry
        the email. This is `true` when the raw message content is still available (not
        expired due to retention policy).

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not email_id:
            raise ValueError(f"Expected a non-empty value for `email_id` but received {email_id!r}")
        return await self._get(
            f"/emails/{email_id}/deliveries",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmailRetrieveDeliveriesResponse,
        )

    async def retry(
        self,
        email_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmailRetryResponse:
        """Retry delivery of a failed or soft-bounced email.

        Creates a new delivery
        attempt.

        Only works for emails that have failed or are in a retryable state.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not email_id:
            raise ValueError(f"Expected a non-empty value for `email_id` but received {email_id!r}")
        return await self._post(
            f"/emails/{email_id}/retry",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmailRetryResponse,
        )

    async def send(
        self,
        *,
        from_: str,
        subject: str,
        to: SequenceNotStr[str],
        attachments: Optional[Iterable[email_send_params.Attachment]] | Omit = omit,
        bcc: Optional[SequenceNotStr[str]] | Omit = omit,
        cc: Optional[SequenceNotStr[str]] | Omit = omit,
        headers: Optional[Dict[str, str]] | Omit = omit,
        html: Optional[str] | Omit = omit,
        metadata: Optional[Dict[str, str]] | Omit = omit,
        reply_to: Optional[str] | Omit = omit,
        tag: Optional[str] | Omit = omit,
        text: Optional[str] | Omit = omit,
        idempotency_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmailSendResponse:
        """Send a single email message.

        The email is accepted for immediate delivery and
        typically delivered within seconds.

        **Example use case:** Send a password reset email to a user.

        **Required fields:** `from`, `to`, `subject`, and either `html` or `text`

        **Idempotency:** Supports `Idempotency-Key` header for safe retries.

        **Related endpoints:**

        - `GET /emails/{id}` - Track delivery status
        - `GET /emails/{id}/deliveries` - View delivery attempts
        - `POST /emails/{id}/retry` - Retry failed delivery

        Args:
          from_: Sender email address. Must be from a verified domain OR use sandbox mode.

              **Supported formats:**

              - Email only: `hello@yourdomain.com`
              - With display name: `Acme <hello@yourdomain.com>`
              - With quoted name: `"Acme Support" <support@yourdomain.com>`

              The domain portion must match a verified sending domain in your account.

              **Sandbox mode:** Use `sandbox@arkhq.io` to send test emails without domain
              verification. Sandbox emails can only be sent to organization members and are
              limited to 10 per day.

          subject: Email subject line

          to: Recipient email addresses (max 50)

          attachments: File attachments (accepts null)

          bcc: BCC recipients (accepts null)

          cc: CC recipients (accepts null)

          headers: Custom email headers (accepts null)

          html: HTML body content (accepts null). Maximum 5MB (5,242,880 characters). Combined
              with attachments, the total message must not exceed 14MB.

          metadata: Custom key-value pairs attached to an email for webhook correlation.

              When you send an email with metadata, these key-value pairs are:

              - **Stored** with the message
              - **Returned** in all webhook event payloads (MessageSent, MessageBounced, etc.)
              - **Never visible** to email recipients

              This is useful for correlating webhook events with your internal systems (e.g.,
              user IDs, order IDs, campaign identifiers).

              **Validation Rules:**

              - Maximum 10 keys per email
              - Keys: 1-40 characters, must start with a letter, only alphanumeric and
                underscores (`^[a-zA-Z][a-zA-Z0-9_]*$`)
              - Values: 1-500 characters, no control characters (newlines, tabs, etc.)
              - Total size: 4KB maximum (JSON-encoded)

          reply_to: Reply-to address (accepts null)

          tag: Tag for categorization and filtering (accepts null)

          text: Plain text body (accepts null, auto-generated from HTML if not provided).
              Maximum 5MB (5,242,880 characters).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"Idempotency-Key": idempotency_key}), **(extra_headers or {})}
        return await self._post(
            "/emails",
            body=await async_maybe_transform(
                {
                    "from_": from_,
                    "subject": subject,
                    "to": to,
                    "attachments": attachments,
                    "bcc": bcc,
                    "cc": cc,
                    "headers": headers,
                    "html": html,
                    "metadata": metadata,
                    "reply_to": reply_to,
                    "tag": tag,
                    "text": text,
                },
                email_send_params.EmailSendParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmailSendResponse,
        )

    async def send_batch(
        self,
        *,
        emails: Iterable[email_send_batch_params.Email],
        from_: str,
        idempotency_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmailSendBatchResponse:
        """Send up to 100 emails in a single request.

        Useful for sending personalized
        emails to multiple recipients efficiently.

        Each email in the batch can have different content and recipients. Failed emails
        don't affect other emails in the batch.

        **Idempotency:** Supports `Idempotency-Key` header for safe retries.

        Args:
          from_: Sender email for all messages

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"Idempotency-Key": idempotency_key}), **(extra_headers or {})}
        return await self._post(
            "/emails/batch",
            body=await async_maybe_transform(
                {
                    "emails": emails,
                    "from_": from_,
                },
                email_send_batch_params.EmailSendBatchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmailSendBatchResponse,
        )

    async def send_raw(
        self,
        *,
        from_: str,
        raw_message: str,
        to: SequenceNotStr[str],
        bounce: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EmailSendRawResponse:
        """Send a pre-formatted RFC 2822 MIME message.

        Use this for advanced use cases or
        when migrating from systems that generate raw email content.

        **Important:** The `rawMessage` field must be base64-encoded. Your raw MIME
        message (with headers like From, To, Subject, Content-Type, followed by a blank
        line and the body) must be encoded to base64 before sending.

        Args:
          from_: Sender email address. Must be from a verified domain.

              **Supported formats:**

              - Email only: `hello@yourdomain.com`
              - With display name: `Acme <hello@yourdomain.com>`
              - With quoted name: `"Acme Support" <support@yourdomain.com>`

              The domain portion must match a verified sending domain in your account.

          raw_message: Base64-encoded RFC 2822 MIME message.

              **You must base64-encode your raw email before sending.** The raw email should
              include headers (From, To, Subject, Content-Type, etc.) followed by a blank line
              and the message body.

          to: Recipient email addresses

          bounce: Whether this is a bounce message (accepts null)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/emails/raw",
            body=await async_maybe_transform(
                {
                    "from_": from_,
                    "raw_message": raw_message,
                    "to": to,
                    "bounce": bounce,
                },
                email_send_raw_params.EmailSendRawParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EmailSendRawResponse,
        )


class EmailsResourceWithRawResponse:
    def __init__(self, emails: EmailsResource) -> None:
        self._emails = emails

        self.retrieve = to_raw_response_wrapper(
            emails.retrieve,
        )
        self.list = to_raw_response_wrapper(
            emails.list,
        )
        self.retrieve_deliveries = to_raw_response_wrapper(
            emails.retrieve_deliveries,
        )
        self.retry = to_raw_response_wrapper(
            emails.retry,
        )
        self.send = to_raw_response_wrapper(
            emails.send,
        )
        self.send_batch = to_raw_response_wrapper(
            emails.send_batch,
        )
        self.send_raw = to_raw_response_wrapper(
            emails.send_raw,
        )


class AsyncEmailsResourceWithRawResponse:
    def __init__(self, emails: AsyncEmailsResource) -> None:
        self._emails = emails

        self.retrieve = async_to_raw_response_wrapper(
            emails.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            emails.list,
        )
        self.retrieve_deliveries = async_to_raw_response_wrapper(
            emails.retrieve_deliveries,
        )
        self.retry = async_to_raw_response_wrapper(
            emails.retry,
        )
        self.send = async_to_raw_response_wrapper(
            emails.send,
        )
        self.send_batch = async_to_raw_response_wrapper(
            emails.send_batch,
        )
        self.send_raw = async_to_raw_response_wrapper(
            emails.send_raw,
        )


class EmailsResourceWithStreamingResponse:
    def __init__(self, emails: EmailsResource) -> None:
        self._emails = emails

        self.retrieve = to_streamed_response_wrapper(
            emails.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            emails.list,
        )
        self.retrieve_deliveries = to_streamed_response_wrapper(
            emails.retrieve_deliveries,
        )
        self.retry = to_streamed_response_wrapper(
            emails.retry,
        )
        self.send = to_streamed_response_wrapper(
            emails.send,
        )
        self.send_batch = to_streamed_response_wrapper(
            emails.send_batch,
        )
        self.send_raw = to_streamed_response_wrapper(
            emails.send_raw,
        )


class AsyncEmailsResourceWithStreamingResponse:
    def __init__(self, emails: AsyncEmailsResource) -> None:
        self._emails = emails

        self.retrieve = async_to_streamed_response_wrapper(
            emails.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            emails.list,
        )
        self.retrieve_deliveries = async_to_streamed_response_wrapper(
            emails.retrieve_deliveries,
        )
        self.retry = async_to_streamed_response_wrapper(
            emails.retry,
        )
        self.send = async_to_streamed_response_wrapper(
            emails.send,
        )
        self.send_batch = async_to_streamed_response_wrapper(
            emails.send_batch,
        )
        self.send_raw = async_to_streamed_response_wrapper(
            emails.send_raw,
        )
