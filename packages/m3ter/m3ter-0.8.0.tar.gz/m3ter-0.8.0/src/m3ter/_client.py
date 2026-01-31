# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
import base64
from typing import TYPE_CHECKING, Any, Mapping
from datetime import datetime
from typing_extensions import Self, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    Omit,
    Headers,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    not_given,
)
from ._utils import is_given, get_async_library
from ._compat import cached_property
from ._models import FinalRequestOptions
from ._version import __version__
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import M3terError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import (
        bills,
        plans,
        usage,
        users,
        events,
        meters,
        charges,
        accounts,
        balances,
        counters,
        pricings,
        products,
        webhooks,
        bill_jobs,
        contracts,
        currencies,
        statements,
        bill_config,
        commitments,
        plan_groups,
        aggregations,
        data_exports,
        account_plans,
        custom_fields,
        debit_reasons,
        lookup_tables,
        authentication,
        credit_reasons,
        plan_templates,
        resource_groups,
        counter_pricings,
        plan_group_links,
        external_mappings,
        transaction_types,
        counter_adjustments,
        organization_config,
        permission_policies,
        compound_aggregations,
        integration_configurations,
        notification_configurations,
        scheduled_event_configurations,
    )
    from .resources.plans import PlansResource, AsyncPlansResource
    from .resources.events import EventsResource, AsyncEventsResource
    from .resources.meters import MetersResource, AsyncMetersResource
    from .resources.charges import ChargesResource, AsyncChargesResource
    from .resources.accounts import AccountsResource, AsyncAccountsResource
    from .resources.counters import CountersResource, AsyncCountersResource
    from .resources.pricings import PricingsResource, AsyncPricingsResource
    from .resources.products import ProductsResource, AsyncProductsResource
    from .resources.webhooks import WebhooksResource, AsyncWebhooksResource
    from .resources.bill_jobs import BillJobsResource, AsyncBillJobsResource
    from .resources.contracts import ContractsResource, AsyncContractsResource
    from .resources.currencies import CurrenciesResource, AsyncCurrenciesResource
    from .resources.bill_config import BillConfigResource, AsyncBillConfigResource
    from .resources.bills.bills import BillsResource, AsyncBillsResource
    from .resources.commitments import CommitmentsResource, AsyncCommitmentsResource
    from .resources.plan_groups import PlanGroupsResource, AsyncPlanGroupsResource
    from .resources.usage.usage import UsageResource, AsyncUsageResource
    from .resources.users.users import UsersResource, AsyncUsersResource
    from .resources.aggregations import AggregationsResource, AsyncAggregationsResource
    from .resources.account_plans import AccountPlansResource, AsyncAccountPlansResource
    from .resources.custom_fields import CustomFieldsResource, AsyncCustomFieldsResource
    from .resources.debit_reasons import DebitReasonsResource, AsyncDebitReasonsResource
    from .resources.authentication import AuthenticationResource, AsyncAuthenticationResource
    from .resources.credit_reasons import CreditReasonsResource, AsyncCreditReasonsResource
    from .resources.plan_templates import PlanTemplatesResource, AsyncPlanTemplatesResource
    from .resources.resource_groups import ResourceGroupsResource, AsyncResourceGroupsResource
    from .resources.counter_pricings import CounterPricingsResource, AsyncCounterPricingsResource
    from .resources.plan_group_links import PlanGroupLinksResource, AsyncPlanGroupLinksResource
    from .resources.balances.balances import BalancesResource, AsyncBalancesResource
    from .resources.external_mappings import ExternalMappingsResource, AsyncExternalMappingsResource
    from .resources.transaction_types import TransactionTypesResource, AsyncTransactionTypesResource
    from .resources.counter_adjustments import CounterAdjustmentsResource, AsyncCounterAdjustmentsResource
    from .resources.organization_config import OrganizationConfigResource, AsyncOrganizationConfigResource
    from .resources.permission_policies import PermissionPoliciesResource, AsyncPermissionPoliciesResource
    from .resources.compound_aggregations import CompoundAggregationsResource, AsyncCompoundAggregationsResource
    from .resources.statements.statements import StatementsResource, AsyncStatementsResource
    from .resources.data_exports.data_exports import DataExportsResource, AsyncDataExportsResource
    from .resources.integration_configurations import (
        IntegrationConfigurationsResource,
        AsyncIntegrationConfigurationsResource,
    )
    from .resources.lookup_tables.lookup_tables import LookupTablesResource, AsyncLookupTablesResource
    from .resources.notification_configurations import (
        NotificationConfigurationsResource,
        AsyncNotificationConfigurationsResource,
    )
    from .resources.scheduled_event_configurations import (
        ScheduledEventConfigurationsResource,
        AsyncScheduledEventConfigurationsResource,
    )

__all__ = ["Timeout", "Transport", "ProxiesTypes", "RequestOptions", "M3ter", "AsyncM3ter", "Client", "AsyncClient"]

from .types import AuthenticationGetBearerTokenResponse


