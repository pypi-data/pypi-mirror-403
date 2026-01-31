# Users

Types:

```python
from aibanking.types import UserRegisterResponse
```

Methods:

- <code title="post /users/login">client.users.<a href="./src/aibanking/resources/users/users.py">login</a>() -> object</code>
- <code title="post /users/register">client.users.<a href="./src/aibanking/resources/users/users.py">register</a>(\*\*<a href="src/aibanking/types/user_register_params.py">params</a>) -> <a href="./src/aibanking/types/user_register_response.py">UserRegisterResponse</a></code>

## PasswordReset

Methods:

- <code title="post /users/password-reset/confirm">client.users.password_reset.<a href="./src/aibanking/resources/users/password_reset.py">confirm</a>() -> object</code>
- <code title="post /users/password-reset/initiate">client.users.password_reset.<a href="./src/aibanking/resources/users/password_reset.py">initiate</a>() -> object</code>

## Me

Types:

```python
from aibanking.types.users import MeRetrieveResponse, MeUpdateResponse
```

Methods:

- <code title="get /users/me">client.users.me.<a href="./src/aibanking/resources/users/me/me.py">retrieve</a>() -> <a href="./src/aibanking/types/users/me_retrieve_response.py">MeRetrieveResponse</a></code>
- <code title="put /users/me">client.users.me.<a href="./src/aibanking/resources/users/me/me.py">update</a>(\*\*<a href="src/aibanking/types/users/me_update_params.py">params</a>) -> <a href="./src/aibanking/types/users/me_update_response.py">MeUpdateResponse</a></code>

### Preferences

Types:

```python
from aibanking.types.users.me import PreferenceRetrieveResponse, PreferenceUpdateResponse
```

Methods:

- <code title="get /users/me/preferences">client.users.me.preferences.<a href="./src/aibanking/resources/users/me/preferences.py">retrieve</a>() -> <a href="./src/aibanking/types/users/me/preference_retrieve_response.py">PreferenceRetrieveResponse</a></code>
- <code title="put /users/me/preferences">client.users.me.preferences.<a href="./src/aibanking/resources/users/me/preferences.py">update</a>(\*\*<a href="src/aibanking/types/users/me/preference_update_params.py">params</a>) -> <a href="./src/aibanking/types/users/me/preference_update_response.py">PreferenceUpdateResponse</a></code>

### Devices

Methods:

- <code title="get /users/me/devices">client.users.me.devices.<a href="./src/aibanking/resources/users/me/devices.py">list</a>(\*\*<a href="src/aibanking/types/users/me/device_list_params.py">params</a>) -> object</code>

### Biometrics

Methods:

- <code title="get /users/me/biometrics">client.users.me.biometrics.<a href="./src/aibanking/resources/users/me/biometrics.py">retrieve_status</a>() -> object</code>
- <code title="post /users/me/biometrics/verify">client.users.me.biometrics.<a href="./src/aibanking/resources/users/me/biometrics.py">verify</a>() -> object</code>

# Accounts

Types:

```python
from aibanking.types import AccountRetrieveDetailsResponse
```

Methods:

- <code title="post /accounts/link">client.accounts.<a href="./src/aibanking/resources/accounts/accounts.py">link</a>() -> object</code>
- <code title="get /accounts/{accountId}/details">client.accounts.<a href="./src/aibanking/resources/accounts/accounts.py">retrieve_details</a>(account_id) -> <a href="./src/aibanking/types/account_retrieve_details_response.py">AccountRetrieveDetailsResponse</a></code>
- <code title="get /accounts/me">client.accounts.<a href="./src/aibanking/resources/accounts/accounts.py">retrieve_me</a>(\*\*<a href="src/aibanking/types/account_retrieve_me_params.py">params</a>) -> object</code>

## Transactions

Methods:

- <code title="get /accounts/{accountId}/transactions/pending">client.accounts.transactions.<a href="./src/aibanking/resources/accounts/transactions.py">retrieve_pending</a>(account_id, \*\*<a href="src/aibanking/types/accounts/transaction_retrieve_pending_params.py">params</a>) -> object</code>

