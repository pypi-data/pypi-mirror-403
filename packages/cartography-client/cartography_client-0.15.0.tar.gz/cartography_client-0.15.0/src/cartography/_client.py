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
from ._exceptions import APIStatusError, CartographyError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import crawl, health, scrape, api_info, download, workflows
    from .resources.crawl import CrawlResource, AsyncCrawlResource
    from .resources.health import HealthResource, AsyncHealthResource
    from .resources.scrape import ScrapeResource, AsyncScrapeResource
    from .resources.api_info import APIInfoResource, AsyncAPIInfoResource
    from .resources.download import DownloadResource, AsyncDownloadResource
    from .resources.workflows.workflows import WorkflowsResource, AsyncWorkflowsResource

__all__ = [
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "Cartography",
    "AsyncCartography",
    "Client",
    "AsyncClient",
]


class Cartography(SyncAPIClient):
    # client options
    bearer_token: str

    def __init__(
        self,
        *,
        bearer_token: str | None = None,
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
        """Construct a new synchronous Cartography client instance.

        This automatically infers the `bearer_token` argument from the `CARTOGRAPHY_BEARER_TOKEN` environment variable if it is not provided.
        """
        if bearer_token is None:
            bearer_token = os.environ.get("CARTOGRAPHY_BEARER_TOKEN")
        if bearer_token is None:
            raise CartographyError(
                "The bearer_token client option must be set either by passing bearer_token to the client or by setting the CARTOGRAPHY_BEARER_TOKEN environment variable"
            )
        self.bearer_token = bearer_token

        if base_url is None:
            base_url = os.environ.get("CARTOGRAPHY_BASE_URL")
        if base_url is None:
            base_url = f"https://cartography.evrim.ai"

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
    def health(self) -> HealthResource:
        from .resources.health import HealthResource

        return HealthResource(self)

    @cached_property
    def api_info(self) -> APIInfoResource:
        from .resources.api_info import APIInfoResource

        return APIInfoResource(self)

    @cached_property
    def scrape(self) -> ScrapeResource:
        from .resources.scrape import ScrapeResource

        return ScrapeResource(self)

    @cached_property
    def crawl(self) -> CrawlResource:
        from .resources.crawl import CrawlResource

        return CrawlResource(self)

    @cached_property
    def download(self) -> DownloadResource:
        from .resources.download import DownloadResource

        return DownloadResource(self)

    @cached_property
    def workflows(self) -> WorkflowsResource:
        from .resources.workflows import WorkflowsResource

        return WorkflowsResource(self)

    @cached_property
    def with_raw_response(self) -> CartographyWithRawResponse:
        return CartographyWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CartographyWithStreamedResponse:
        return CartographyWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        bearer_token = self.bearer_token
        return {"Authorization": f"Bearer {bearer_token}"}

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
        bearer_token: str | None = None,
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
            bearer_token=bearer_token or self.bearer_token,
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


class AsyncCartography(AsyncAPIClient):
    # client options
    bearer_token: str

    def __init__(
        self,
        *,
        bearer_token: str | None = None,
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
        """Construct a new async AsyncCartography client instance.

        This automatically infers the `bearer_token` argument from the `CARTOGRAPHY_BEARER_TOKEN` environment variable if it is not provided.
        """
        if bearer_token is None:
            bearer_token = os.environ.get("CARTOGRAPHY_BEARER_TOKEN")
        if bearer_token is None:
            raise CartographyError(
                "The bearer_token client option must be set either by passing bearer_token to the client or by setting the CARTOGRAPHY_BEARER_TOKEN environment variable"
            )
        self.bearer_token = bearer_token

        if base_url is None:
            base_url = os.environ.get("CARTOGRAPHY_BASE_URL")
        if base_url is None:
            base_url = f"https://cartography.evrim.ai"

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
    def health(self) -> AsyncHealthResource:
        from .resources.health import AsyncHealthResource

        return AsyncHealthResource(self)

    @cached_property
    def api_info(self) -> AsyncAPIInfoResource:
        from .resources.api_info import AsyncAPIInfoResource

        return AsyncAPIInfoResource(self)

    @cached_property
    def scrape(self) -> AsyncScrapeResource:
        from .resources.scrape import AsyncScrapeResource

        return AsyncScrapeResource(self)

    @cached_property
    def crawl(self) -> AsyncCrawlResource:
        from .resources.crawl import AsyncCrawlResource

        return AsyncCrawlResource(self)

    @cached_property
    def download(self) -> AsyncDownloadResource:
        from .resources.download import AsyncDownloadResource

        return AsyncDownloadResource(self)

    @cached_property
    def workflows(self) -> AsyncWorkflowsResource:
        from .resources.workflows import AsyncWorkflowsResource

        return AsyncWorkflowsResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncCartographyWithRawResponse:
        return AsyncCartographyWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCartographyWithStreamedResponse:
        return AsyncCartographyWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        bearer_token = self.bearer_token
        return {"Authorization": f"Bearer {bearer_token}"}

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
        bearer_token: str | None = None,
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
            bearer_token=bearer_token or self.bearer_token,
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


class CartographyWithRawResponse:
    _client: Cartography

    def __init__(self, client: Cartography) -> None:
        self._client = client

    @cached_property
    def health(self) -> health.HealthResourceWithRawResponse:
        from .resources.health import HealthResourceWithRawResponse

        return HealthResourceWithRawResponse(self._client.health)

    @cached_property
    def api_info(self) -> api_info.APIInfoResourceWithRawResponse:
        from .resources.api_info import APIInfoResourceWithRawResponse

        return APIInfoResourceWithRawResponse(self._client.api_info)

    @cached_property
    def scrape(self) -> scrape.ScrapeResourceWithRawResponse:
        from .resources.scrape import ScrapeResourceWithRawResponse

        return ScrapeResourceWithRawResponse(self._client.scrape)

    @cached_property
    def crawl(self) -> crawl.CrawlResourceWithRawResponse:
        from .resources.crawl import CrawlResourceWithRawResponse

        return CrawlResourceWithRawResponse(self._client.crawl)

    @cached_property
    def download(self) -> download.DownloadResourceWithRawResponse:
        from .resources.download import DownloadResourceWithRawResponse

        return DownloadResourceWithRawResponse(self._client.download)

    @cached_property
    def workflows(self) -> workflows.WorkflowsResourceWithRawResponse:
        from .resources.workflows import WorkflowsResourceWithRawResponse

        return WorkflowsResourceWithRawResponse(self._client.workflows)


class AsyncCartographyWithRawResponse:
    _client: AsyncCartography

    def __init__(self, client: AsyncCartography) -> None:
        self._client = client

    @cached_property
    def health(self) -> health.AsyncHealthResourceWithRawResponse:
        from .resources.health import AsyncHealthResourceWithRawResponse

        return AsyncHealthResourceWithRawResponse(self._client.health)

    @cached_property
    def api_info(self) -> api_info.AsyncAPIInfoResourceWithRawResponse:
        from .resources.api_info import AsyncAPIInfoResourceWithRawResponse

        return AsyncAPIInfoResourceWithRawResponse(self._client.api_info)

    @cached_property
    def scrape(self) -> scrape.AsyncScrapeResourceWithRawResponse:
        from .resources.scrape import AsyncScrapeResourceWithRawResponse

        return AsyncScrapeResourceWithRawResponse(self._client.scrape)

    @cached_property
    def crawl(self) -> crawl.AsyncCrawlResourceWithRawResponse:
        from .resources.crawl import AsyncCrawlResourceWithRawResponse

        return AsyncCrawlResourceWithRawResponse(self._client.crawl)

    @cached_property
    def download(self) -> download.AsyncDownloadResourceWithRawResponse:
        from .resources.download import AsyncDownloadResourceWithRawResponse

        return AsyncDownloadResourceWithRawResponse(self._client.download)

    @cached_property
    def workflows(self) -> workflows.AsyncWorkflowsResourceWithRawResponse:
        from .resources.workflows import AsyncWorkflowsResourceWithRawResponse

        return AsyncWorkflowsResourceWithRawResponse(self._client.workflows)


class CartographyWithStreamedResponse:
    _client: Cartography

    def __init__(self, client: Cartography) -> None:
        self._client = client

    @cached_property
    def health(self) -> health.HealthResourceWithStreamingResponse:
        from .resources.health import HealthResourceWithStreamingResponse

        return HealthResourceWithStreamingResponse(self._client.health)

    @cached_property
    def api_info(self) -> api_info.APIInfoResourceWithStreamingResponse:
        from .resources.api_info import APIInfoResourceWithStreamingResponse

        return APIInfoResourceWithStreamingResponse(self._client.api_info)

    @cached_property
    def scrape(self) -> scrape.ScrapeResourceWithStreamingResponse:
        from .resources.scrape import ScrapeResourceWithStreamingResponse

        return ScrapeResourceWithStreamingResponse(self._client.scrape)

    @cached_property
    def crawl(self) -> crawl.CrawlResourceWithStreamingResponse:
        from .resources.crawl import CrawlResourceWithStreamingResponse

        return CrawlResourceWithStreamingResponse(self._client.crawl)

    @cached_property
    def download(self) -> download.DownloadResourceWithStreamingResponse:
        from .resources.download import DownloadResourceWithStreamingResponse

        return DownloadResourceWithStreamingResponse(self._client.download)

    @cached_property
    def workflows(self) -> workflows.WorkflowsResourceWithStreamingResponse:
        from .resources.workflows import WorkflowsResourceWithStreamingResponse

        return WorkflowsResourceWithStreamingResponse(self._client.workflows)


class AsyncCartographyWithStreamedResponse:
    _client: AsyncCartography

    def __init__(self, client: AsyncCartography) -> None:
        self._client = client

    @cached_property
    def health(self) -> health.AsyncHealthResourceWithStreamingResponse:
        from .resources.health import AsyncHealthResourceWithStreamingResponse

        return AsyncHealthResourceWithStreamingResponse(self._client.health)

    @cached_property
    def api_info(self) -> api_info.AsyncAPIInfoResourceWithStreamingResponse:
        from .resources.api_info import AsyncAPIInfoResourceWithStreamingResponse

        return AsyncAPIInfoResourceWithStreamingResponse(self._client.api_info)

    @cached_property
    def scrape(self) -> scrape.AsyncScrapeResourceWithStreamingResponse:
        from .resources.scrape import AsyncScrapeResourceWithStreamingResponse

        return AsyncScrapeResourceWithStreamingResponse(self._client.scrape)

    @cached_property
    def crawl(self) -> crawl.AsyncCrawlResourceWithStreamingResponse:
        from .resources.crawl import AsyncCrawlResourceWithStreamingResponse

        return AsyncCrawlResourceWithStreamingResponse(self._client.crawl)

    @cached_property
    def download(self) -> download.AsyncDownloadResourceWithStreamingResponse:
        from .resources.download import AsyncDownloadResourceWithStreamingResponse

        return AsyncDownloadResourceWithStreamingResponse(self._client.download)

    @cached_property
    def workflows(self) -> workflows.AsyncWorkflowsResourceWithStreamingResponse:
        from .resources.workflows import AsyncWorkflowsResourceWithStreamingResponse

        return AsyncWorkflowsResourceWithStreamingResponse(self._client.workflows)


Client = Cartography

AsyncClient = AsyncCartography
