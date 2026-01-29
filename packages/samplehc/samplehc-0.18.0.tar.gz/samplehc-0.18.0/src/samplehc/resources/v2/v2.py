# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .events import (
    EventsResource,
    AsyncEventsResource,
    EventsResourceWithRawResponse,
    AsyncEventsResourceWithRawResponse,
    EventsResourceWithStreamingResponse,
    AsyncEventsResourceWithStreamingResponse,
)
from .database import (
    DatabaseResource,
    AsyncDatabaseResource,
    DatabaseResourceWithRawResponse,
    AsyncDatabaseResourceWithRawResponse,
    DatabaseResourceWithStreamingResponse,
    AsyncDatabaseResourceWithStreamingResponse,
)
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from .async_results import (
    AsyncResultsResource,
    AsyncAsyncResultsResource,
    AsyncResultsResourceWithRawResponse,
    AsyncAsyncResultsResourceWithRawResponse,
    AsyncResultsResourceWithStreamingResponse,
    AsyncAsyncResultsResourceWithStreamingResponse,
)
from .communication import (
    CommunicationResource,
    AsyncCommunicationResource,
    CommunicationResourceWithRawResponse,
    AsyncCommunicationResourceWithRawResponse,
    CommunicationResourceWithStreamingResponse,
    AsyncCommunicationResourceWithStreamingResponse,
)
from .documents.documents import (
    DocumentsResource,
    AsyncDocumentsResource,
    DocumentsResourceWithRawResponse,
    AsyncDocumentsResourceWithRawResponse,
    DocumentsResourceWithStreamingResponse,
    AsyncDocumentsResourceWithStreamingResponse,
)

__all__ = ["V2Resource", "AsyncV2Resource"]


class V2Resource(SyncAPIResource):
    @cached_property
    def async_results(self) -> AsyncResultsResource:
        return AsyncResultsResource(self._client)

    @cached_property
    def documents(self) -> DocumentsResource:
        return DocumentsResource(self._client)

    @cached_property
    def communication(self) -> CommunicationResource:
        return CommunicationResource(self._client)

    @cached_property
    def events(self) -> EventsResource:
        return EventsResource(self._client)

    @cached_property
    def database(self) -> DatabaseResource:
        return DatabaseResource(self._client)

    @cached_property
    def with_raw_response(self) -> V2ResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/samplehc/samplehc-python#accessing-raw-response-data-eg-headers
        """
        return V2ResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> V2ResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/samplehc/samplehc-python#with_streaming_response
        """
        return V2ResourceWithStreamingResponse(self)


class AsyncV2Resource(AsyncAPIResource):
    @cached_property
    def async_results(self) -> AsyncAsyncResultsResource:
        return AsyncAsyncResultsResource(self._client)

    @cached_property
    def documents(self) -> AsyncDocumentsResource:
        return AsyncDocumentsResource(self._client)

    @cached_property
    def communication(self) -> AsyncCommunicationResource:
        return AsyncCommunicationResource(self._client)

    @cached_property
    def events(self) -> AsyncEventsResource:
        return AsyncEventsResource(self._client)

    @cached_property
    def database(self) -> AsyncDatabaseResource:
        return AsyncDatabaseResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncV2ResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/samplehc/samplehc-python#accessing-raw-response-data-eg-headers
        """
        return AsyncV2ResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncV2ResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/samplehc/samplehc-python#with_streaming_response
        """
        return AsyncV2ResourceWithStreamingResponse(self)


class V2ResourceWithRawResponse:
    def __init__(self, v2: V2Resource) -> None:
        self._v2 = v2

    @cached_property
    def async_results(self) -> AsyncResultsResourceWithRawResponse:
        return AsyncResultsResourceWithRawResponse(self._v2.async_results)

    @cached_property
    def documents(self) -> DocumentsResourceWithRawResponse:
        return DocumentsResourceWithRawResponse(self._v2.documents)

    @cached_property
    def communication(self) -> CommunicationResourceWithRawResponse:
        return CommunicationResourceWithRawResponse(self._v2.communication)

    @cached_property
    def events(self) -> EventsResourceWithRawResponse:
        return EventsResourceWithRawResponse(self._v2.events)

    @cached_property
    def database(self) -> DatabaseResourceWithRawResponse:
        return DatabaseResourceWithRawResponse(self._v2.database)


class AsyncV2ResourceWithRawResponse:
    def __init__(self, v2: AsyncV2Resource) -> None:
        self._v2 = v2

    @cached_property
    def async_results(self) -> AsyncAsyncResultsResourceWithRawResponse:
        return AsyncAsyncResultsResourceWithRawResponse(self._v2.async_results)

    @cached_property
    def documents(self) -> AsyncDocumentsResourceWithRawResponse:
        return AsyncDocumentsResourceWithRawResponse(self._v2.documents)

    @cached_property
    def communication(self) -> AsyncCommunicationResourceWithRawResponse:
        return AsyncCommunicationResourceWithRawResponse(self._v2.communication)

    @cached_property
    def events(self) -> AsyncEventsResourceWithRawResponse:
        return AsyncEventsResourceWithRawResponse(self._v2.events)

    @cached_property
    def database(self) -> AsyncDatabaseResourceWithRawResponse:
        return AsyncDatabaseResourceWithRawResponse(self._v2.database)


class V2ResourceWithStreamingResponse:
    def __init__(self, v2: V2Resource) -> None:
        self._v2 = v2

    @cached_property
    def async_results(self) -> AsyncResultsResourceWithStreamingResponse:
        return AsyncResultsResourceWithStreamingResponse(self._v2.async_results)

    @cached_property
    def documents(self) -> DocumentsResourceWithStreamingResponse:
        return DocumentsResourceWithStreamingResponse(self._v2.documents)

    @cached_property
    def communication(self) -> CommunicationResourceWithStreamingResponse:
        return CommunicationResourceWithStreamingResponse(self._v2.communication)

    @cached_property
    def events(self) -> EventsResourceWithStreamingResponse:
        return EventsResourceWithStreamingResponse(self._v2.events)

    @cached_property
    def database(self) -> DatabaseResourceWithStreamingResponse:
        return DatabaseResourceWithStreamingResponse(self._v2.database)


class AsyncV2ResourceWithStreamingResponse:
    def __init__(self, v2: AsyncV2Resource) -> None:
        self._v2 = v2

    @cached_property
    def async_results(self) -> AsyncAsyncResultsResourceWithStreamingResponse:
        return AsyncAsyncResultsResourceWithStreamingResponse(self._v2.async_results)

    @cached_property
    def documents(self) -> AsyncDocumentsResourceWithStreamingResponse:
        return AsyncDocumentsResourceWithStreamingResponse(self._v2.documents)

    @cached_property
    def communication(self) -> AsyncCommunicationResourceWithStreamingResponse:
        return AsyncCommunicationResourceWithStreamingResponse(self._v2.communication)

    @cached_property
    def events(self) -> AsyncEventsResourceWithStreamingResponse:
        return AsyncEventsResourceWithStreamingResponse(self._v2.events)

    @cached_property
    def database(self) -> AsyncDatabaseResourceWithStreamingResponse:
        return AsyncDatabaseResourceWithStreamingResponse(self._v2.database)