## Statements

Types:

```python
from aibanking.types.accounts import StatementListResponse
```

Methods:

- <code title="get /accounts/{accountId}/statements">client.accounts.statements.<a href="./src/aibanking/resources/accounts/statements.py">list</a>(account_id, \*\*<a href="src/aibanking/types/accounts/statement_list_params.py">params</a>) -> <a href="./src/aibanking/types/accounts/statement_list_response.py">StatementListResponse</a></code>

## OverdraftSettings

Methods:

- <code title="get /accounts/{accountId}/overdraft-settings">client.accounts.overdraft_settings.<a href="./src/aibanking/resources/accounts/overdraft_settings.py">retrieve_overdraft_settings</a>(account_id) -> object</code>
- <code title="put /accounts/{accountId}/overdraft-settings">client.accounts.overdraft_settings.<a href="./src/aibanking/resources/accounts/overdraft_settings.py">update_overdraft_settings</a>(account_id) -> object</code>

# Transactions

Types:

```python
from aibanking.types import (
    TransactionRetrieveResponse,
    TransactionAddNotesResponse,
    TransactionCategorizeResponse,
)
```

Methods:

- <code title="get /transactions/{transactionId}">client.transactions.<a href="./src/aibanking/resources/transactions/transactions.py">retrieve</a>(transaction_id) -> <a href="./src/aibanking/types/transaction_retrieve_response.py">TransactionRetrieveResponse</a></code>
- <code title="get /transactions">client.transactions.<a href="./src/aibanking/resources/transactions/transactions.py">list</a>(\*\*<a href="src/aibanking/types/transaction_list_params.py">params</a>) -> object</code>
- <code title="put /transactions/{transactionId}/notes">client.transactions.<a href="./src/aibanking/resources/transactions/transactions.py">add_notes</a>(transaction_id) -> <a href="./src/aibanking/types/transaction_add_notes_response.py">TransactionAddNotesResponse</a></code>
- <code title="put /transactions/{transactionId}/categorize">client.transactions.<a href="./src/aibanking/resources/transactions/transactions.py">categorize</a>(transaction_id) -> <a href="./src/aibanking/types/transaction_categorize_response.py">TransactionCategorizeResponse</a></code>

## Recurring

Methods:

- <code title="get /transactions/recurring">client.transactions.recurring.<a href="./src/aibanking/resources/transactions/recurring.py">list</a>(\*\*<a href="src/aibanking/types/transactions/recurring_list_params.py">params</a>) -> object</code>

## Insights

Methods:

- <code title="get /transactions/insights/spending-trends">client.transactions.insights.<a href="./src/aibanking/resources/transactions/insights.py">get_spending_trends</a>() -> object</code>

# AI

## Oracle

### Simulate

Types:

```python
from aibanking.types.ai.oracle import SimulateCreateResponse
```

Methods:

- <code title="post /ai/oracle/simulate">client.ai.oracle.simulate.<a href="./src/aibanking/resources/ai/oracle/simulate.py">create</a>() -> <a href="./src/aibanking/types/ai/oracle/simulate_create_response.py">SimulateCreateResponse</a></code>
- <code title="post /ai/oracle/simulate/advanced">client.ai.oracle.simulate.<a href="./src/aibanking/resources/ai/oracle/simulate.py">advanced</a>(\*\*<a href="src/aibanking/types/ai/oracle/simulate_advanced_params.py">params</a>) -> object</code>

### Simulations

Types:

```python
from aibanking.types.ai.oracle import SimulationRetrieveResponse
```

Methods:

