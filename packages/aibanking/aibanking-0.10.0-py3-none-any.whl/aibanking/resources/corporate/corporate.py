# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .cards import (
    CardsResource,
    AsyncCardsResource,
    CardsResourceWithRawResponse,
    AsyncCardsResourceWithRawResponse,
    CardsResourceWithStreamingResponse,
    AsyncCardsResourceWithStreamingResponse,
)
from ..._compat import cached_property
from .anomalies import (
    AnomaliesResource,
    AsyncAnomaliesResource,
    AnomaliesResourceWithRawResponse,
    AsyncAnomaliesResourceWithRawResponse,
    AnomaliesResourceWithStreamingResponse,
    AsyncAnomaliesResourceWithStreamingResponse,
)
from .risk.risk import (
    RiskResource,
    AsyncRiskResource,
    RiskResourceWithRawResponse,
    AsyncRiskResourceWithRawResponse,
    RiskResourceWithStreamingResponse,
    AsyncRiskResourceWithStreamingResponse,
)
from ..._resource import SyncAPIResource, AsyncAPIResource
from .treasury.treasury import (
    TreasuryResource,
    AsyncTreasuryResource,
    TreasuryResourceWithRawResponse,
    AsyncTreasuryResourceWithRawResponse,
    TreasuryResourceWithStreamingResponse,
    AsyncTreasuryResourceWithStreamingResponse,
)
from .compliance.compliance import (
    ComplianceResource,
    AsyncComplianceResource,
    ComplianceResourceWithRawResponse,
    AsyncComplianceResourceWithRawResponse,
    ComplianceResourceWithStreamingResponse,
    AsyncComplianceResourceWithStreamingResponse,
)

__all__ = ["CorporateResource", "AsyncCorporateResource"]


class CorporateResource(SyncAPIResource):
    @cached_property
    def compliance(self) -> ComplianceResource:
        return ComplianceResource(self._client)

    @cached_property
    def treasury(self) -> TreasuryResource:
        return TreasuryResource(self._client)

    @cached_property
    def cards(self) -> CardsResource:
        return CardsResource(self._client)

    @cached_property
    def risk(self) -> RiskResource:
        return RiskResource(self._client)

    @cached_property
    def anomalies(self) -> AnomaliesResource:
        return AnomaliesResource(self._client)

    @cached_property
    def with_raw_response(self) -> CorporateResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return CorporateResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CorporateResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return CorporateResourceWithStreamingResponse(self)


class AsyncCorporateResource(AsyncAPIResource):
    @cached_property
    def compliance(self) -> AsyncComplianceResource:
        return AsyncComplianceResource(self._client)

    @cached_property
    def treasury(self) -> AsyncTreasuryResource:
        return AsyncTreasuryResource(self._client)

    @cached_property
    def cards(self) -> AsyncCardsResource:
        return AsyncCardsResource(self._client)

    @cached_property
    def risk(self) -> AsyncRiskResource:
        return AsyncRiskResource(self._client)

    @cached_property
    def anomalies(self) -> AsyncAnomaliesResource:
        return AsyncAnomaliesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncCorporateResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncCorporateResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCorporateResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncCorporateResourceWithStreamingResponse(self)


class CorporateResourceWithRawResponse:
    def __init__(self, corporate: CorporateResource) -> None:
        self._corporate = corporate

    @cached_property
    def compliance(self) -> ComplianceResourceWithRawResponse:
        return ComplianceResourceWithRawResponse(self._corporate.compliance)

    @cached_property
    def treasury(self) -> TreasuryResourceWithRawResponse:
        return TreasuryResourceWithRawResponse(self._corporate.treasury)

    @cached_property
    def cards(self) -> CardsResourceWithRawResponse:
        return CardsResourceWithRawResponse(self._corporate.cards)

    @cached_property
    def risk(self) -> RiskResourceWithRawResponse:
        return RiskResourceWithRawResponse(self._corporate.risk)

    @cached_property
    def anomalies(self) -> AnomaliesResourceWithRawResponse:
        return AnomaliesResourceWithRawResponse(self._corporate.anomalies)


class AsyncCorporateResourceWithRawResponse:
    def __init__(self, corporate: AsyncCorporateResource) -> None:
        self._corporate = corporate

    @cached_property
    def compliance(self) -> AsyncComplianceResourceWithRawResponse:
        return AsyncComplianceResourceWithRawResponse(self._corporate.compliance)

    @cached_property
    def treasury(self) -> AsyncTreasuryResourceWithRawResponse:
        return AsyncTreasuryResourceWithRawResponse(self._corporate.treasury)

    @cached_property
    def cards(self) -> AsyncCardsResourceWithRawResponse:
        return AsyncCardsResourceWithRawResponse(self._corporate.cards)

    @cached_property
    def risk(self) -> AsyncRiskResourceWithRawResponse:
        return AsyncRiskResourceWithRawResponse(self._corporate.risk)

    @cached_property
    def anomalies(self) -> AsyncAnomaliesResourceWithRawResponse:
        return AsyncAnomaliesResourceWithRawResponse(self._corporate.anomalies)


class CorporateResourceWithStreamingResponse:
    def __init__(self, corporate: CorporateResource) -> None:
        self._corporate = corporate

    @cached_property
    def compliance(self) -> ComplianceResourceWithStreamingResponse:
        return ComplianceResourceWithStreamingResponse(self._corporate.compliance)

    @cached_property
    def treasury(self) -> TreasuryResourceWithStreamingResponse:
        return TreasuryResourceWithStreamingResponse(self._corporate.treasury)

    @cached_property
    def cards(self) -> CardsResourceWithStreamingResponse:
        return CardsResourceWithStreamingResponse(self._corporate.cards)

    @cached_property
    def risk(self) -> RiskResourceWithStreamingResponse:
        return RiskResourceWithStreamingResponse(self._corporate.risk)

    @cached_property
    def anomalies(self) -> AnomaliesResourceWithStreamingResponse:
        return AnomaliesResourceWithStreamingResponse(self._corporate.anomalies)


class AsyncCorporateResourceWithStreamingResponse:
    def __init__(self, corporate: AsyncCorporateResource) -> None:
        self._corporate = corporate

    @cached_property
    def compliance(self) -> AsyncComplianceResourceWithStreamingResponse:
        return AsyncComplianceResourceWithStreamingResponse(self._corporate.compliance)

    @cached_property
    def treasury(self) -> AsyncTreasuryResourceWithStreamingResponse:
        return AsyncTreasuryResourceWithStreamingResponse(self._corporate.treasury)

    @cached_property
    def cards(self) -> AsyncCardsResourceWithStreamingResponse:
        return AsyncCardsResourceWithStreamingResponse(self._corporate.cards)

    @cached_property
    def risk(self) -> AsyncRiskResourceWithStreamingResponse:
        return AsyncRiskResourceWithStreamingResponse(self._corporate.risk)

    @cached_property
    def anomalies(self) -> AsyncAnomaliesResourceWithStreamingResponse:
        return AsyncAnomaliesResourceWithStreamingResponse(self._corporate.anomalies)