class M3ter(SyncAPIClient):
    # client options
    api_key: str
    api_secret: str
    token: str | None
    token_expiry: datetime | None
    org_id: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_secret: str | None = None,
        token: str | None = None,
        token_expiry: datetime | None = None,
        org_id: str | None = None,
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
        """Construct a new synchronous M3ter client instance.

        This automatically infers the following arguments from their corresponding environment variables if they are not provided:
        - `api_key` from `M3TER_API_KEY`
        - `api_secret` from `M3TER_API_SECRET`
        - `token` from `M3TER_API_TOKEN`
        - `org_id` from `M3TER_ORG_ID`
        """
        if api_key is None:
            api_key = os.environ.get("M3TER_API_KEY")
        if api_key is None:
            raise M3terError(
                "The api_key client option must be set either by passing api_key to the client or by setting the M3TER_API_KEY environment variable"
            )
        self.api_key = api_key

        if api_secret is None:
            api_secret = os.environ.get("M3TER_API_SECRET")
        if api_secret is None:
            raise M3terError(
                "The api_secret client option must be set either by passing api_secret to the client or by setting the M3TER_API_SECRET environment variable"
            )
        self.api_secret = api_secret

        if token is None:
            token = os.environ.get("M3TER_API_TOKEN")
        self.token = token
        self.token_expiry = token_expiry

        if org_id is None:
            org_id = os.environ.get("M3TER_ORG_ID")
        if org_id is None:
            raise M3terError(
                "The org_id client option must be set either by passing org_id to the client or by setting the M3TER_ORG_ID environment variable"
            )
        self.org_id = org_id

        if base_url is None:
            base_url = os.environ.get("M3TER_BASE_URL")
        self._base_url_overridden = base_url is not None
        if base_url is None:
            base_url = f"https://api.m3ter.com"

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
    def authentication(self) -> AuthenticationResource:
        from .resources.authentication import AuthenticationResource

        return AuthenticationResource(self)

    @cached_property
    def accounts(self) -> AccountsResource:
        from .resources.accounts import AccountsResource

        return AccountsResource(self)

    @cached_property
    def account_plans(self) -> AccountPlansResource:
        from .resources.account_plans import AccountPlansResource

        return AccountPlansResource(self)

    @cached_property
    def aggregations(self) -> AggregationsResource:
        from .resources.aggregations import AggregationsResource

        return AggregationsResource(self)

    @cached_property
    def balances(self) -> BalancesResource:
        from .resources.balances import BalancesResource

        return BalancesResource(self)

    @cached_property
    def bills(self) -> BillsResource:
        from .resources.bills import BillsResource

        return BillsResource(self)

    @cached_property
    def bill_config(self) -> BillConfigResource:
        from .resources.bill_config import BillConfigResource

        return BillConfigResource(self)

    @cached_property
    def commitments(self) -> CommitmentsResource:
        from .resources.commitments import CommitmentsResource

        return CommitmentsResource(self)

    @cached_property
    def bill_jobs(self) -> BillJobsResource:
        from .resources.bill_jobs import BillJobsResource

        return BillJobsResource(self)

    @cached_property
    def charges(self) -> ChargesResource:
        from .resources.charges import ChargesResource

        return ChargesResource(self)

    @cached_property
    def compound_aggregations(self) -> CompoundAggregationsResource:
        from .resources.compound_aggregations import CompoundAggregationsResource

        return CompoundAggregationsResource(self)

    @cached_property
    def contracts(self) -> ContractsResource:
        from .resources.contracts import ContractsResource

        return ContractsResource(self)

    @cached_property
    def counters(self) -> CountersResource:
        from .resources.counters import CountersResource

        return CountersResource(self)

    @cached_property
    def counter_adjustments(self) -> CounterAdjustmentsResource:
        from .resources.counter_adjustments import CounterAdjustmentsResource

        return CounterAdjustmentsResource(self)

    @cached_property
    def counter_pricings(self) -> CounterPricingsResource:
        from .resources.counter_pricings import CounterPricingsResource

        return CounterPricingsResource(self)

    @cached_property
    def credit_reasons(self) -> CreditReasonsResource:
        from .resources.credit_reasons import CreditReasonsResource

        return CreditReasonsResource(self)

    @cached_property
    def currencies(self) -> CurrenciesResource:
        from .resources.currencies import CurrenciesResource

        return CurrenciesResource(self)

    @cached_property
    def custom_fields(self) -> CustomFieldsResource:
        from .resources.custom_fields import CustomFieldsResource

        return CustomFieldsResource(self)

    @cached_property
    def data_exports(self) -> DataExportsResource:
        from .resources.data_exports import DataExportsResource

        return DataExportsResource(self)

    @cached_property
    def debit_reasons(self) -> DebitReasonsResource:
        from .resources.debit_reasons import DebitReasonsResource

        return DebitReasonsResource(self)

    @cached_property
    def events(self) -> EventsResource:
        from .resources.events import EventsResource

        return EventsResource(self)

    @cached_property
    def external_mappings(self) -> ExternalMappingsResource:
        from .resources.external_mappings import ExternalMappingsResource

        return ExternalMappingsResource(self)

    @cached_property
    def integration_configurations(self) -> IntegrationConfigurationsResource:
        from .resources.integration_configurations import IntegrationConfigurationsResource

        return IntegrationConfigurationsResource(self)

    @cached_property
    def lookup_tables(self) -> LookupTablesResource:
        from .resources.lookup_tables import LookupTablesResource

        return LookupTablesResource(self)

    @cached_property
    def meters(self) -> MetersResource:
        from .resources.meters import MetersResource

        return MetersResource(self)

    @cached_property
    def notification_configurations(self) -> NotificationConfigurationsResource:
        from .resources.notification_configurations import NotificationConfigurationsResource

        return NotificationConfigurationsResource(self)

    @cached_property
    def organization_config(self) -> OrganizationConfigResource:
        from .resources.organization_config import OrganizationConfigResource

        return OrganizationConfigResource(self)

    @cached_property
    def permission_policies(self) -> PermissionPoliciesResource:
        from .resources.permission_policies import PermissionPoliciesResource

        return PermissionPoliciesResource(self)

    @cached_property
    def plans(self) -> PlansResource:
        from .resources.plans import PlansResource

        return PlansResource(self)

    @cached_property
    def plan_groups(self) -> PlanGroupsResource:
        from .resources.plan_groups import PlanGroupsResource

        return PlanGroupsResource(self)

    @cached_property
    def plan_group_links(self) -> PlanGroupLinksResource:
        from .resources.plan_group_links import PlanGroupLinksResource

        return PlanGroupLinksResource(self)

    @cached_property
    def plan_templates(self) -> PlanTemplatesResource:
        from .resources.plan_templates import PlanTemplatesResource

        return PlanTemplatesResource(self)

    @cached_property
    def pricings(self) -> PricingsResource:
        from .resources.pricings import PricingsResource

        return PricingsResource(self)

    @cached_property
    def products(self) -> ProductsResource:
        from .resources.products import ProductsResource

        return ProductsResource(self)

    @cached_property
    def resource_groups(self) -> ResourceGroupsResource:
        from .resources.resource_groups import ResourceGroupsResource

        return ResourceGroupsResource(self)

    @cached_property
    def scheduled_event_configurations(self) -> ScheduledEventConfigurationsResource:
        from .resources.scheduled_event_configurations import ScheduledEventConfigurationsResource

        return ScheduledEventConfigurationsResource(self)

    @cached_property
    def statements(self) -> StatementsResource:
        from .resources.statements import StatementsResource

        return StatementsResource(self)

    @cached_property
    def transaction_types(self) -> TransactionTypesResource:
        from .resources.transaction_types import TransactionTypesResource

        return TransactionTypesResource(self)

    @cached_property
    def usage(self) -> UsageResource:
        from .resources.usage import UsageResource

        return UsageResource(self)

    @cached_property
    def users(self) -> UsersResource:
        from .resources.users import UsersResource

        return UsersResource(self)

    @cached_property
    def webhooks(self) -> WebhooksResource:
        from .resources.webhooks import WebhooksResource

        return WebhooksResource(self)

    @cached_property
    def with_raw_response(self) -> M3terWithRawResponse:
        return M3terWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> M3terWithStreamedResponse:
        return M3terWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        token = self.token
        if token is None:
            return {}
        return {"Authorization": f"Bearer {token}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    @override
    def _validate_headers(self, headers: Headers, custom_headers: Headers) -> None:
        if self.token or headers.get("Authorization") or isinstance(custom_headers.get("Authorization"), Omit):
            return

        raise TypeError(
            '"Could not resolve authentication method. Expected the token to be set. Or for the `Authorization` headers to be explicitly omitted"'
        )

    @override
    def _prepare_options(
        self,
        options: FinalRequestOptions,  # noqa: ARG002
    ) -> FinalRequestOptions:
        token_valid: bool = self.token is not None and (self.token_expiry is None or self.token_expiry > datetime.now())
        if not options.url.endswith("/oauth/token"):
            if not token_valid:
                auth: str = base64.b64encode(f"{self.api_key}:{self.api_secret}".encode("utf8")).decode("utf8")
                token: AuthenticationGetBearerTokenResponse = self.authentication.get_bearer_token(
                    grant_type="client_credentials", extra_headers={"Authorization": f"Basic {auth}"}
                )
                self.token = token.access_token
                # expiry minus 5 minutes from effective refreshing
                self.token_expiry = datetime.fromtimestamp(token.expires_in - 300)
        return options

    def copy(
        self,
        *,
        api_key: str | None = None,
        api_secret: str | None = None,
        token: str | None = None,
        token_expiry: datetime | None = None,
        org_id: str | None = None,
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
        client = self.__class__(
            api_key=api_key or self.api_key,
            api_secret=api_secret or self.api_secret,
            token=token or self.token,
            token_expiry=token_expiry or self.token_expiry,
            org_id=org_id or self.org_id,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )
        client._base_url_overridden = self._base_url_overridden or base_url is not None
        return client

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    def _get_org_id_path_param(self) -> str:
        return self.org_id

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


class AsyncM3ter(AsyncAPIClient):
    # client options
    api_key: str
    api_secret: str
    token: str | None
    org_id: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_secret: str | None = None,
        token: str | None = None,
        org_id: str | None = None,
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
        """Construct a new async AsyncM3ter client instance.

        This automatically infers the following arguments from their corresponding environment variables if they are not provided:
        - `api_key` from `M3TER_API_KEY`
        - `api_secret` from `M3TER_API_SECRET`
        - `token` from `M3TER_API_TOKEN`
        - `org_id` from `M3TER_ORG_ID`
        """
        if api_key is None:
            api_key = os.environ.get("M3TER_API_KEY")
        if api_key is None:
            raise M3terError(
                "The api_key client option must be set either by passing api_key to the client or by setting the M3TER_API_KEY environment variable"
            )
        self.api_key = api_key

        if api_secret is None:
            api_secret = os.environ.get("M3TER_API_SECRET")
        if api_secret is None:
            raise M3terError(
                "The api_secret client option must be set either by passing api_secret to the client or by setting the M3TER_API_SECRET environment variable"
            )
        self.api_secret = api_secret

        if token is None:
            token = os.environ.get("M3TER_API_TOKEN")
        self.token = token

        if org_id is None:
            org_id = os.environ.get("M3TER_ORG_ID")
        if org_id is None:
            raise M3terError(
                "The org_id client option must be set either by passing org_id to the client or by setting the M3TER_ORG_ID environment variable"
            )
        self.org_id = org_id

        if base_url is None:
            base_url = os.environ.get("M3TER_BASE_URL")
        self._base_url_overridden = base_url is not None
        if base_url is None:
            base_url = f"https://api.m3ter.com"

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
    def authentication(self) -> AsyncAuthenticationResource:
        from .resources.authentication import AsyncAuthenticationResource

        return AsyncAuthenticationResource(self)

    @cached_property
    def accounts(self) -> AsyncAccountsResource:
        from .resources.accounts import AsyncAccountsResource

        return AsyncAccountsResource(self)

    @cached_property
    def account_plans(self) -> AsyncAccountPlansResource:
        from .resources.account_plans import AsyncAccountPlansResource

        return AsyncAccountPlansResource(self)

    @cached_property
    def aggregations(self) -> AsyncAggregationsResource:
        from .resources.aggregations import AsyncAggregationsResource

        return AsyncAggregationsResource(self)

    @cached_property
    def balances(self) -> AsyncBalancesResource:
        from .resources.balances import AsyncBalancesResource

        return AsyncBalancesResource(self)

    @cached_property
    def bills(self) -> AsyncBillsResource:
        from .resources.bills import AsyncBillsResource

        return AsyncBillsResource(self)

    @cached_property
    def bill_config(self) -> AsyncBillConfigResource:
        from .resources.bill_config import AsyncBillConfigResource

        return AsyncBillConfigResource(self)

    @cached_property
    def commitments(self) -> AsyncCommitmentsResource:
        from .resources.commitments import AsyncCommitmentsResource

        return AsyncCommitmentsResource(self)

    @cached_property
    def bill_jobs(self) -> AsyncBillJobsResource:
        from .resources.bill_jobs import AsyncBillJobsResource

        return AsyncBillJobsResource(self)

    @cached_property
    def charges(self) -> AsyncChargesResource:
        from .resources.charges import AsyncChargesResource

        return AsyncChargesResource(self)

    @cached_property
    def compound_aggregations(self) -> AsyncCompoundAggregationsResource:
        from .resources.compound_aggregations import AsyncCompoundAggregationsResource

        return AsyncCompoundAggregationsResource(self)

    @cached_property
    def contracts(self) -> AsyncContractsResource:
        from .resources.contracts import AsyncContractsResource

        return AsyncContractsResource(self)

    @cached_property
    def counters(self) -> AsyncCountersResource:
        from .resources.counters import AsyncCountersResource

        return AsyncCountersResource(self)

    @cached_property
    def counter_adjustments(self) -> AsyncCounterAdjustmentsResource:
        from .resources.counter_adjustments import AsyncCounterAdjustmentsResource

        return AsyncCounterAdjustmentsResource(self)

    @cached_property
    def counter_pricings(self) -> AsyncCounterPricingsResource:
        from .resources.counter_pricings import AsyncCounterPricingsResource

        return AsyncCounterPricingsResource(self)

    @cached_property
    def credit_reasons(self) -> AsyncCreditReasonsResource:
        from .resources.credit_reasons import AsyncCreditReasonsResource

        return AsyncCreditReasonsResource(self)

    @cached_property
    def currencies(self) -> AsyncCurrenciesResource:
        from .resources.currencies import AsyncCurrenciesResource

        return AsyncCurrenciesResource(self)

    @cached_property
    def custom_fields(self) -> AsyncCustomFieldsResource:
        from .resources.custom_fields import AsyncCustomFieldsResource

        return AsyncCustomFieldsResource(self)

    @cached_property
    def data_exports(self) -> AsyncDataExportsResource:
        from .resources.data_exports import AsyncDataExportsResource

        return AsyncDataExportsResource(self)

    @cached_property
    def debit_reasons(self) -> AsyncDebitReasonsResource:
        from .resources.debit_reasons import AsyncDebitReasonsResource

        return AsyncDebitReasonsResource(self)

    @cached_property
    def events(self) -> AsyncEventsResource:
        from .resources.events import AsyncEventsResource

        return AsyncEventsResource(self)

    @cached_property
    def external_mappings(self) -> AsyncExternalMappingsResource:
        from .resources.external_mappings import AsyncExternalMappingsResource

        return AsyncExternalMappingsResource(self)

    @cached_property
    def integration_configurations(self) -> AsyncIntegrationConfigurationsResource:
        from .resources.integration_configurations import AsyncIntegrationConfigurationsResource

        return AsyncIntegrationConfigurationsResource(self)

    @cached_property
    def lookup_tables(self) -> AsyncLookupTablesResource:
        from .resources.lookup_tables import AsyncLookupTablesResource

        return AsyncLookupTablesResource(self)

    @cached_property
    def meters(self) -> AsyncMetersResource:
        from .resources.meters import AsyncMetersResource

        return AsyncMetersResource(self)

    @cached_property
    def notification_configurations(self) -> AsyncNotificationConfigurationsResource:
        from .resources.notification_configurations import AsyncNotificationConfigurationsResource

        return AsyncNotificationConfigurationsResource(self)

    @cached_property
    def organization_config(self) -> AsyncOrganizationConfigResource:
        from .resources.organization_config import AsyncOrganizationConfigResource

        return AsyncOrganizationConfigResource(self)

    @cached_property
    def permission_policies(self) -> AsyncPermissionPoliciesResource:
        from .resources.permission_policies import AsyncPermissionPoliciesResource

        return AsyncPermissionPoliciesResource(self)

    @cached_property
    def plans(self) -> AsyncPlansResource:
        from .resources.plans import AsyncPlansResource

        return AsyncPlansResource(self)

    @cached_property
    def plan_groups(self) -> AsyncPlanGroupsResource:
        from .resources.plan_groups import AsyncPlanGroupsResource

        return AsyncPlanGroupsResource(self)

    @cached_property
    def plan_group_links(self) -> AsyncPlanGroupLinksResource:
        from .resources.plan_group_links import AsyncPlanGroupLinksResource

        return AsyncPlanGroupLinksResource(self)

    @cached_property
    def plan_templates(self) -> AsyncPlanTemplatesResource:
        from .resources.plan_templates import AsyncPlanTemplatesResource

        return AsyncPlanTemplatesResource(self)

    @cached_property
    def pricings(self) -> AsyncPricingsResource:
        from .resources.pricings import AsyncPricingsResource

        return AsyncPricingsResource(self)

    @cached_property
    def products(self) -> AsyncProductsResource:
        from .resources.products import AsyncProductsResource

        return AsyncProductsResource(self)

    @cached_property
    def resource_groups(self) -> AsyncResourceGroupsResource:
        from .resources.resource_groups import AsyncResourceGroupsResource

        return AsyncResourceGroupsResource(self)

    @cached_property
    def scheduled_event_configurations(self) -> AsyncScheduledEventConfigurationsResource:
        from .resources.scheduled_event_configurations import AsyncScheduledEventConfigurationsResource

        return AsyncScheduledEventConfigurationsResource(self)

    @cached_property
    def statements(self) -> AsyncStatementsResource:
        from .resources.statements import AsyncStatementsResource

        return AsyncStatementsResource(self)

    @cached_property
    def transaction_types(self) -> AsyncTransactionTypesResource:
        from .resources.transaction_types import AsyncTransactionTypesResource

        return AsyncTransactionTypesResource(self)

    @cached_property
    def usage(self) -> AsyncUsageResource:
        from .resources.usage import AsyncUsageResource

        return AsyncUsageResource(self)

    @cached_property
    def users(self) -> AsyncUsersResource:
        from .resources.users import AsyncUsersResource

        return AsyncUsersResource(self)

    @cached_property
    def webhooks(self) -> AsyncWebhooksResource:
        from .resources.webhooks import AsyncWebhooksResource

        return AsyncWebhooksResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncM3terWithRawResponse:
        return AsyncM3terWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncM3terWithStreamedResponse:
        return AsyncM3terWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        token = self.token
        if token is None:
            return {}
        return {"Authorization": f"Bearer {token}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    @override
    def _validate_headers(self, headers: Headers, custom_headers: Headers) -> None:
        if headers.get("Authorization") or isinstance(custom_headers.get("Authorization"), Omit):
            return

        raise TypeError(
            '"Could not resolve authentication method. Expected the token to be set. Or for the `Authorization` headers to be explicitly omitted"'
        )

    def copy(
        self,
        *,
        api_key: str | None = None,
        api_secret: str | None = None,
        token: str | None = None,
        org_id: str | None = None,
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
        client = self.__class__(
            api_key=api_key or self.api_key,
            api_secret=api_secret or self.api_secret,
            token=token or self.token,
            org_id=org_id or self.org_id,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )
        client._base_url_overridden = self._base_url_overridden or base_url is not None
        return client

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    def _get_org_id_path_param(self) -> str:
        return self.org_id

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


class M3terWithRawResponse:
    _client: M3ter

    def __init__(self, client: M3ter) -> None:
        self._client = client

    @cached_property
    def authentication(self) -> authentication.AuthenticationResourceWithRawResponse:
        from .resources.authentication import AuthenticationResourceWithRawResponse

        return AuthenticationResourceWithRawResponse(self._client.authentication)

    @cached_property
    def accounts(self) -> accounts.AccountsResourceWithRawResponse:
        from .resources.accounts import AccountsResourceWithRawResponse

        return AccountsResourceWithRawResponse(self._client.accounts)

    @cached_property
    def account_plans(self) -> account_plans.AccountPlansResourceWithRawResponse:
        from .resources.account_plans import AccountPlansResourceWithRawResponse

        return AccountPlansResourceWithRawResponse(self._client.account_plans)

    @cached_property
    def aggregations(self) -> aggregations.AggregationsResourceWithRawResponse:
        from .resources.aggregations import AggregationsResourceWithRawResponse

        return AggregationsResourceWithRawResponse(self._client.aggregations)

    @cached_property
    def balances(self) -> balances.BalancesResourceWithRawResponse:
        from .resources.balances import BalancesResourceWithRawResponse

        return BalancesResourceWithRawResponse(self._client.balances)

    @cached_property
    def bills(self) -> bills.BillsResourceWithRawResponse:
        from .resources.bills import BillsResourceWithRawResponse

        return BillsResourceWithRawResponse(self._client.bills)

    @cached_property
    def bill_config(self) -> bill_config.BillConfigResourceWithRawResponse:
        from .resources.bill_config import BillConfigResourceWithRawResponse

        return BillConfigResourceWithRawResponse(self._client.bill_config)

    @cached_property
    def commitments(self) -> commitments.CommitmentsResourceWithRawResponse:
        from .resources.commitments import CommitmentsResourceWithRawResponse

        return CommitmentsResourceWithRawResponse(self._client.commitments)

    @cached_property
    def bill_jobs(self) -> bill_jobs.BillJobsResourceWithRawResponse:
        from .resources.bill_jobs import BillJobsResourceWithRawResponse

        return BillJobsResourceWithRawResponse(self._client.bill_jobs)

    @cached_property
    def charges(self) -> charges.ChargesResourceWithRawResponse:
        from .resources.charges import ChargesResourceWithRawResponse

        return ChargesResourceWithRawResponse(self._client.charges)

    @cached_property
    def compound_aggregations(self) -> compound_aggregations.CompoundAggregationsResourceWithRawResponse:
        from .resources.compound_aggregations import CompoundAggregationsResourceWithRawResponse

        return CompoundAggregationsResourceWithRawResponse(self._client.compound_aggregations)

    @cached_property
    def contracts(self) -> contracts.ContractsResourceWithRawResponse:
        from .resources.contracts import ContractsResourceWithRawResponse

        return ContractsResourceWithRawResponse(self._client.contracts)

    @cached_property
    def counters(self) -> counters.CountersResourceWithRawResponse:
        from .resources.counters import CountersResourceWithRawResponse

        return CountersResourceWithRawResponse(self._client.counters)

    @cached_property
    def counter_adjustments(self) -> counter_adjustments.CounterAdjustmentsResourceWithRawResponse:
        from .resources.counter_adjustments import CounterAdjustmentsResourceWithRawResponse

        return CounterAdjustmentsResourceWithRawResponse(self._client.counter_adjustments)

    @cached_property
    def counter_pricings(self) -> counter_pricings.CounterPricingsResourceWithRawResponse:
        from .resources.counter_pricings import CounterPricingsResourceWithRawResponse

        return CounterPricingsResourceWithRawResponse(self._client.counter_pricings)

    @cached_property
    def credit_reasons(self) -> credit_reasons.CreditReasonsResourceWithRawResponse:
        from .resources.credit_reasons import CreditReasonsResourceWithRawResponse

        return CreditReasonsResourceWithRawResponse(self._client.credit_reasons)

    @cached_property
    def currencies(self) -> currencies.CurrenciesResourceWithRawResponse:
        from .resources.currencies import CurrenciesResourceWithRawResponse

        return CurrenciesResourceWithRawResponse(self._client.currencies)

    @cached_property
    def custom_fields(self) -> custom_fields.CustomFieldsResourceWithRawResponse:
        from .resources.custom_fields import CustomFieldsResourceWithRawResponse

        return CustomFieldsResourceWithRawResponse(self._client.custom_fields)

    @cached_property
    def data_exports(self) -> data_exports.DataExportsResourceWithRawResponse:
        from .resources.data_exports import DataExportsResourceWithRawResponse

        return DataExportsResourceWithRawResponse(self._client.data_exports)

    @cached_property
    def debit_reasons(self) -> debit_reasons.DebitReasonsResourceWithRawResponse:
        from .resources.debit_reasons import DebitReasonsResourceWithRawResponse

        return DebitReasonsResourceWithRawResponse(self._client.debit_reasons)

    @cached_property
    def events(self) -> events.EventsResourceWithRawResponse:
        from .resources.events import EventsResourceWithRawResponse

        return EventsResourceWithRawResponse(self._client.events)

    @cached_property
    def external_mappings(self) -> external_mappings.ExternalMappingsResourceWithRawResponse:
        from .resources.external_mappings import ExternalMappingsResourceWithRawResponse

        return ExternalMappingsResourceWithRawResponse(self._client.external_mappings)

    @cached_property
    def integration_configurations(self) -> integration_configurations.IntegrationConfigurationsResourceWithRawResponse:
        from .resources.integration_configurations import IntegrationConfigurationsResourceWithRawResponse

        return IntegrationConfigurationsResourceWithRawResponse(self._client.integration_configurations)

    @cached_property
    def lookup_tables(self) -> lookup_tables.LookupTablesResourceWithRawResponse:
        from .resources.lookup_tables import LookupTablesResourceWithRawResponse

        return LookupTablesResourceWithRawResponse(self._client.lookup_tables)

    @cached_property
    def meters(self) -> meters.MetersResourceWithRawResponse:
        from .resources.meters import MetersResourceWithRawResponse

        return MetersResourceWithRawResponse(self._client.meters)

    @cached_property
    def notification_configurations(
        self,
    ) -> notification_configurations.NotificationConfigurationsResourceWithRawResponse:
        from .resources.notification_configurations import NotificationConfigurationsResourceWithRawResponse

        return NotificationConfigurationsResourceWithRawResponse(self._client.notification_configurations)

    @cached_property
    def organization_config(self) -> organization_config.OrganizationConfigResourceWithRawResponse:
        from .resources.organization_config import OrganizationConfigResourceWithRawResponse

        return OrganizationConfigResourceWithRawResponse(self._client.organization_config)

    @cached_property
    def permission_policies(self) -> permission_policies.PermissionPoliciesResourceWithRawResponse:
        from .resources.permission_policies import PermissionPoliciesResourceWithRawResponse

        return PermissionPoliciesResourceWithRawResponse(self._client.permission_policies)

    @cached_property
    def plans(self) -> plans.PlansResourceWithRawResponse:
        from .resources.plans import PlansResourceWithRawResponse

        return PlansResourceWithRawResponse(self._client.plans)

    @cached_property
    def plan_groups(self) -> plan_groups.PlanGroupsResourceWithRawResponse:
        from .resources.plan_groups import PlanGroupsResourceWithRawResponse

        return PlanGroupsResourceWithRawResponse(self._client.plan_groups)

    @cached_property
    def plan_group_links(self) -> plan_group_links.PlanGroupLinksResourceWithRawResponse:
        from .resources.plan_group_links import PlanGroupLinksResourceWithRawResponse

        return PlanGroupLinksResourceWithRawResponse(self._client.plan_group_links)

    @cached_property
    def plan_templates(self) -> plan_templates.PlanTemplatesResourceWithRawResponse:
        from .resources.plan_templates import PlanTemplatesResourceWithRawResponse

        return PlanTemplatesResourceWithRawResponse(self._client.plan_templates)

    @cached_property
    def pricings(self) -> pricings.PricingsResourceWithRawResponse:
        from .resources.pricings import PricingsResourceWithRawResponse

        return PricingsResourceWithRawResponse(self._client.pricings)

    @cached_property
    def products(self) -> products.ProductsResourceWithRawResponse:
        from .resources.products import ProductsResourceWithRawResponse

        return ProductsResourceWithRawResponse(self._client.products)

    @cached_property
    def resource_groups(self) -> resource_groups.ResourceGroupsResourceWithRawResponse:
        from .resources.resource_groups import ResourceGroupsResourceWithRawResponse

        return ResourceGroupsResourceWithRawResponse(self._client.resource_groups)

    @cached_property
    def scheduled_event_configurations(
        self,
    ) -> scheduled_event_configurations.ScheduledEventConfigurationsResourceWithRawResponse:
        from .resources.scheduled_event_configurations import ScheduledEventConfigurationsResourceWithRawResponse

        return ScheduledEventConfigurationsResourceWithRawResponse(self._client.scheduled_event_configurations)

    @cached_property
    def statements(self) -> statements.StatementsResourceWithRawResponse:
        from .resources.statements import StatementsResourceWithRawResponse

        return StatementsResourceWithRawResponse(self._client.statements)

    @cached_property
    def transaction_types(self) -> transaction_types.TransactionTypesResourceWithRawResponse:
        from .resources.transaction_types import TransactionTypesResourceWithRawResponse

        return TransactionTypesResourceWithRawResponse(self._client.transaction_types)

    @cached_property
    def usage(self) -> usage.UsageResourceWithRawResponse:
        from .resources.usage import UsageResourceWithRawResponse

        return UsageResourceWithRawResponse(self._client.usage)

    @cached_property
    def users(self) -> users.UsersResourceWithRawResponse:
        from .resources.users import UsersResourceWithRawResponse

        return UsersResourceWithRawResponse(self._client.users)

    @cached_property
    def webhooks(self) -> webhooks.WebhooksResourceWithRawResponse:
        from .resources.webhooks import WebhooksResourceWithRawResponse

        return WebhooksResourceWithRawResponse(self._client.webhooks)


class AsyncM3terWithRawResponse:
    _client: AsyncM3ter

    def __init__(self, client: AsyncM3ter) -> None:
        self._client = client

    @cached_property
    def authentication(self) -> authentication.AsyncAuthenticationResourceWithRawResponse:
        from .resources.authentication import AsyncAuthenticationResourceWithRawResponse

        return AsyncAuthenticationResourceWithRawResponse(self._client.authentication)

    @cached_property
    def accounts(self) -> accounts.AsyncAccountsResourceWithRawResponse:
        from .resources.accounts import AsyncAccountsResourceWithRawResponse

        return AsyncAccountsResourceWithRawResponse(self._client.accounts)

    @cached_property
    def account_plans(self) -> account_plans.AsyncAccountPlansResourceWithRawResponse:
        from .resources.account_plans import AsyncAccountPlansResourceWithRawResponse

        return AsyncAccountPlansResourceWithRawResponse(self._client.account_plans)

    @cached_property
    def aggregations(self) -> aggregations.AsyncAggregationsResourceWithRawResponse:
        from .resources.aggregations import AsyncAggregationsResourceWithRawResponse

        return AsyncAggregationsResourceWithRawResponse(self._client.aggregations)

    @cached_property
    def balances(self) -> balances.AsyncBalancesResourceWithRawResponse:
        from .resources.balances import AsyncBalancesResourceWithRawResponse

        return AsyncBalancesResourceWithRawResponse(self._client.balances)

    @cached_property
    def bills(self) -> bills.AsyncBillsResourceWithRawResponse:
        from .resources.bills import AsyncBillsResourceWithRawResponse

        return AsyncBillsResourceWithRawResponse(self._client.bills)

    @cached_property
    def bill_config(self) -> bill_config.AsyncBillConfigResourceWithRawResponse:
        from .resources.bill_config import AsyncBillConfigResourceWithRawResponse

        return AsyncBillConfigResourceWithRawResponse(self._client.bill_config)

    @cached_property
    def commitments(self) -> commitments.AsyncCommitmentsResourceWithRawResponse:
        from .resources.commitments import AsyncCommitmentsResourceWithRawResponse

        return AsyncCommitmentsResourceWithRawResponse(self._client.commitments)

    @cached_property
    def bill_jobs(self) -> bill_jobs.AsyncBillJobsResourceWithRawResponse:
        from .resources.bill_jobs import AsyncBillJobsResourceWithRawResponse

        return AsyncBillJobsResourceWithRawResponse(self._client.bill_jobs)

    @cached_property
    def charges(self) -> charges.AsyncChargesResourceWithRawResponse:
        from .resources.charges import AsyncChargesResourceWithRawResponse

        return AsyncChargesResourceWithRawResponse(self._client.charges)

    @cached_property
    def compound_aggregations(self) -> compound_aggregations.AsyncCompoundAggregationsResourceWithRawResponse:
        from .resources.compound_aggregations import AsyncCompoundAggregationsResourceWithRawResponse

        return AsyncCompoundAggregationsResourceWithRawResponse(self._client.compound_aggregations)

    @cached_property
    def contracts(self) -> contracts.AsyncContractsResourceWithRawResponse:
        from .resources.contracts import AsyncContractsResourceWithRawResponse

        return AsyncContractsResourceWithRawResponse(self._client.contracts)

    @cached_property
    def counters(self) -> counters.AsyncCountersResourceWithRawResponse:
        from .resources.counters import AsyncCountersResourceWithRawResponse

        return AsyncCountersResourceWithRawResponse(self._client.counters)

    @cached_property
    def counter_adjustments(self) -> counter_adjustments.AsyncCounterAdjustmentsResourceWithRawResponse:
        from .resources.counter_adjustments import AsyncCounterAdjustmentsResourceWithRawResponse

        return AsyncCounterAdjustmentsResourceWithRawResponse(self._client.counter_adjustments)

    @cached_property
    def counter_pricings(self) -> counter_pricings.AsyncCounterPricingsResourceWithRawResponse:
        from .resources.counter_pricings import AsyncCounterPricingsResourceWithRawResponse

        return AsyncCounterPricingsResourceWithRawResponse(self._client.counter_pricings)

    @cached_property
    def credit_reasons(self) -> credit_reasons.AsyncCreditReasonsResourceWithRawResponse:
        from .resources.credit_reasons import AsyncCreditReasonsResourceWithRawResponse

        return AsyncCreditReasonsResourceWithRawResponse(self._client.credit_reasons)

    @cached_property
    def currencies(self) -> currencies.AsyncCurrenciesResourceWithRawResponse:
        from .resources.currencies import AsyncCurrenciesResourceWithRawResponse

        return AsyncCurrenciesResourceWithRawResponse(self._client.currencies)

    @cached_property
    def custom_fields(self) -> custom_fields.AsyncCustomFieldsResourceWithRawResponse:
        from .resources.custom_fields import AsyncCustomFieldsResourceWithRawResponse

        return AsyncCustomFieldsResourceWithRawResponse(self._client.custom_fields)

    @cached_property
    def data_exports(self) -> data_exports.AsyncDataExportsResourceWithRawResponse:
        from .resources.data_exports import AsyncDataExportsResourceWithRawResponse

        return AsyncDataExportsResourceWithRawResponse(self._client.data_exports)

    @cached_property
    def debit_reasons(self) -> debit_reasons.AsyncDebitReasonsResourceWithRawResponse:
        from .resources.debit_reasons import AsyncDebitReasonsResourceWithRawResponse

        return AsyncDebitReasonsResourceWithRawResponse(self._client.debit_reasons)

    @cached_property
    def events(self) -> events.AsyncEventsResourceWithRawResponse:
        from .resources.events import AsyncEventsResourceWithRawResponse

        return AsyncEventsResourceWithRawResponse(self._client.events)

    @cached_property
    def external_mappings(self) -> external_mappings.AsyncExternalMappingsResourceWithRawResponse:
        from .resources.external_mappings import AsyncExternalMappingsResourceWithRawResponse

        return AsyncExternalMappingsResourceWithRawResponse(self._client.external_mappings)

    @cached_property
    def integration_configurations(
        self,
    ) -> integration_configurations.AsyncIntegrationConfigurationsResourceWithRawResponse:
        from .resources.integration_configurations import AsyncIntegrationConfigurationsResourceWithRawResponse

        return AsyncIntegrationConfigurationsResourceWithRawResponse(self._client.integration_configurations)

    @cached_property
    def lookup_tables(self) -> lookup_tables.AsyncLookupTablesResourceWithRawResponse:
        from .resources.lookup_tables import AsyncLookupTablesResourceWithRawResponse

        return AsyncLookupTablesResourceWithRawResponse(self._client.lookup_tables)

    @cached_property
    def meters(self) -> meters.AsyncMetersResourceWithRawResponse:
        from .resources.meters import AsyncMetersResourceWithRawResponse

        return AsyncMetersResourceWithRawResponse(self._client.meters)

    @cached_property
    def notification_configurations(
        self,
    ) -> notification_configurations.AsyncNotificationConfigurationsResourceWithRawResponse:
        from .resources.notification_configurations import AsyncNotificationConfigurationsResourceWithRawResponse

        return AsyncNotificationConfigurationsResourceWithRawResponse(self._client.notification_configurations)

    @cached_property
    def organization_config(self) -> organization_config.AsyncOrganizationConfigResourceWithRawResponse:
        from .resources.organization_config import AsyncOrganizationConfigResourceWithRawResponse

        return AsyncOrganizationConfigResourceWithRawResponse(self._client.organization_config)

    @cached_property
    def permission_policies(self) -> permission_policies.AsyncPermissionPoliciesResourceWithRawResponse:
        from .resources.permission_policies import AsyncPermissionPoliciesResourceWithRawResponse

        return AsyncPermissionPoliciesResourceWithRawResponse(self._client.permission_policies)

    @cached_property
    def plans(self) -> plans.AsyncPlansResourceWithRawResponse:
        from .resources.plans import AsyncPlansResourceWithRawResponse

        return AsyncPlansResourceWithRawResponse(self._client.plans)

    @cached_property
    def plan_groups(self) -> plan_groups.AsyncPlanGroupsResourceWithRawResponse:
        from .resources.plan_groups import AsyncPlanGroupsResourceWithRawResponse

        return AsyncPlanGroupsResourceWithRawResponse(self._client.plan_groups)

    @cached_property
    def plan_group_links(self) -> plan_group_links.AsyncPlanGroupLinksResourceWithRawResponse:
        from .resources.plan_group_links import AsyncPlanGroupLinksResourceWithRawResponse

        return AsyncPlanGroupLinksResourceWithRawResponse(self._client.plan_group_links)

    @cached_property
    def plan_templates(self) -> plan_templates.AsyncPlanTemplatesResourceWithRawResponse:
        from .resources.plan_templates import AsyncPlanTemplatesResourceWithRawResponse

        return AsyncPlanTemplatesResourceWithRawResponse(self._client.plan_templates)

    @cached_property
    def pricings(self) -> pricings.AsyncPricingsResourceWithRawResponse:
        from .resources.pricings import AsyncPricingsResourceWithRawResponse

        return AsyncPricingsResourceWithRawResponse(self._client.pricings)

    @cached_property
    def products(self) -> products.AsyncProductsResourceWithRawResponse:
        from .resources.products import AsyncProductsResourceWithRawResponse

        return AsyncProductsResourceWithRawResponse(self._client.products)

    @cached_property
    def resource_groups(self) -> resource_groups.AsyncResourceGroupsResourceWithRawResponse:
        from .resources.resource_groups import AsyncResourceGroupsResourceWithRawResponse

        return AsyncResourceGroupsResourceWithRawResponse(self._client.resource_groups)

    @cached_property
    def scheduled_event_configurations(
        self,
    ) -> scheduled_event_configurations.AsyncScheduledEventConfigurationsResourceWithRawResponse:
        from .resources.scheduled_event_configurations import AsyncScheduledEventConfigurationsResourceWithRawResponse

        return AsyncScheduledEventConfigurationsResourceWithRawResponse(self._client.scheduled_event_configurations)

    @cached_property
    def statements(self) -> statements.AsyncStatementsResourceWithRawResponse:
        from .resources.statements import AsyncStatementsResourceWithRawResponse

        return AsyncStatementsResourceWithRawResponse(self._client.statements)

    @cached_property
    def transaction_types(self) -> transaction_types.AsyncTransactionTypesResourceWithRawResponse:
        from .resources.transaction_types import AsyncTransactionTypesResourceWithRawResponse

        return AsyncTransactionTypesResourceWithRawResponse(self._client.transaction_types)

    @cached_property
    def usage(self) -> usage.AsyncUsageResourceWithRawResponse:
        from .resources.usage import AsyncUsageResourceWithRawResponse

        return AsyncUsageResourceWithRawResponse(self._client.usage)

    @cached_property
    def users(self) -> users.AsyncUsersResourceWithRawResponse:
        from .resources.users import AsyncUsersResourceWithRawResponse

        return AsyncUsersResourceWithRawResponse(self._client.users)

    @cached_property
    def webhooks(self) -> webhooks.AsyncWebhooksResourceWithRawResponse:
        from .resources.webhooks import AsyncWebhooksResourceWithRawResponse

        return AsyncWebhooksResourceWithRawResponse(self._client.webhooks)


class M3terWithStreamedResponse:
    _client: M3ter

    def __init__(self, client: M3ter) -> None:
        self._client = client

    @cached_property
    def authentication(self) -> authentication.AuthenticationResourceWithStreamingResponse:
        from .resources.authentication import AuthenticationResourceWithStreamingResponse

        return AuthenticationResourceWithStreamingResponse(self._client.authentication)

    @cached_property
    def accounts(self) -> accounts.AccountsResourceWithStreamingResponse:
        from .resources.accounts import AccountsResourceWithStreamingResponse

        return AccountsResourceWithStreamingResponse(self._client.accounts)

    @cached_property
    def account_plans(self) -> account_plans.AccountPlansResourceWithStreamingResponse:
        from .resources.account_plans import AccountPlansResourceWithStreamingResponse

        return AccountPlansResourceWithStreamingResponse(self._client.account_plans)

    @cached_property
    def aggregations(self) -> aggregations.AggregationsResourceWithStreamingResponse:
        from .resources.aggregations import AggregationsResourceWithStreamingResponse

        return AggregationsResourceWithStreamingResponse(self._client.aggregations)

    @cached_property
    def balances(self) -> balances.BalancesResourceWithStreamingResponse:
        from .resources.balances import BalancesResourceWithStreamingResponse

        return BalancesResourceWithStreamingResponse(self._client.balances)

    @cached_property
    def bills(self) -> bills.BillsResourceWithStreamingResponse:
        from .resources.bills import BillsResourceWithStreamingResponse

        return BillsResourceWithStreamingResponse(self._client.bills)

    @cached_property
    def bill_config(self) -> bill_config.BillConfigResourceWithStreamingResponse:
        from .resources.bill_config import BillConfigResourceWithStreamingResponse

        return BillConfigResourceWithStreamingResponse(self._client.bill_config)

    @cached_property
    def commitments(self) -> commitments.CommitmentsResourceWithStreamingResponse:
        from .resources.commitments import CommitmentsResourceWithStreamingResponse

        return CommitmentsResourceWithStreamingResponse(self._client.commitments)

    @cached_property
    def bill_jobs(self) -> bill_jobs.BillJobsResourceWithStreamingResponse:
        from .resources.bill_jobs import BillJobsResourceWithStreamingResponse

        return BillJobsResourceWithStreamingResponse(self._client.bill_jobs)

    @cached_property
    def charges(self) -> charges.ChargesResourceWithStreamingResponse:
        from .resources.charges import ChargesResourceWithStreamingResponse

        return ChargesResourceWithStreamingResponse(self._client.charges)

    @cached_property
    def compound_aggregations(self) -> compound_aggregations.CompoundAggregationsResourceWithStreamingResponse:
        from .resources.compound_aggregations import CompoundAggregationsResourceWithStreamingResponse

        return CompoundAggregationsResourceWithStreamingResponse(self._client.compound_aggregations)

    @cached_property
    def contracts(self) -> contracts.ContractsResourceWithStreamingResponse:
        from .resources.contracts import ContractsResourceWithStreamingResponse

        return ContractsResourceWithStreamingResponse(self._client.contracts)

    @cached_property
    def counters(self) -> counters.CountersResourceWithStreamingResponse:
        from .resources.counters import CountersResourceWithStreamingResponse

        return CountersResourceWithStreamingResponse(self._client.counters)

    @cached_property
    def counter_adjustments(self) -> counter_adjustments.CounterAdjustmentsResourceWithStreamingResponse:
        from .resources.counter_adjustments import CounterAdjustmentsResourceWithStreamingResponse

        return CounterAdjustmentsResourceWithStreamingResponse(self._client.counter_adjustments)

    @cached_property
    def counter_pricings(self) -> counter_pricings.CounterPricingsResourceWithStreamingResponse:
        from .resources.counter_pricings import CounterPricingsResourceWithStreamingResponse

        return CounterPricingsResourceWithStreamingResponse(self._client.counter_pricings)

    @cached_property
    def credit_reasons(self) -> credit_reasons.CreditReasonsResourceWithStreamingResponse:
        from .resources.credit_reasons import CreditReasonsResourceWithStreamingResponse

        return CreditReasonsResourceWithStreamingResponse(self._client.credit_reasons)

    @cached_property
    def currencies(self) -> currencies.CurrenciesResourceWithStreamingResponse:
        from .resources.currencies import CurrenciesResourceWithStreamingResponse

        return CurrenciesResourceWithStreamingResponse(self._client.currencies)

    @cached_property
    def custom_fields(self) -> custom_fields.CustomFieldsResourceWithStreamingResponse:
        from .resources.custom_fields import CustomFieldsResourceWithStreamingResponse

        return CustomFieldsResourceWithStreamingResponse(self._client.custom_fields)

    @cached_property
    def data_exports(self) -> data_exports.DataExportsResourceWithStreamingResponse:
        from .resources.data_exports import DataExportsResourceWithStreamingResponse

        return DataExportsResourceWithStreamingResponse(self._client.data_exports)

    @cached_property
    def debit_reasons(self) -> debit_reasons.DebitReasonsResourceWithStreamingResponse:
        from .resources.debit_reasons import DebitReasonsResourceWithStreamingResponse

        return DebitReasonsResourceWithStreamingResponse(self._client.debit_reasons)

    @cached_property
    def events(self) -> events.EventsResourceWithStreamingResponse:
        from .resources.events import EventsResourceWithStreamingResponse

        return EventsResourceWithStreamingResponse(self._client.events)

    @cached_property
    def external_mappings(self) -> external_mappings.ExternalMappingsResourceWithStreamingResponse:
        from .resources.external_mappings import ExternalMappingsResourceWithStreamingResponse

        return ExternalMappingsResourceWithStreamingResponse(self._client.external_mappings)

    @cached_property
    def integration_configurations(
        self,
    ) -> integration_configurations.IntegrationConfigurationsResourceWithStreamingResponse:
        from .resources.integration_configurations import IntegrationConfigurationsResourceWithStreamingResponse

        return IntegrationConfigurationsResourceWithStreamingResponse(self._client.integration_configurations)

    @cached_property
    def lookup_tables(self) -> lookup_tables.LookupTablesResourceWithStreamingResponse:
        from .resources.lookup_tables import LookupTablesResourceWithStreamingResponse

        return LookupTablesResourceWithStreamingResponse(self._client.lookup_tables)

    @cached_property
    def meters(self) -> meters.MetersResourceWithStreamingResponse:
        from .resources.meters import MetersResourceWithStreamingResponse

        return MetersResourceWithStreamingResponse(self._client.meters)

    @cached_property
    def notification_configurations(
        self,
    ) -> notification_configurations.NotificationConfigurationsResourceWithStreamingResponse:
        from .resources.notification_configurations import NotificationConfigurationsResourceWithStreamingResponse

        return NotificationConfigurationsResourceWithStreamingResponse(self._client.notification_configurations)

    @cached_property
    def organization_config(self) -> organization_config.OrganizationConfigResourceWithStreamingResponse:
        from .resources.organization_config import OrganizationConfigResourceWithStreamingResponse

        return OrganizationConfigResourceWithStreamingResponse(self._client.organization_config)

    @cached_property
    def permission_policies(self) -> permission_policies.PermissionPoliciesResourceWithStreamingResponse:
        from .resources.permission_policies import PermissionPoliciesResourceWithStreamingResponse

        return PermissionPoliciesResourceWithStreamingResponse(self._client.permission_policies)

    @cached_property
    def plans(self) -> plans.PlansResourceWithStreamingResponse:
        from .resources.plans import PlansResourceWithStreamingResponse

        return PlansResourceWithStreamingResponse(self._client.plans)

    @cached_property
    def plan_groups(self) -> plan_groups.PlanGroupsResourceWithStreamingResponse:
        from .resources.plan_groups import PlanGroupsResourceWithStreamingResponse

        return PlanGroupsResourceWithStreamingResponse(self._client.plan_groups)

    @cached_property
    def plan_group_links(self) -> plan_group_links.PlanGroupLinksResourceWithStreamingResponse:
        from .resources.plan_group_links import PlanGroupLinksResourceWithStreamingResponse

        return PlanGroupLinksResourceWithStreamingResponse(self._client.plan_group_links)

    @cached_property
    def plan_templates(self) -> plan_templates.PlanTemplatesResourceWithStreamingResponse:
        from .resources.plan_templates import PlanTemplatesResourceWithStreamingResponse

        return PlanTemplatesResourceWithStreamingResponse(self._client.plan_templates)

    @cached_property
    def pricings(self) -> pricings.PricingsResourceWithStreamingResponse:
        from .resources.pricings import PricingsResourceWithStreamingResponse

        return PricingsResourceWithStreamingResponse(self._client.pricings)

    @cached_property
    def products(self) -> products.ProductsResourceWithStreamingResponse:
        from .resources.products import ProductsResourceWithStreamingResponse

        return ProductsResourceWithStreamingResponse(self._client.products)

    @cached_property
    def resource_groups(self) -> resource_groups.ResourceGroupsResourceWithStreamingResponse:
        from .resources.resource_groups import ResourceGroupsResourceWithStreamingResponse

        return ResourceGroupsResourceWithStreamingResponse(self._client.resource_groups)

    @cached_property
    def scheduled_event_configurations(
        self,
    ) -> scheduled_event_configurations.ScheduledEventConfigurationsResourceWithStreamingResponse:
        from .resources.scheduled_event_configurations import ScheduledEventConfigurationsResourceWithStreamingResponse

        return ScheduledEventConfigurationsResourceWithStreamingResponse(self._client.scheduled_event_configurations)

    @cached_property
    def statements(self) -> statements.StatementsResourceWithStreamingResponse:
        from .resources.statements import StatementsResourceWithStreamingResponse

        return StatementsResourceWithStreamingResponse(self._client.statements)

    @cached_property
    def transaction_types(self) -> transaction_types.TransactionTypesResourceWithStreamingResponse:
        from .resources.transaction_types import TransactionTypesResourceWithStreamingResponse

        return TransactionTypesResourceWithStreamingResponse(self._client.transaction_types)

    @cached_property
    def usage(self) -> usage.UsageResourceWithStreamingResponse:
        from .resources.usage import UsageResourceWithStreamingResponse

        return UsageResourceWithStreamingResponse(self._client.usage)

    @cached_property
    def users(self) -> users.UsersResourceWithStreamingResponse:
        from .resources.users import UsersResourceWithStreamingResponse

        return UsersResourceWithStreamingResponse(self._client.users)

    @cached_property
    def webhooks(self) -> webhooks.WebhooksResourceWithStreamingResponse:
        from .resources.webhooks import WebhooksResourceWithStreamingResponse

        return WebhooksResourceWithStreamingResponse(self._client.webhooks)


class AsyncM3terWithStreamedResponse:
    _client: AsyncM3ter

    def __init__(self, client: AsyncM3ter) -> None:
        self._client = client

    @cached_property
    def authentication(self) -> authentication.AsyncAuthenticationResourceWithStreamingResponse:
        from .resources.authentication import AsyncAuthenticationResourceWithStreamingResponse

        return AsyncAuthenticationResourceWithStreamingResponse(self._client.authentication)

    @cached_property
    def accounts(self) -> accounts.AsyncAccountsResourceWithStreamingResponse:
        from .resources.accounts import AsyncAccountsResourceWithStreamingResponse

        return AsyncAccountsResourceWithStreamingResponse(self._client.accounts)

    @cached_property
    def account_plans(self) -> account_plans.AsyncAccountPlansResourceWithStreamingResponse:
        from .resources.account_plans import AsyncAccountPlansResourceWithStreamingResponse

        return AsyncAccountPlansResourceWithStreamingResponse(self._client.account_plans)

    @cached_property
    def aggregations(self) -> aggregations.AsyncAggregationsResourceWithStreamingResponse:
        from .resources.aggregations import AsyncAggregationsResourceWithStreamingResponse

        return AsyncAggregationsResourceWithStreamingResponse(self._client.aggregations)

    @cached_property
    def balances(self) -> balances.AsyncBalancesResourceWithStreamingResponse:
        from .resources.balances import AsyncBalancesResourceWithStreamingResponse

        return AsyncBalancesResourceWithStreamingResponse(self._client.balances)

    @cached_property
    def bills(self) -> bills.AsyncBillsResourceWithStreamingResponse:
        from .resources.bills import AsyncBillsResourceWithStreamingResponse

        return AsyncBillsResourceWithStreamingResponse(self._client.bills)

    @cached_property
    def bill_config(self) -> bill_config.AsyncBillConfigResourceWithStreamingResponse:
        from .resources.bill_config import AsyncBillConfigResourceWithStreamingResponse

        return AsyncBillConfigResourceWithStreamingResponse(self._client.bill_config)

    @cached_property
    def commitments(self) -> commitments.AsyncCommitmentsResourceWithStreamingResponse:
        from .resources.commitments import AsyncCommitmentsResourceWithStreamingResponse

        return AsyncCommitmentsResourceWithStreamingResponse(self._client.commitments)

    @cached_property
    def bill_jobs(self) -> bill_jobs.AsyncBillJobsResourceWithStreamingResponse:
        from .resources.bill_jobs import AsyncBillJobsResourceWithStreamingResponse

        return AsyncBillJobsResourceWithStreamingResponse(self._client.bill_jobs)

    @cached_property
    def charges(self) -> charges.AsyncChargesResourceWithStreamingResponse:
        from .resources.charges import AsyncChargesResourceWithStreamingResponse

        return AsyncChargesResourceWithStreamingResponse(self._client.charges)

    @cached_property
    def compound_aggregations(self) -> compound_aggregations.AsyncCompoundAggregationsResourceWithStreamingResponse:
        from .resources.compound_aggregations import AsyncCompoundAggregationsResourceWithStreamingResponse

        return AsyncCompoundAggregationsResourceWithStreamingResponse(self._client.compound_aggregations)

    @cached_property
    def contracts(self) -> contracts.AsyncContractsResourceWithStreamingResponse:
        from .resources.contracts import AsyncContractsResourceWithStreamingResponse

        return AsyncContractsResourceWithStreamingResponse(self._client.contracts)

    @cached_property
    def counters(self) -> counters.AsyncCountersResourceWithStreamingResponse:
        from .resources.counters import AsyncCountersResourceWithStreamingResponse

        return AsyncCountersResourceWithStreamingResponse(self._client.counters)

    @cached_property
    def counter_adjustments(self) -> counter_adjustments.AsyncCounterAdjustmentsResourceWithStreamingResponse:
        from .resources.counter_adjustments import AsyncCounterAdjustmentsResourceWithStreamingResponse

        return AsyncCounterAdjustmentsResourceWithStreamingResponse(self._client.counter_adjustments)

    @cached_property
    def counter_pricings(self) -> counter_pricings.AsyncCounterPricingsResourceWithStreamingResponse:
        from .resources.counter_pricings import AsyncCounterPricingsResourceWithStreamingResponse

        return AsyncCounterPricingsResourceWithStreamingResponse(self._client.counter_pricings)

    @cached_property
    def credit_reasons(self) -> credit_reasons.AsyncCreditReasonsResourceWithStreamingResponse:
        from .resources.credit_reasons import AsyncCreditReasonsResourceWithStreamingResponse

        return AsyncCreditReasonsResourceWithStreamingResponse(self._client.credit_reasons)

    @cached_property
    def currencies(self) -> currencies.AsyncCurrenciesResourceWithStreamingResponse:
        from .resources.currencies import AsyncCurrenciesResourceWithStreamingResponse

        return AsyncCurrenciesResourceWithStreamingResponse(self._client.currencies)

    @cached_property
    def custom_fields(self) -> custom_fields.AsyncCustomFieldsResourceWithStreamingResponse:
        from .resources.custom_fields import AsyncCustomFieldsResourceWithStreamingResponse

        return AsyncCustomFieldsResourceWithStreamingResponse(self._client.custom_fields)

    @cached_property
    def data_exports(self) -> data_exports.AsyncDataExportsResourceWithStreamingResponse:
        from .resources.data_exports import AsyncDataExportsResourceWithStreamingResponse

        return AsyncDataExportsResourceWithStreamingResponse(self._client.data_exports)

    @cached_property
    def debit_reasons(self) -> debit_reasons.AsyncDebitReasonsResourceWithStreamingResponse:
        from .resources.debit_reasons import AsyncDebitReasonsResourceWithStreamingResponse

        return AsyncDebitReasonsResourceWithStreamingResponse(self._client.debit_reasons)

    @cached_property
    def events(self) -> events.AsyncEventsResourceWithStreamingResponse:
        from .resources.events import AsyncEventsResourceWithStreamingResponse

        return AsyncEventsResourceWithStreamingResponse(self._client.events)

    @cached_property
    def external_mappings(self) -> external_mappings.AsyncExternalMappingsResourceWithStreamingResponse:
        from .resources.external_mappings import AsyncExternalMappingsResourceWithStreamingResponse

        return AsyncExternalMappingsResourceWithStreamingResponse(self._client.external_mappings)

    @cached_property
    def integration_configurations(
        self,
    ) -> integration_configurations.AsyncIntegrationConfigurationsResourceWithStreamingResponse:
        from .resources.integration_configurations import AsyncIntegrationConfigurationsResourceWithStreamingResponse

        return AsyncIntegrationConfigurationsResourceWithStreamingResponse(self._client.integration_configurations)

    @cached_property
    def lookup_tables(self) -> lookup_tables.AsyncLookupTablesResourceWithStreamingResponse:
        from .resources.lookup_tables import AsyncLookupTablesResourceWithStreamingResponse

        return AsyncLookupTablesResourceWithStreamingResponse(self._client.lookup_tables)

    @cached_property
    def meters(self) -> meters.AsyncMetersResourceWithStreamingResponse:
        from .resources.meters import AsyncMetersResourceWithStreamingResponse

        return AsyncMetersResourceWithStreamingResponse(self._client.meters)

    @cached_property
    def notification_configurations(
        self,
    ) -> notification_configurations.AsyncNotificationConfigurationsResourceWithStreamingResponse:
        from .resources.notification_configurations import AsyncNotificationConfigurationsResourceWithStreamingResponse

        return AsyncNotificationConfigurationsResourceWithStreamingResponse(self._client.notification_configurations)

    @cached_property
    def organization_config(self) -> organization_config.AsyncOrganizationConfigResourceWithStreamingResponse:
        from .resources.organization_config import AsyncOrganizationConfigResourceWithStreamingResponse

        return AsyncOrganizationConfigResourceWithStreamingResponse(self._client.organization_config)

    @cached_property
    def permission_policies(self) -> permission_policies.AsyncPermissionPoliciesResourceWithStreamingResponse:
        from .resources.permission_policies import AsyncPermissionPoliciesResourceWithStreamingResponse

        return AsyncPermissionPoliciesResourceWithStreamingResponse(self._client.permission_policies)

    @cached_property
    def plans(self) -> plans.AsyncPlansResourceWithStreamingResponse:
        from .resources.plans import AsyncPlansResourceWithStreamingResponse

        return AsyncPlansResourceWithStreamingResponse(self._client.plans)

    @cached_property
    def plan_groups(self) -> plan_groups.AsyncPlanGroupsResourceWithStreamingResponse:
        from .resources.plan_groups import AsyncPlanGroupsResourceWithStreamingResponse

        return AsyncPlanGroupsResourceWithStreamingResponse(self._client.plan_groups)

    @cached_property
    def plan_group_links(self) -> plan_group_links.AsyncPlanGroupLinksResourceWithStreamingResponse:
        from .resources.plan_group_links import AsyncPlanGroupLinksResourceWithStreamingResponse

        return AsyncPlanGroupLinksResourceWithStreamingResponse(self._client.plan_group_links)

    @cached_property
    def plan_templates(self) -> plan_templates.AsyncPlanTemplatesResourceWithStreamingResponse:
        from .resources.plan_templates import AsyncPlanTemplatesResourceWithStreamingResponse

        return AsyncPlanTemplatesResourceWithStreamingResponse(self._client.plan_templates)

    @cached_property
    def pricings(self) -> pricings.AsyncPricingsResourceWithStreamingResponse:
        from .resources.pricings import AsyncPricingsResourceWithStreamingResponse

        return AsyncPricingsResourceWithStreamingResponse(self._client.pricings)

    @cached_property
    def products(self) -> products.AsyncProductsResourceWithStreamingResponse:
        from .resources.products import AsyncProductsResourceWithStreamingResponse

        return AsyncProductsResourceWithStreamingResponse(self._client.products)

    @cached_property
    def resource_groups(self) -> resource_groups.AsyncResourceGroupsResourceWithStreamingResponse:
        from .resources.resource_groups import AsyncResourceGroupsResourceWithStreamingResponse

        return AsyncResourceGroupsResourceWithStreamingResponse(self._client.resource_groups)

    @cached_property
    def scheduled_event_configurations(
        self,
    ) -> scheduled_event_configurations.AsyncScheduledEventConfigurationsResourceWithStreamingResponse:
        from .resources.scheduled_event_configurations import (
            AsyncScheduledEventConfigurationsResourceWithStreamingResponse,
        )

        return AsyncScheduledEventConfigurationsResourceWithStreamingResponse(
            self._client.scheduled_event_configurations
        )

    @cached_property
    def statements(self) -> statements.AsyncStatementsResourceWithStreamingResponse:
        from .resources.statements import AsyncStatementsResourceWithStreamingResponse

        return AsyncStatementsResourceWithStreamingResponse(self._client.statements)

    @cached_property
    def transaction_types(self) -> transaction_types.AsyncTransactionTypesResourceWithStreamingResponse:
        from .resources.transaction_types import AsyncTransactionTypesResourceWithStreamingResponse

        return AsyncTransactionTypesResourceWithStreamingResponse(self._client.transaction_types)

    @cached_property
    def usage(self) -> usage.AsyncUsageResourceWithStreamingResponse:
        from .resources.usage import AsyncUsageResourceWithStreamingResponse

        return AsyncUsageResourceWithStreamingResponse(self._client.usage)

    @cached_property
    def users(self) -> users.AsyncUsersResourceWithStreamingResponse:
        from .resources.users import AsyncUsersResourceWithStreamingResponse

        return AsyncUsersResourceWithStreamingResponse(self._client.users)

    @cached_property
    def webhooks(self) -> webhooks.AsyncWebhooksResourceWithStreamingResponse:
        from .resources.webhooks import AsyncWebhooksResourceWithStreamingResponse

        return AsyncWebhooksResourceWithStreamingResponse(self._client.webhooks)


Client = M3ter

AsyncClient = AsyncM3ter