- <code title="get /ai/oracle/simulations/{simulationId}">client.ai.oracle.simulations.<a href="./src/aibanking/resources/ai/oracle/simulations.py">retrieve</a>(simulation_id) -> <a href="./src/aibanking/types/ai/oracle/simulation_retrieve_response.py">SimulationRetrieveResponse</a></code>
- <code title="get /ai/oracle/simulations">client.ai.oracle.simulations.<a href="./src/aibanking/resources/ai/oracle/simulations.py">list</a>(\*\*<a href="src/aibanking/types/ai/oracle/simulation_list_params.py">params</a>) -> object</code>

## Incubator

Methods:

- <code title="get /ai/incubator/pitches">client.ai.incubator.<a href="./src/aibanking/resources/ai/incubator/incubator.py">retrieve_pitches</a>(\*\*<a href="src/aibanking/types/ai/incubator_retrieve_pitches_params.py">params</a>) -> object</code>

### Pitch

Types:

```python
from aibanking.types.ai.incubator import PitchRetrieveDetailsResponse
```

Methods:

- <code title="post /ai/incubator/pitch">client.ai.incubator.pitch.<a href="./src/aibanking/resources/ai/incubator/pitch.py">create</a>(\*\*<a href="src/aibanking/types/ai/incubator/pitch_create_params.py">params</a>) -> object</code>
- <code title="get /ai/incubator/pitch/{pitchId}/details">client.ai.incubator.pitch.<a href="./src/aibanking/resources/ai/incubator/pitch.py">retrieve_details</a>(pitch_id) -> <a href="./src/aibanking/types/ai/incubator/pitch_retrieve_details_response.py">PitchRetrieveDetailsResponse</a></code>
- <code title="put /ai/incubator/pitch/{pitchId}/feedback">client.ai.incubator.pitch.<a href="./src/aibanking/resources/ai/incubator/pitch.py">update_feedback</a>(pitch_id) -> object</code>

## Ads

Methods:

- <code title="get /ai/ads/operations/{operationId}">client.ai.ads.<a href="./src/aibanking/resources/ai/ads/ads.py">retrieve</a>(operation_id) -> object</code>
- <code title="get /ai/ads">client.ai.ads.<a href="./src/aibanking/resources/ai/ads/ads.py">list</a>(\*\*<a href="src/aibanking/types/ai/ad_list_params.py">params</a>) -> object</code>

## Advisor

### Chat

Methods:

- <code title="post /ai/advisor/chat">client.ai.advisor.chat.<a href="./src/aibanking/resources/ai/advisor/chat.py">create</a>(\*\*<a href="src/aibanking/types/ai/advisor/chat_create_params.py">params</a>) -> object</code>
- <code title="get /ai/advisor/chat/history">client.ai.advisor.chat.<a href="./src/aibanking/resources/ai/advisor/chat.py">retrieve_history</a>(\*\*<a href="src/aibanking/types/ai/advisor/chat_retrieve_history_params.py">params</a>) -> object</code>

### Tools

Methods:

- <code title="get /ai/advisor/tools">client.ai.advisor.tools.<a href="./src/aibanking/resources/ai/advisor/tools.py">list</a>(\*\*<a href="src/aibanking/types/ai/advisor/tool_list_params.py">params</a>) -> object</code>

# Corporate

## Compliance

### Audits

Types:

```python
from aibanking.types.corporate.compliance import AuditRetrieveReportResponse
```

Methods:

- <code title="post /corporate/compliance/audits">client.corporate.compliance.audits.<a href="./src/aibanking/resources/corporate/compliance/audits.py">request_audit</a>() -> object</code>
- <code title="get /corporate/compliance/audits/{auditId}/report">client.corporate.compliance.audits.<a href="./src/aibanking/resources/corporate/compliance/audits.py">retrieve_report</a>(audit_id) -> <a href="./src/aibanking/types/corporate/compliance/audit_retrieve_report_response.py">AuditRetrieveReportResponse</a></code>

## Treasury

Types:

```python
from aibanking.types.corporate import TreasuryGetLiquidityPositionsResponse
```

Methods:

