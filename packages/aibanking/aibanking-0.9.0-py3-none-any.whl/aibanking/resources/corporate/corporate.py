# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal

import httpx

from .cards import (
    CardsResource,
    AsyncCardsResource,
    CardsResourceWithRawResponse,
    AsyncCardsResourceWithRawResponse,
    CardsResourceWithStreamingResponse,
    AsyncCardsResourceWithStreamingResponse,
)
from ...types import corporate_onboard_params
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
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
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
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
from .governance.governance import (
    GovernanceResource,
    AsyncGovernanceResource,
    GovernanceResourceWithRawResponse,
    AsyncGovernanceResourceWithRawResponse,
    GovernanceResourceWithStreamingResponse,
    AsyncGovernanceResourceWithStreamingResponse,
)
from ...types.corporate_onboard_response import CorporateOnboardResponse

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
    def governance(self) -> GovernanceResource:
        return GovernanceResource(self._client)

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

    def onboard(
        self,
        *,
        entity_type: Literal["LLC", "CORP", "NGO", "PARTNERSHIP"],
        jurisdiction: str,
        legal_name: str,
        tax_id: str,
        beneficial_owners: Iterable[corporate_onboard_params.BeneficialOwner] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CorporateOnboardResponse:
        """
        Onboard a New Corporate Entity

        Args:
          legal_name: Registered business name

          tax_id: EIN, VAT, or local tax ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/corporate/onboard",
            body=maybe_transform(
                {
                    "entity_type": entity_type,
                    "jurisdiction": jurisdiction,
                    "legal_name": legal_name,
                    "tax_id": tax_id,
                    "beneficial_owners": beneficial_owners,
                },
                corporate_onboard_params.CorporateOnboardParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CorporateOnboardResponse,
        )


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
    def governance(self) -> AsyncGovernanceResource:
        return AsyncGovernanceResource(self._client)

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

    async def onboard(
        self,
        *,
        entity_type: Literal["LLC", "CORP", "NGO", "PARTNERSHIP"],
        jurisdiction: str,
        legal_name: str,
        tax_id: str,
        beneficial_owners: Iterable[corporate_onboard_params.BeneficialOwner] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CorporateOnboardResponse:
        """
        Onboard a New Corporate Entity

        Args:
          legal_name: Registered business name

          tax_id: EIN, VAT, or local tax ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/corporate/onboard",
            body=await async_maybe_transform(
                {
                    "entity_type": entity_type,
                    "jurisdiction": jurisdiction,
                    "legal_name": legal_name,
                    "tax_id": tax_id,
                    "beneficial_owners": beneficial_owners,
                },
                corporate_onboard_params.CorporateOnboardParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CorporateOnboardResponse,
        )


class CorporateResourceWithRawResponse:
    def __init__(self, corporate: CorporateResource) -> None:
        self._corporate = corporate

        self.onboard = to_raw_response_wrapper(
            corporate.onboard,
        )

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
    def governance(self) -> GovernanceResourceWithRawResponse:
        return GovernanceResourceWithRawResponse(self._corporate.governance)

    @cached_property
    def anomalies(self) -> AnomaliesResourceWithRawResponse:
        return AnomaliesResourceWithRawResponse(self._corporate.anomalies)


class AsyncCorporateResourceWithRawResponse:
    def __init__(self, corporate: AsyncCorporateResource) -> None:
        self._corporate = corporate

        self.onboard = async_to_raw_response_wrapper(
            corporate.onboard,
        )

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
    def governance(self) -> AsyncGovernanceResourceWithRawResponse:
        return AsyncGovernanceResourceWithRawResponse(self._corporate.governance)

    @cached_property
    def anomalies(self) -> AsyncAnomaliesResourceWithRawResponse:
        return AsyncAnomaliesResourceWithRawResponse(self._corporate.anomalies)


class CorporateResourceWithStreamingResponse:
    def __init__(self, corporate: CorporateResource) -> None:
        self._corporate = corporate

        self.onboard = to_streamed_response_wrapper(
            corporate.onboard,
        )

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
    def governance(self) -> GovernanceResourceWithStreamingResponse:
        return GovernanceResourceWithStreamingResponse(self._corporate.governance)

    @cached_property
    def anomalies(self) -> AnomaliesResourceWithStreamingResponse:
        return AnomaliesResourceWithStreamingResponse(self._corporate.anomalies)


class AsyncCorporateResourceWithStreamingResponse:
    def __init__(self, corporate: AsyncCorporateResource) -> None:
        self._corporate = corporate

        self.onboard = async_to_streamed_response_wrapper(
            corporate.onboard,
        )

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
    def governance(self) -> AsyncGovernanceResourceWithStreamingResponse:
        return AsyncGovernanceResourceWithStreamingResponse(self._corporate.governance)

    @cached_property
    def anomalies(self) -> AsyncAnomaliesResourceWithStreamingResponse:
        return AsyncAnomaliesResourceWithStreamingResponse(self._corporate.anomalies)
