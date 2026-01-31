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
from ._exceptions import BlueHiveError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import fax, hl7, health, orders, version, database, employees, employers, providers, integrations
    from .resources.fax import FaxResource, AsyncFaxResource
    from .resources.hl7 import Hl7Resource, AsyncHl7Resource
    from .resources.health import HealthResource, AsyncHealthResource
    from .resources.orders import OrdersResource, AsyncOrdersResource
    from .resources.version import VersionResource, AsyncVersionResource
    from .resources.database import DatabaseResource, AsyncDatabaseResource
    from .resources.employees import EmployeesResource, AsyncEmployeesResource
    from .resources.providers import ProvidersResource, AsyncProvidersResource
    from .resources.integrations import IntegrationsResource, AsyncIntegrationsResource
    from .resources.employers.employers import EmployersResource, AsyncEmployersResource

__all__ = [
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "BlueHive",
    "AsyncBlueHive",
    "Client",
    "AsyncClient",
]


class BlueHive(SyncAPIClient):
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
        """Construct a new synchronous BlueHive client instance.

        This automatically infers the `api_key` argument from the `BLUEHIVE_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("BLUEHIVE_API_KEY")
        if api_key is None:
            raise BlueHiveError(
                "The api_key client option must be set either by passing api_key to the client or by setting the BLUEHIVE_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("BLUE_HIVE_BASE_URL")
        if base_url is None:
            base_url = f"https://api.bluehive.com"

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
    def version(self) -> VersionResource:
        from .resources.version import VersionResource

        return VersionResource(self)

    @cached_property
    def providers(self) -> ProvidersResource:
        from .resources.providers import ProvidersResource

        return ProvidersResource(self)

    @cached_property
    def database(self) -> DatabaseResource:
        from .resources.database import DatabaseResource

        return DatabaseResource(self)

    @cached_property
    def fax(self) -> FaxResource:
        from .resources.fax import FaxResource

        return FaxResource(self)

    @cached_property
    def employers(self) -> EmployersResource:
        from .resources.employers import EmployersResource

        return EmployersResource(self)

    @cached_property
    def hl7(self) -> Hl7Resource:
        from .resources.hl7 import Hl7Resource

        return Hl7Resource(self)

    @cached_property
    def orders(self) -> OrdersResource:
        from .resources.orders import OrdersResource

        return OrdersResource(self)

    @cached_property
    def employees(self) -> EmployeesResource:
        from .resources.employees import EmployeesResource

        return EmployeesResource(self)

    @cached_property
    def integrations(self) -> IntegrationsResource:
        from .resources.integrations import IntegrationsResource

        return IntegrationsResource(self)

    @cached_property
    def with_raw_response(self) -> BlueHiveWithRawResponse:
        return BlueHiveWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> BlueHiveWithStreamedResponse:
        return BlueHiveWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": api_key}

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


class AsyncBlueHive(AsyncAPIClient):
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
        """Construct a new async AsyncBlueHive client instance.

        This automatically infers the `api_key` argument from the `BLUEHIVE_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("BLUEHIVE_API_KEY")
        if api_key is None:
            raise BlueHiveError(
                "The api_key client option must be set either by passing api_key to the client or by setting the BLUEHIVE_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("BLUE_HIVE_BASE_URL")
        if base_url is None:
            base_url = f"https://api.bluehive.com"

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
    def version(self) -> AsyncVersionResource:
        from .resources.version import AsyncVersionResource

        return AsyncVersionResource(self)

    @cached_property
    def providers(self) -> AsyncProvidersResource:
        from .resources.providers import AsyncProvidersResource

        return AsyncProvidersResource(self)

    @cached_property
    def database(self) -> AsyncDatabaseResource:
        from .resources.database import AsyncDatabaseResource

        return AsyncDatabaseResource(self)

    @cached_property
    def fax(self) -> AsyncFaxResource:
        from .resources.fax import AsyncFaxResource

        return AsyncFaxResource(self)

    @cached_property
    def employers(self) -> AsyncEmployersResource:
        from .resources.employers import AsyncEmployersResource

        return AsyncEmployersResource(self)

    @cached_property
    def hl7(self) -> AsyncHl7Resource:
        from .resources.hl7 import AsyncHl7Resource

        return AsyncHl7Resource(self)

    @cached_property
    def orders(self) -> AsyncOrdersResource:
        from .resources.orders import AsyncOrdersResource

        return AsyncOrdersResource(self)

    @cached_property
    def employees(self) -> AsyncEmployeesResource:
        from .resources.employees import AsyncEmployeesResource

        return AsyncEmployeesResource(self)

    @cached_property
    def integrations(self) -> AsyncIntegrationsResource:
        from .resources.integrations import AsyncIntegrationsResource

        return AsyncIntegrationsResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncBlueHiveWithRawResponse:
        return AsyncBlueHiveWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncBlueHiveWithStreamedResponse:
        return AsyncBlueHiveWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": api_key}

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


class BlueHiveWithRawResponse:
    _client: BlueHive

    def __init__(self, client: BlueHive) -> None:
        self._client = client

    @cached_property
    def health(self) -> health.HealthResourceWithRawResponse:
        from .resources.health import HealthResourceWithRawResponse

        return HealthResourceWithRawResponse(self._client.health)

    @cached_property
    def version(self) -> version.VersionResourceWithRawResponse:
        from .resources.version import VersionResourceWithRawResponse

        return VersionResourceWithRawResponse(self._client.version)

    @cached_property
    def providers(self) -> providers.ProvidersResourceWithRawResponse:
        from .resources.providers import ProvidersResourceWithRawResponse

        return ProvidersResourceWithRawResponse(self._client.providers)

    @cached_property
    def database(self) -> database.DatabaseResourceWithRawResponse:
        from .resources.database import DatabaseResourceWithRawResponse

        return DatabaseResourceWithRawResponse(self._client.database)

    @cached_property
    def fax(self) -> fax.FaxResourceWithRawResponse:
        from .resources.fax import FaxResourceWithRawResponse

        return FaxResourceWithRawResponse(self._client.fax)

    @cached_property
    def employers(self) -> employers.EmployersResourceWithRawResponse:
        from .resources.employers import EmployersResourceWithRawResponse

        return EmployersResourceWithRawResponse(self._client.employers)

    @cached_property
    def hl7(self) -> hl7.Hl7ResourceWithRawResponse:
        from .resources.hl7 import Hl7ResourceWithRawResponse

        return Hl7ResourceWithRawResponse(self._client.hl7)

    @cached_property
    def orders(self) -> orders.OrdersResourceWithRawResponse:
        from .resources.orders import OrdersResourceWithRawResponse

        return OrdersResourceWithRawResponse(self._client.orders)

    @cached_property
    def employees(self) -> employees.EmployeesResourceWithRawResponse:
        from .resources.employees import EmployeesResourceWithRawResponse

        return EmployeesResourceWithRawResponse(self._client.employees)

    @cached_property
    def integrations(self) -> integrations.IntegrationsResourceWithRawResponse:
        from .resources.integrations import IntegrationsResourceWithRawResponse

        return IntegrationsResourceWithRawResponse(self._client.integrations)


class AsyncBlueHiveWithRawResponse:
    _client: AsyncBlueHive

    def __init__(self, client: AsyncBlueHive) -> None:
        self._client = client

    @cached_property
    def health(self) -> health.AsyncHealthResourceWithRawResponse:
        from .resources.health import AsyncHealthResourceWithRawResponse

        return AsyncHealthResourceWithRawResponse(self._client.health)

    @cached_property
    def version(self) -> version.AsyncVersionResourceWithRawResponse:
        from .resources.version import AsyncVersionResourceWithRawResponse

        return AsyncVersionResourceWithRawResponse(self._client.version)

    @cached_property
    def providers(self) -> providers.AsyncProvidersResourceWithRawResponse:
        from .resources.providers import AsyncProvidersResourceWithRawResponse

        return AsyncProvidersResourceWithRawResponse(self._client.providers)

    @cached_property
    def database(self) -> database.AsyncDatabaseResourceWithRawResponse:
        from .resources.database import AsyncDatabaseResourceWithRawResponse

        return AsyncDatabaseResourceWithRawResponse(self._client.database)

    @cached_property
    def fax(self) -> fax.AsyncFaxResourceWithRawResponse:
        from .resources.fax import AsyncFaxResourceWithRawResponse

        return AsyncFaxResourceWithRawResponse(self._client.fax)

    @cached_property
    def employers(self) -> employers.AsyncEmployersResourceWithRawResponse:
        from .resources.employers import AsyncEmployersResourceWithRawResponse

        return AsyncEmployersResourceWithRawResponse(self._client.employers)

    @cached_property
    def hl7(self) -> hl7.AsyncHl7ResourceWithRawResponse:
        from .resources.hl7 import AsyncHl7ResourceWithRawResponse

        return AsyncHl7ResourceWithRawResponse(self._client.hl7)

    @cached_property
    def orders(self) -> orders.AsyncOrdersResourceWithRawResponse:
        from .resources.orders import AsyncOrdersResourceWithRawResponse

        return AsyncOrdersResourceWithRawResponse(self._client.orders)

    @cached_property
    def employees(self) -> employees.AsyncEmployeesResourceWithRawResponse:
        from .resources.employees import AsyncEmployeesResourceWithRawResponse

        return AsyncEmployeesResourceWithRawResponse(self._client.employees)

    @cached_property
    def integrations(self) -> integrations.AsyncIntegrationsResourceWithRawResponse:
        from .resources.integrations import AsyncIntegrationsResourceWithRawResponse

        return AsyncIntegrationsResourceWithRawResponse(self._client.integrations)


class BlueHiveWithStreamedResponse:
    _client: BlueHive

    def __init__(self, client: BlueHive) -> None:
        self._client = client

    @cached_property
    def health(self) -> health.HealthResourceWithStreamingResponse:
        from .resources.health import HealthResourceWithStreamingResponse

        return HealthResourceWithStreamingResponse(self._client.health)

    @cached_property
    def version(self) -> version.VersionResourceWithStreamingResponse:
        from .resources.version import VersionResourceWithStreamingResponse

        return VersionResourceWithStreamingResponse(self._client.version)

    @cached_property
    def providers(self) -> providers.ProvidersResourceWithStreamingResponse:
        from .resources.providers import ProvidersResourceWithStreamingResponse

        return ProvidersResourceWithStreamingResponse(self._client.providers)

    @cached_property
    def database(self) -> database.DatabaseResourceWithStreamingResponse:
        from .resources.database import DatabaseResourceWithStreamingResponse

        return DatabaseResourceWithStreamingResponse(self._client.database)

    @cached_property
    def fax(self) -> fax.FaxResourceWithStreamingResponse:
        from .resources.fax import FaxResourceWithStreamingResponse

        return FaxResourceWithStreamingResponse(self._client.fax)

    @cached_property
    def employers(self) -> employers.EmployersResourceWithStreamingResponse:
        from .resources.employers import EmployersResourceWithStreamingResponse

        return EmployersResourceWithStreamingResponse(self._client.employers)

    @cached_property
    def hl7(self) -> hl7.Hl7ResourceWithStreamingResponse:
        from .resources.hl7 import Hl7ResourceWithStreamingResponse

        return Hl7ResourceWithStreamingResponse(self._client.hl7)

    @cached_property
    def orders(self) -> orders.OrdersResourceWithStreamingResponse:
        from .resources.orders import OrdersResourceWithStreamingResponse

        return OrdersResourceWithStreamingResponse(self._client.orders)

    @cached_property
    def employees(self) -> employees.EmployeesResourceWithStreamingResponse:
        from .resources.employees import EmployeesResourceWithStreamingResponse

        return EmployeesResourceWithStreamingResponse(self._client.employees)

    @cached_property
    def integrations(self) -> integrations.IntegrationsResourceWithStreamingResponse:
        from .resources.integrations import IntegrationsResourceWithStreamingResponse

        return IntegrationsResourceWithStreamingResponse(self._client.integrations)


class AsyncBlueHiveWithStreamedResponse:
    _client: AsyncBlueHive

    def __init__(self, client: AsyncBlueHive) -> None:
        self._client = client

    @cached_property
    def health(self) -> health.AsyncHealthResourceWithStreamingResponse:
        from .resources.health import AsyncHealthResourceWithStreamingResponse

        return AsyncHealthResourceWithStreamingResponse(self._client.health)

    @cached_property
    def version(self) -> version.AsyncVersionResourceWithStreamingResponse:
        from .resources.version import AsyncVersionResourceWithStreamingResponse

        return AsyncVersionResourceWithStreamingResponse(self._client.version)

    @cached_property
    def providers(self) -> providers.AsyncProvidersResourceWithStreamingResponse:
        from .resources.providers import AsyncProvidersResourceWithStreamingResponse

        return AsyncProvidersResourceWithStreamingResponse(self._client.providers)

    @cached_property
    def database(self) -> database.AsyncDatabaseResourceWithStreamingResponse:
        from .resources.database import AsyncDatabaseResourceWithStreamingResponse

        return AsyncDatabaseResourceWithStreamingResponse(self._client.database)

    @cached_property
    def fax(self) -> fax.AsyncFaxResourceWithStreamingResponse:
        from .resources.fax import AsyncFaxResourceWithStreamingResponse

        return AsyncFaxResourceWithStreamingResponse(self._client.fax)

    @cached_property
    def employers(self) -> employers.AsyncEmployersResourceWithStreamingResponse:
        from .resources.employers import AsyncEmployersResourceWithStreamingResponse

        return AsyncEmployersResourceWithStreamingResponse(self._client.employers)

    @cached_property
    def hl7(self) -> hl7.AsyncHl7ResourceWithStreamingResponse:
        from .resources.hl7 import AsyncHl7ResourceWithStreamingResponse

        return AsyncHl7ResourceWithStreamingResponse(self._client.hl7)

    @cached_property
    def orders(self) -> orders.AsyncOrdersResourceWithStreamingResponse:
        from .resources.orders import AsyncOrdersResourceWithStreamingResponse

        return AsyncOrdersResourceWithStreamingResponse(self._client.orders)

    @cached_property
    def employees(self) -> employees.AsyncEmployeesResourceWithStreamingResponse:
        from .resources.employees import AsyncEmployeesResourceWithStreamingResponse

        return AsyncEmployeesResourceWithStreamingResponse(self._client.employees)

    @cached_property
    def integrations(self) -> integrations.AsyncIntegrationsResourceWithStreamingResponse:
        from .resources.integrations import AsyncIntegrationsResourceWithStreamingResponse

        return AsyncIntegrationsResourceWithStreamingResponse(self._client.integrations)


Client = BlueHive

AsyncClient = AsyncBlueHive