- <code title="get /corporate/treasury/liquidity-positions">client.corporate.treasury.<a href="./src/aibanking/resources/corporate/treasury/treasury.py">get_liquidity_positions</a>() -> <a href="./src/aibanking/types/corporate/treasury_get_liquidity_positions_response.py">TreasuryGetLiquidityPositionsResponse</a></code>

### CashFlow

Types:

```python
from aibanking.types.corporate.treasury import CashFlowForecastResponse
```

Methods:

- <code title="get /corporate/treasury/cash-flow/forecast">client.corporate.treasury.cash_flow.<a href="./src/aibanking/resources/corporate/treasury/cash_flow.py">forecast</a>(\*\*<a href="src/aibanking/types/corporate/treasury/cash_flow_forecast_params.py">params</a>) -> <a href="./src/aibanking/types/corporate/treasury/cash_flow_forecast_response.py">CashFlowForecastResponse</a></code>

## Cards

Types:

```python
from aibanking.types.corporate import (
    CardIssueVirtualCardResponse,
    CardToggleCardLockResponse,
    CardUpdateControlsResponse,
)
```

Methods:

- <code title="get /corporate/cards/{cardId}/transactions">client.corporate.cards.<a href="./src/aibanking/resources/corporate/cards.py">get_transactions</a>(card_id, \*\*<a href="src/aibanking/types/corporate/card_get_transactions_params.py">params</a>) -> object</code>
- <code title="post /corporate/cards/virtual">client.corporate.cards.<a href="./src/aibanking/resources/corporate/cards.py">issue_virtual_card</a>(\*\*<a href="src/aibanking/types/corporate/card_issue_virtual_card_params.py">params</a>) -> <a href="./src/aibanking/types/corporate/card_issue_virtual_card_response.py">CardIssueVirtualCardResponse</a></code>
- <code title="get /corporate/cards">client.corporate.cards.<a href="./src/aibanking/resources/corporate/cards.py">list_all</a>(\*\*<a href="src/aibanking/types/corporate/card_list_all_params.py">params</a>) -> object</code>
- <code title="post /corporate/cards/{cardId}/freeze">client.corporate.cards.<a href="./src/aibanking/resources/corporate/cards.py">toggle_card_lock</a>(card_id) -> <a href="./src/aibanking/types/corporate/card_toggle_card_lock_response.py">CardToggleCardLockResponse</a></code>
- <code title="put /corporate/cards/{cardId}/controls">client.corporate.cards.<a href="./src/aibanking/resources/corporate/cards.py">update_controls</a>(card_id) -> <a href="./src/aibanking/types/corporate/card_update_controls_response.py">CardUpdateControlsResponse</a></code>

## Risk

### Fraud

#### Rules

Types:

```python
from aibanking.types.corporate.risk.fraud import RuleUpdateRuleResponse
```

Methods:

- <code title="get /corporate/risk/fraud/rules">client.corporate.risk.fraud.rules.<a href="./src/aibanking/resources/corporate/risk/fraud/rules.py">list_active</a>(\*\*<a href="src/aibanking/types/corporate/risk/fraud/rule_list_active_params.py">params</a>) -> object</code>
- <code title="put /corporate/risk/fraud/rules/{ruleId}">client.corporate.risk.fraud.rules.<a href="./src/aibanking/resources/corporate/risk/fraud/rules.py">update_rule</a>(rule_id, \*\*<a href="src/aibanking/types/corporate/risk/fraud/rule_update_rule_params.py">params</a>) -> <a href="./src/aibanking/types/corporate/risk/fraud/rule_update_rule_response.py">RuleUpdateRuleResponse</a></code>

## Anomalies

Methods:

- <code title="get /corporate/anomalies">client.corporate.anomalies.<a href="./src/aibanking/resources/corporate/anomalies.py">list_detected</a>(\*\*<a href="src/aibanking/types/corporate/anomaly_list_detected_params.py">params</a>) -> object</code>
- <code title="put /corporate/anomalies/{anomalyId}/status">client.corporate.anomalies.<a href="./src/aibanking/resources/corporate/anomalies.py">update_status</a>(anomaly_id) -> object</code>

