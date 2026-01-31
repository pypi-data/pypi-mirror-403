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
from ._exceptions import ArkError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import logs, usage, emails, domains, tracking, webhooks, suppressions
    from .resources.logs import LogsResource, AsyncLogsResource
    from .resources.usage import UsageResource, AsyncUsageResource
    from .resources.emails import EmailsResource, AsyncEmailsResource
    from .resources.domains import DomainsResource, AsyncDomainsResource
    from .resources.tracking import TrackingResource, AsyncTrackingResource
    from .resources.webhooks import WebhooksResource, AsyncWebhooksResource
    from .resources.suppressions import SuppressionsResource, AsyncSuppressionsResource

__all__ = ["Timeout", "Transport", "ProxiesTypes", "RequestOptions", "Ark", "AsyncArk", "Client", "AsyncClient"]


class Ark(SyncAPIClient):
    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
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
        """Construct a new synchronous Ark client instance.

        This automatically infers the `api_key` argument from the `ARK_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("ARK_API_KEY")
        if api_key is None:
            raise ArkError(
                "The api_key client option must be set either by passing api_key to the client or by setting the ARK_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("ARK_BASE_URL")
        if base_url is None:
            base_url = f"https://api.arkhq.io/v1"

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
    def emails(self) -> EmailsResource:
        from .resources.emails import EmailsResource

        return EmailsResource(self)

    @cached_property
    def domains(self) -> DomainsResource:
        from .resources.domains import DomainsResource

        return DomainsResource(self)

    @cached_property
    def suppressions(self) -> SuppressionsResource:
        from .resources.suppressions import SuppressionsResource

        return SuppressionsResource(self)

    @cached_property
    def webhooks(self) -> WebhooksResource:
        from .resources.webhooks import WebhooksResource

        return WebhooksResource(self)

    @cached_property
    def tracking(self) -> TrackingResource:
        from .resources.tracking import TrackingResource

        return TrackingResource(self)

    @cached_property
    def logs(self) -> LogsResource:
        from .resources.logs import LogsResource

        return LogsResource(self)

    @cached_property
    def usage(self) -> UsageResource:
        from .resources.usage import UsageResource

        return UsageResource(self)

    @cached_property
    def with_raw_response(self) -> ArkWithRawResponse:
        return ArkWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ArkWithStreamedResponse:
        return ArkWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
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
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

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


class AsyncArk(AsyncAPIClient):
    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
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
        """Construct a new async AsyncArk client instance.

        This automatically infers the `api_key` argument from the `ARK_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("ARK_API_KEY")
        if api_key is None:
            raise ArkError(
                "The api_key client option must be set either by passing api_key to the client or by setting the ARK_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("ARK_BASE_URL")
        if base_url is None:
            base_url = f"https://api.arkhq.io/v1"

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
    def emails(self) -> AsyncEmailsResource:
        from .resources.emails import AsyncEmailsResource

        return AsyncEmailsResource(self)

    @cached_property
    def domains(self) -> AsyncDomainsResource:
        from .resources.domains import AsyncDomainsResource

        return AsyncDomainsResource(self)

    @cached_property
    def suppressions(self) -> AsyncSuppressionsResource:
        from .resources.suppressions import AsyncSuppressionsResource

        return AsyncSuppressionsResource(self)

    @cached_property
    def webhooks(self) -> AsyncWebhooksResource:
        from .resources.webhooks import AsyncWebhooksResource

        return AsyncWebhooksResource(self)

    @cached_property
    def tracking(self) -> AsyncTrackingResource:
        from .resources.tracking import AsyncTrackingResource

        return AsyncTrackingResource(self)

    @cached_property
    def logs(self) -> AsyncLogsResource:
        from .resources.logs import AsyncLogsResource

        return AsyncLogsResource(self)

    @cached_property
    def usage(self) -> AsyncUsageResource:
        from .resources.usage import AsyncUsageResource

        return AsyncUsageResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncArkWithRawResponse:
        return AsyncArkWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncArkWithStreamedResponse:
        return AsyncArkWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
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
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

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


class ArkWithRawResponse:
    _client: Ark

    def __init__(self, client: Ark) -> None:
        self._client = client

    @cached_property
    def emails(self) -> emails.EmailsResourceWithRawResponse:
        from .resources.emails import EmailsResourceWithRawResponse

        return EmailsResourceWithRawResponse(self._client.emails)

    @cached_property
    def domains(self) -> domains.DomainsResourceWithRawResponse:
        from .resources.domains import DomainsResourceWithRawResponse

        return DomainsResourceWithRawResponse(self._client.domains)

    @cached_property
    def suppressions(self) -> suppressions.SuppressionsResourceWithRawResponse:
        from .resources.suppressions import SuppressionsResourceWithRawResponse

        return SuppressionsResourceWithRawResponse(self._client.suppressions)

    @cached_property
    def webhooks(self) -> webhooks.WebhooksResourceWithRawResponse:
        from .resources.webhooks import WebhooksResourceWithRawResponse

        return WebhooksResourceWithRawResponse(self._client.webhooks)

    @cached_property
    def tracking(self) -> tracking.TrackingResourceWithRawResponse:
        from .resources.tracking import TrackingResourceWithRawResponse

        return TrackingResourceWithRawResponse(self._client.tracking)

    @cached_property
    def logs(self) -> logs.LogsResourceWithRawResponse:
        from .resources.logs import LogsResourceWithRawResponse

        return LogsResourceWithRawResponse(self._client.logs)

    @cached_property
    def usage(self) -> usage.UsageResourceWithRawResponse:
        from .resources.usage import UsageResourceWithRawResponse

        return UsageResourceWithRawResponse(self._client.usage)


class AsyncArkWithRawResponse:
    _client: AsyncArk

    def __init__(self, client: AsyncArk) -> None:
        self._client = client

    @cached_property
    def emails(self) -> emails.AsyncEmailsResourceWithRawResponse:
        from .resources.emails import AsyncEmailsResourceWithRawResponse

        return AsyncEmailsResourceWithRawResponse(self._client.emails)

    @cached_property
    def domains(self) -> domains.AsyncDomainsResourceWithRawResponse:
        from .resources.domains import AsyncDomainsResourceWithRawResponse

        return AsyncDomainsResourceWithRawResponse(self._client.domains)

    @cached_property
    def suppressions(self) -> suppressions.AsyncSuppressionsResourceWithRawResponse:
        from .resources.suppressions import AsyncSuppressionsResourceWithRawResponse

        return AsyncSuppressionsResourceWithRawResponse(self._client.suppressions)

    @cached_property
    def webhooks(self) -> webhooks.AsyncWebhooksResourceWithRawResponse:
        from .resources.webhooks import AsyncWebhooksResourceWithRawResponse

        return AsyncWebhooksResourceWithRawResponse(self._client.webhooks)

    @cached_property
    def tracking(self) -> tracking.AsyncTrackingResourceWithRawResponse:
        from .resources.tracking import AsyncTrackingResourceWithRawResponse

        return AsyncTrackingResourceWithRawResponse(self._client.tracking)

    @cached_property
    def logs(self) -> logs.AsyncLogsResourceWithRawResponse:
        from .resources.logs import AsyncLogsResourceWithRawResponse

        return AsyncLogsResourceWithRawResponse(self._client.logs)

    @cached_property
    def usage(self) -> usage.AsyncUsageResourceWithRawResponse:
        from .resources.usage import AsyncUsageResourceWithRawResponse

        return AsyncUsageResourceWithRawResponse(self._client.usage)


class ArkWithStreamedResponse:
    _client: Ark

    def __init__(self, client: Ark) -> None:
        self._client = client

    @cached_property
    def emails(self) -> emails.EmailsResourceWithStreamingResponse:
        from .resources.emails import EmailsResourceWithStreamingResponse

        return EmailsResourceWithStreamingResponse(self._client.emails)

    @cached_property
    def domains(self) -> domains.DomainsResourceWithStreamingResponse:
        from .resources.domains import DomainsResourceWithStreamingResponse

        return DomainsResourceWithStreamingResponse(self._client.domains)

    @cached_property
    def suppressions(self) -> suppressions.SuppressionsResourceWithStreamingResponse:
        from .resources.suppressions import SuppressionsResourceWithStreamingResponse

        return SuppressionsResourceWithStreamingResponse(self._client.suppressions)

    @cached_property
    def webhooks(self) -> webhooks.WebhooksResourceWithStreamingResponse:
        from .resources.webhooks import WebhooksResourceWithStreamingResponse

        return WebhooksResourceWithStreamingResponse(self._client.webhooks)

    @cached_property
    def tracking(self) -> tracking.TrackingResourceWithStreamingResponse:
        from .resources.tracking import TrackingResourceWithStreamingResponse

        return TrackingResourceWithStreamingResponse(self._client.tracking)

    @cached_property
    def logs(self) -> logs.LogsResourceWithStreamingResponse:
        from .resources.logs import LogsResourceWithStreamingResponse

        return LogsResourceWithStreamingResponse(self._client.logs)

    @cached_property
    def usage(self) -> usage.UsageResourceWithStreamingResponse:
        from .resources.usage import UsageResourceWithStreamingResponse

        return UsageResourceWithStreamingResponse(self._client.usage)


class AsyncArkWithStreamedResponse:
    _client: AsyncArk

    def __init__(self, client: AsyncArk) -> None:
        self._client = client

    @cached_property
    def emails(self) -> emails.AsyncEmailsResourceWithStreamingResponse:
        from .resources.emails import AsyncEmailsResourceWithStreamingResponse

        return AsyncEmailsResourceWithStreamingResponse(self._client.emails)

    @cached_property
    def domains(self) -> domains.AsyncDomainsResourceWithStreamingResponse:
        from .resources.domains import AsyncDomainsResourceWithStreamingResponse

        return AsyncDomainsResourceWithStreamingResponse(self._client.domains)

    @cached_property
    def suppressions(self) -> suppressions.AsyncSuppressionsResourceWithStreamingResponse:
        from .resources.suppressions import AsyncSuppressionsResourceWithStreamingResponse

        return AsyncSuppressionsResourceWithStreamingResponse(self._client.suppressions)

    @cached_property
    def webhooks(self) -> webhooks.AsyncWebhooksResourceWithStreamingResponse:
        from .resources.webhooks import AsyncWebhooksResourceWithStreamingResponse

        return AsyncWebhooksResourceWithStreamingResponse(self._client.webhooks)

    @cached_property
    def tracking(self) -> tracking.AsyncTrackingResourceWithStreamingResponse:
        from .resources.tracking import AsyncTrackingResourceWithStreamingResponse

        return AsyncTrackingResourceWithStreamingResponse(self._client.tracking)

    @cached_property
    def logs(self) -> logs.AsyncLogsResourceWithStreamingResponse:
        from .resources.logs import AsyncLogsResourceWithStreamingResponse

        return AsyncLogsResourceWithStreamingResponse(self._client.logs)

    @cached_property
    def usage(self) -> usage.AsyncUsageResourceWithStreamingResponse:
        from .resources.usage import AsyncUsageResourceWithStreamingResponse

        return AsyncUsageResourceWithStreamingResponse(self._client.usage)


Client = Ark

AsyncClient = AsyncArk