# Web3

## Wallets

Methods:

- <code title="post /web3/wallets">client.web3.wallets.<a href="./src/aibanking/resources/web3/wallets.py">create</a>() -> object</code>
- <code title="get /web3/wallets">client.web3.wallets.<a href="./src/aibanking/resources/web3/wallets.py">list</a>(\*\*<a href="src/aibanking/types/web3/wallet_list_params.py">params</a>) -> object</code>
- <code title="get /web3/wallets/{walletId}/balances">client.web3.wallets.<a href="./src/aibanking/resources/web3/wallets.py">get_balances</a>(wallet_id, \*\*<a href="src/aibanking/types/web3/wallet_get_balances_params.py">params</a>) -> object</code>

## Transactions

Methods:

- <code title="post /web3/transactions/initiate">client.web3.transactions.<a href="./src/aibanking/resources/web3/transactions.py">initiate</a>() -> object</code>

## NFTs

Methods:

- <code title="get /web3/nfts">client.web3.nfts.<a href="./src/aibanking/resources/web3/nfts.py">list</a>(\*\*<a href="src/aibanking/types/web3/nft_list_params.py">params</a>) -> object</code>

# Payments

## International

Methods:

- <code title="get /payments/international/{paymentId}/status">client.payments.international.<a href="./src/aibanking/resources/payments/international.py">get_status</a>(payment_id) -> object</code>

## Fx

Types:

```python
from aibanking.types.payments import FxGetRatesResponse
```

Methods:

- <code title="post /payments/fx/convert">client.payments.fx.<a href="./src/aibanking/resources/payments/fx.py">execute_conversion</a>() -> object</code>
- <code title="get /payments/fx/rates">client.payments.fx.<a href="./src/aibanking/resources/payments/fx.py">get_rates</a>(\*\*<a href="src/aibanking/types/payments/fx_get_rates_params.py">params</a>) -> <a href="./src/aibanking/types/payments/fx_get_rates_response.py">FxGetRatesResponse</a></code>

# Sustainability

Methods:

- <code title="get /sustainability/carbon-footprint">client.sustainability.<a href="./src/aibanking/resources/sustainability/sustainability.py">retrieve_carbon_footprint</a>() -> object</code>

# Marketplace

Methods:

- <code title="get /marketplace/products">client.marketplace.<a href="./src/aibanking/resources/marketplace/marketplace.py">list_products</a>(\*\*<a href="src/aibanking/types/marketplace_list_products_params.py">params</a>) -> object</code>

## Offers

Methods:

- <code title="post /marketplace/offers/{offerId}/redeem">client.marketplace.offers.<a href="./src/aibanking/resources/marketplace/offers.py">redeem_offer</a>(offer_id) -> object</code>

# Investments

## Portfolios

Methods:

- <code title="get /investments/portfolios/{portfolioId}">client.investments.portfolios.<a href="./src/aibanking/resources/investments/portfolios.py">retrieve</a>(portfolio_id) -> object</code>
- <code title="put /investments/portfolios/{portfolioId}">client.investments.portfolios.<a href="./src/aibanking/resources/investments/portfolios.py">update</a>(portfolio_id) -> object</code>
- <code title="get /investments/portfolios">client.investments.portfolios.<a href="./src/aibanking/resources/investments/portfolios.py">list</a>(\*\*<a href="src/aibanking/types/investments/portfolio_list_params.py">params</a>) -> object</code>
- <code title="post /investments/portfolios/{portfolioId}/rebalance">client.investments.portfolios.<a href="./src/aibanking/resources/investments/portfolios.py">rebalance</a>(portfolio_id) -> object</code>

## Assets

Methods:

- <code title="get /investments/assets/search">client.investments.assets.<a href="./src/aibanking/resources/investments/assets.py">search</a>(\*\*<a href="src/aibanking/types/investments/asset_search_params.py">params</a>) -> object</code>
