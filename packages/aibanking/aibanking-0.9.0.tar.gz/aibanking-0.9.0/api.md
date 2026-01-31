# Users

Types:

```python
from aibanking.types import UserLoginResponse, UserRegisterResponse
```

Methods:

- <code title="post /users/login">client.users.<a href="./src/aibanking/resources/users/users.py">login</a>(\*\*<a href="src/aibanking/types/user_login_params.py">params</a>) -> <a href="./src/aibanking/types/user_login_response.py">UserLoginResponse</a></code>
- <code title="post /users/logout">client.users.<a href="./src/aibanking/resources/users/users.py">logout</a>() -> None</code>
- <code title="post /users/register">client.users.<a href="./src/aibanking/resources/users/users.py">register</a>(\*\*<a href="src/aibanking/types/user_register_params.py">params</a>) -> <a href="./src/aibanking/types/user_register_response.py">UserRegisterResponse</a></code>

## PasswordReset

Types:

```python
from aibanking.types.users import PasswordResetConfirmResponse, PasswordResetInitiateResponse
```

Methods:

- <code title="post /users/password-reset/confirm">client.users.password_reset.<a href="./src/aibanking/resources/users/password_reset.py">confirm</a>(\*\*<a href="src/aibanking/types/users/password_reset_confirm_params.py">params</a>) -> <a href="./src/aibanking/types/users/password_reset_confirm_response.py">PasswordResetConfirmResponse</a></code>
- <code title="post /users/password-reset/initiate">client.users.password_reset.<a href="./src/aibanking/resources/users/password_reset.py">initiate</a>(\*\*<a href="src/aibanking/types/users/password_reset_initiate_params.py">params</a>) -> <a href="./src/aibanking/types/users/password_reset_initiate_response.py">PasswordResetInitiateResponse</a></code>

## Me

Types:

```python
from aibanking.types.users import MeRetrieveResponse
```

Methods:

- <code title="get /users/me">client.users.me.<a href="./src/aibanking/resources/users/me/me.py">retrieve</a>() -> <a href="./src/aibanking/types/users/me_retrieve_response.py">MeRetrieveResponse</a></code>
- <code title="put /users/me">client.users.me.<a href="./src/aibanking/resources/users/me/me.py">update</a>() -> None</code>
- <code title="delete /users/me">client.users.me.<a href="./src/aibanking/resources/users/me/me.py">delete</a>() -> None</code>

### Preferences

Types:

```python
from aibanking.types.users.me import PreferenceRetrieveResponse, PreferenceUpdateResponse
```

Methods:

- <code title="get /users/me/preferences">client.users.me.preferences.<a href="./src/aibanking/resources/users/me/preferences.py">retrieve</a>() -> <a href="./src/aibanking/types/users/me/preference_retrieve_response.py">PreferenceRetrieveResponse</a></code>
- <code title="put /users/me/preferences">client.users.me.preferences.<a href="./src/aibanking/resources/users/me/preferences.py">update</a>(\*\*<a href="src/aibanking/types/users/me/preference_update_params.py">params</a>) -> <a href="./src/aibanking/types/users/me/preference_update_response.py">PreferenceUpdateResponse</a></code>

### Security

Types:

```python
from aibanking.types.users.me import SecurityRetrieveLogResponse, SecurityRotateKeysResponse
```

Methods:

- <code title="get /users/me/security/log">client.users.me.security.<a href="./src/aibanking/resources/users/me/security.py">retrieve_log</a>(\*\*<a href="src/aibanking/types/users/me/security_retrieve_log_params.py">params</a>) -> <a href="./src/aibanking/types/users/me/security_retrieve_log_response.py">SecurityRetrieveLogResponse</a></code>
- <code title="post /users/me/security/rotate-keys">client.users.me.security.<a href="./src/aibanking/resources/users/me/security.py">rotate_keys</a>() -> <a href="./src/aibanking/types/users/me/security_rotate_keys_response.py">SecurityRotateKeysResponse</a></code>

### Devices

Types:

```python
from aibanking.types.users.me import DeviceListResponse
```

Methods:

- <code title="get /users/me/devices">client.users.me.devices.<a href="./src/aibanking/resources/users/me/devices.py">list</a>() -> <a href="./src/aibanking/types/users/me/device_list_response.py">DeviceListResponse</a></code>
- <code title="delete /users/me/devices/{deviceId}">client.users.me.devices.<a href="./src/aibanking/resources/users/me/devices.py">deregister</a>(device_id) -> None</code>
- <code title="post /users/me/devices">client.users.me.devices.<a href="./src/aibanking/resources/users/me/devices.py">register</a>(\*\*<a href="src/aibanking/types/users/me/device_register_params.py">params</a>) -> None</code>

### Biometrics

Types:

```python
from aibanking.types.users.me import BiometricRetrieveStatusResponse, BiometricVerifyResponse
```

Methods:

- <code title="post /users/me/biometrics/enroll">client.users.me.biometrics.<a href="./src/aibanking/resources/users/me/biometrics.py">enroll</a>(\*\*<a href="src/aibanking/types/users/me/biometric_enroll_params.py">params</a>) -> None</code>
- <code title="delete /users/me/biometrics">client.users.me.biometrics.<a href="./src/aibanking/resources/users/me/biometrics.py">remove_all</a>() -> None</code>
- <code title="get /users/me/biometrics">client.users.me.biometrics.<a href="./src/aibanking/resources/users/me/biometrics.py">retrieve_status</a>() -> <a href="./src/aibanking/types/users/me/biometric_retrieve_status_response.py">BiometricRetrieveStatusResponse</a></code>
- <code title="post /users/me/biometrics/verify">client.users.me.biometrics.<a href="./src/aibanking/resources/users/me/biometrics.py">verify</a>(\*\*<a href="src/aibanking/types/users/me/biometric_verify_params.py">params</a>) -> <a href="./src/aibanking/types/users/me/biometric_verify_response.py">BiometricVerifyResponse</a></code>

# Accounts

Types:

```python
from aibanking.types import (
    AccountLinkResponse,
    AccountOpenResponse,
    AccountRetrieveBalanceHistoryResponse,
    AccountRetrieveDetailsResponse,
    AccountRetrieveMeResponse,
)
```

Methods:

- <code title="delete /accounts/{accountId}">client.accounts.<a href="./src/aibanking/resources/accounts/accounts.py">delete</a>(account_id) -> None</code>
- <code title="post /accounts/link">client.accounts.<a href="./src/aibanking/resources/accounts/accounts.py">link</a>(\*\*<a href="src/aibanking/types/account_link_params.py">params</a>) -> <a href="./src/aibanking/types/account_link_response.py">AccountLinkResponse</a></code>
- <code title="post /accounts/open">client.accounts.<a href="./src/aibanking/resources/accounts/accounts.py">open</a>(\*\*<a href="src/aibanking/types/account_open_params.py">params</a>) -> <a href="./src/aibanking/types/account_open_response.py">AccountOpenResponse</a></code>
- <code title="get /accounts/{accountId}/balance-history">client.accounts.<a href="./src/aibanking/resources/accounts/accounts.py">retrieve_balance_history</a>(account_id, \*\*<a href="src/aibanking/types/account_retrieve_balance_history_params.py">params</a>) -> <a href="./src/aibanking/types/account_retrieve_balance_history_response.py">AccountRetrieveBalanceHistoryResponse</a></code>
- <code title="get /accounts/{accountId}/details">client.accounts.<a href="./src/aibanking/resources/accounts/accounts.py">retrieve_details</a>(account_id) -> <a href="./src/aibanking/types/account_retrieve_details_response.py">AccountRetrieveDetailsResponse</a></code>
- <code title="get /accounts/me">client.accounts.<a href="./src/aibanking/resources/accounts/accounts.py">retrieve_me</a>() -> <a href="./src/aibanking/types/account_retrieve_me_response.py">AccountRetrieveMeResponse</a></code>

## Transactions

Types:

```python
from aibanking.types.accounts import (
    TransactionRetrieveArchivedResponse,
    TransactionRetrievePendingResponse,
)
```

Methods:

- <code title="get /accounts/{accountId}/transactions/archived">client.accounts.transactions.<a href="./src/aibanking/resources/accounts/transactions.py">retrieve_archived</a>(account_id, \*\*<a href="src/aibanking/types/accounts/transaction_retrieve_archived_params.py">params</a>) -> <a href="./src/aibanking/types/accounts/transaction_retrieve_archived_response.py">TransactionRetrieveArchivedResponse</a></code>
- <code title="get /accounts/{accountId}/transactions/pending">client.accounts.transactions.<a href="./src/aibanking/resources/accounts/transactions.py">retrieve_pending</a>(account_id) -> <a href="./src/aibanking/types/accounts/transaction_retrieve_pending_response.py">TransactionRetrievePendingResponse</a></code>

## Statements

Types:

```python
from aibanking.types.accounts import StatementListResponse
```

Methods:

- <code title="get /accounts/{accountId}/statements">client.accounts.statements.<a href="./src/aibanking/resources/accounts/statements.py">list</a>(account_id) -> <a href="./src/aibanking/types/accounts/statement_list_response.py">StatementListResponse</a></code>
- <code title="get /accounts/{accountId}/statements/{statementId}/pdf">client.accounts.statements.<a href="./src/aibanking/resources/accounts/statements.py">retrieve_pdf</a>(statement_id, \*, account_id) -> None</code>

## OverdraftSettings

Types:

```python
from aibanking.types.accounts import OverdraftSettingRetrieveOverdraftSettingsResponse
```

Methods:

- <code title="get /accounts/{accountId}/overdraft-settings">client.accounts.overdraft_settings.<a href="./src/aibanking/resources/accounts/overdraft_settings.py">retrieve_overdraft_settings</a>(account_id) -> <a href="./src/aibanking/types/accounts/overdraft_setting_retrieve_overdraft_settings_response.py">OverdraftSettingRetrieveOverdraftSettingsResponse</a></code>
- <code title="put /accounts/{accountId}/overdraft-settings">client.accounts.overdraft_settings.<a href="./src/aibanking/resources/accounts/overdraft_settings.py">update_overdraft_settings</a>(account_id, \*\*<a href="src/aibanking/types/accounts/overdraft_setting_update_overdraft_settings_params.py">params</a>) -> None</code>

# Transactions

Types:

```python
from aibanking.types import (
    TransactionRetrieveResponse,
    TransactionListResponse,
    TransactionCategorizeResponse,
)
```

Methods:

- <code title="get /transactions/{transactionId}">client.transactions.<a href="./src/aibanking/resources/transactions/transactions.py">retrieve</a>(transaction_id) -> <a href="./src/aibanking/types/transaction_retrieve_response.py">TransactionRetrieveResponse</a></code>
- <code title="get /transactions">client.transactions.<a href="./src/aibanking/resources/transactions/transactions.py">list</a>(\*\*<a href="src/aibanking/types/transaction_list_params.py">params</a>) -> <a href="./src/aibanking/types/transaction_list_response.py">TransactionListResponse</a></code>
- <code title="put /transactions/{transactionId}/notes">client.transactions.<a href="./src/aibanking/resources/transactions/transactions.py">add_notes</a>(transaction_id, \*\*<a href="src/aibanking/types/transaction_add_notes_params.py">params</a>) -> None</code>
- <code title="put /transactions/{transactionId}/categorize">client.transactions.<a href="./src/aibanking/resources/transactions/transactions.py">categorize</a>(transaction_id, \*\*<a href="src/aibanking/types/transaction_categorize_params.py">params</a>) -> <a href="./src/aibanking/types/transaction_categorize_response.py">TransactionCategorizeResponse</a></code>
- <code title="post /transactions/{transactionId}/dispute">client.transactions.<a href="./src/aibanking/resources/transactions/transactions.py">initiate_dispute</a>(transaction_id, \*\*<a href="src/aibanking/types/transaction_initiate_dispute_params.py">params</a>) -> None</code>
- <code title="post /transactions/{transactionId}/split">client.transactions.<a href="./src/aibanking/resources/transactions/transactions.py">split</a>(transaction_id, \*\*<a href="src/aibanking/types/transaction_split_params.py">params</a>) -> None</code>

## Recurring

Types:

```python
from aibanking.types.transactions import RecurringListResponse
```

Methods:

- <code title="post /transactions/recurring">client.transactions.recurring.<a href="./src/aibanking/resources/transactions/recurring.py">create</a>(\*\*<a href="src/aibanking/types/transactions/recurring_create_params.py">params</a>) -> None</code>
- <code title="get /transactions/recurring">client.transactions.recurring.<a href="./src/aibanking/resources/transactions/recurring.py">list</a>() -> <a href="./src/aibanking/types/transactions/recurring_list_response.py">RecurringListResponse</a></code>
- <code title="delete /transactions/recurring/{recurringId}">client.transactions.recurring.<a href="./src/aibanking/resources/transactions/recurring.py">cancel</a>(recurring_id) -> None</code>

## Insights

Types:

```python
from aibanking.types.transactions import (
    InsightGetCashFlowPredictionResponse,
    InsightGetSpendingTrendsResponse,
)
```

Methods:

- <code title="get /transactions/insights/future-flow">client.transactions.insights.<a href="./src/aibanking/resources/transactions/insights.py">get_cash_flow_prediction</a>() -> <a href="./src/aibanking/types/transactions/insight_get_cash_flow_prediction_response.py">InsightGetCashFlowPredictionResponse</a></code>
- <code title="get /transactions/insights/spending-trends">client.transactions.insights.<a href="./src/aibanking/resources/transactions/insights.py">get_spending_trends</a>() -> <a href="./src/aibanking/types/transactions/insight_get_spending_trends_response.py">InsightGetSpendingTrendsResponse</a></code>

# AI

## Oracle

### Simulate

Types:

```python
from aibanking.types.ai.oracle import SimulateCreateResponse, SimulateAdvancedResponse
```

Methods:

- <code title="post /ai/oracle/simulate">client.ai.oracle.simulate.<a href="./src/aibanking/resources/ai/oracle/simulate.py">create</a>(\*\*<a href="src/aibanking/types/ai/oracle/simulate_create_params.py">params</a>) -> <a href="./src/aibanking/types/ai/oracle/simulate_create_response.py">SimulateCreateResponse</a></code>
- <code title="post /ai/oracle/simulate/advanced">client.ai.oracle.simulate.<a href="./src/aibanking/resources/ai/oracle/simulate.py">advanced</a>(\*\*<a href="src/aibanking/types/ai/oracle/simulate_advanced_params.py">params</a>) -> <a href="./src/aibanking/types/ai/oracle/simulate_advanced_response.py">SimulateAdvancedResponse</a></code>
- <code title="post /ai/oracle/simulate/monte-carlo">client.ai.oracle.simulate.<a href="./src/aibanking/resources/ai/oracle/simulate.py">monte_carlo</a>(\*\*<a href="src/aibanking/types/ai/oracle/simulate_monte_carlo_params.py">params</a>) -> None</code>

### Predictions

Types:

```python
from aibanking.types.ai.oracle import (
    PredictionRetrieveInflationResponse,
    PredictionRetrieveMarketCrashProbabilityResponse,
)
```

Methods:

- <code title="get /ai/oracle/predictions/inflation">client.ai.oracle.predictions.<a href="./src/aibanking/resources/ai/oracle/predictions.py">retrieve_inflation</a>(\*\*<a href="src/aibanking/types/ai/oracle/prediction_retrieve_inflation_params.py">params</a>) -> <a href="./src/aibanking/types/ai/oracle/prediction_retrieve_inflation_response.py">PredictionRetrieveInflationResponse</a></code>
- <code title="get /ai/oracle/predictions/market-crash-probability">client.ai.oracle.predictions.<a href="./src/aibanking/resources/ai/oracle/predictions.py">retrieve_market_crash_probability</a>() -> <a href="./src/aibanking/types/ai/oracle/prediction_retrieve_market_crash_probability_response.py">PredictionRetrieveMarketCrashProbabilityResponse</a></code>

### Simulations

Types:

```python
from aibanking.types.ai.oracle import SimulationRetrieveResponse, SimulationListResponse
```

Methods:

- <code title="get /ai/oracle/simulations/{simulationId}">client.ai.oracle.simulations.<a href="./src/aibanking/resources/ai/oracle/simulations.py">retrieve</a>(simulation_id) -> <a href="./src/aibanking/types/ai/oracle/simulation_retrieve_response.py">SimulationRetrieveResponse</a></code>
- <code title="get /ai/oracle/simulations">client.ai.oracle.simulations.<a href="./src/aibanking/resources/ai/oracle/simulations.py">list</a>() -> <a href="./src/aibanking/types/ai/oracle/simulation_list_response.py">SimulationListResponse</a></code>

## Incubator

Types:

```python
from aibanking.types.ai import IncubatorRetrievePitchesResponse, IncubatorValidateResponse
```

Methods:

- <code title="get /ai/incubator/pitches">client.ai.incubator.<a href="./src/aibanking/resources/ai/incubator/incubator.py">retrieve_pitches</a>() -> <a href="./src/aibanking/types/ai/incubator_retrieve_pitches_response.py">IncubatorRetrievePitchesResponse</a></code>
- <code title="post /ai/incubator/validate">client.ai.incubator.<a href="./src/aibanking/resources/ai/incubator/incubator.py">validate</a>(\*\*<a href="src/aibanking/types/ai/incubator_validate_params.py">params</a>) -> <a href="./src/aibanking/types/ai/incubator_validate_response.py">IncubatorValidateResponse</a></code>

### Pitch

Types:

```python
from aibanking.types.ai.incubator import PitchCreateResponse, PitchRetrieveDetailsResponse
```

Methods:

- <code title="post /ai/incubator/pitch">client.ai.incubator.pitch.<a href="./src/aibanking/resources/ai/incubator/pitch.py">create</a>(\*\*<a href="src/aibanking/types/ai/incubator/pitch_create_params.py">params</a>) -> <a href="./src/aibanking/types/ai/incubator/pitch_create_response.py">PitchCreateResponse</a></code>
- <code title="get /ai/incubator/pitch/{pitchId}/details">client.ai.incubator.pitch.<a href="./src/aibanking/resources/ai/incubator/pitch.py">retrieve_details</a>(pitch_id) -> <a href="./src/aibanking/types/ai/incubator/pitch_retrieve_details_response.py">PitchRetrieveDetailsResponse</a></code>
- <code title="put /ai/incubator/pitch/{pitchId}/feedback">client.ai.incubator.pitch.<a href="./src/aibanking/resources/ai/incubator/pitch.py">update_feedback</a>(pitch_id, \*\*<a href="src/aibanking/types/ai/incubator/pitch_update_feedback_params.py">params</a>) -> None</code>

### Analysis

Types:

```python
from aibanking.types.ai.incubator import AnalysisCompetitorsResponse, AnalysisSwotResponse
```

Methods:

- <code title="post /ai/incubator/analysis/competitors">client.ai.incubator.analysis.<a href="./src/aibanking/resources/ai/incubator/analysis.py">competitors</a>(\*\*<a href="src/aibanking/types/ai/incubator/analysis_competitors_params.py">params</a>) -> <a href="./src/aibanking/types/ai/incubator/analysis_competitors_response.py">AnalysisCompetitorsResponse</a></code>
- <code title="post /ai/incubator/analysis/swot">client.ai.incubator.analysis.<a href="./src/aibanking/resources/ai/incubator/analysis.py">swot</a>(\*\*<a href="src/aibanking/types/ai/incubator/analysis_swot_params.py">params</a>) -> <a href="./src/aibanking/types/ai/incubator/analysis_swot_response.py">AnalysisSwotResponse</a></code>

## Ads

Types:

```python
from aibanking.types.ai import AdRetrieveResponse, AdListResponse, AdOptimizeResponse
```

Methods:

- <code title="get /ai/ads/operations/{operationId}">client.ai.ads.<a href="./src/aibanking/resources/ai/ads/ads.py">retrieve</a>(operation_id) -> <a href="./src/aibanking/types/ai/ad_retrieve_response.py">AdRetrieveResponse</a></code>
- <code title="get /ai/ads">client.ai.ads.<a href="./src/aibanking/resources/ai/ads/ads.py">list</a>() -> <a href="./src/aibanking/types/ai/ad_list_response.py">AdListResponse</a></code>
- <code title="post /ai/ads/optimize">client.ai.ads.<a href="./src/aibanking/resources/ai/ads/ads.py">optimize</a>(\*\*<a href="src/aibanking/types/ai/ad_optimize_params.py">params</a>) -> <a href="./src/aibanking/types/ai/ad_optimize_response.py">AdOptimizeResponse</a></code>

### Generate

Types:

```python
from aibanking.types.ai.ads import GenerateCopyResponse, GenerateVideoResponse
```

Methods:

- <code title="post /ai/ads/generate/copy">client.ai.ads.generate.<a href="./src/aibanking/resources/ai/ads/generate.py">copy</a>(\*\*<a href="src/aibanking/types/ai/ads/generate_copy_params.py">params</a>) -> <a href="./src/aibanking/types/ai/ads/generate_copy_response.py">GenerateCopyResponse</a></code>
- <code title="post /ai/ads/generate/video">client.ai.ads.generate.<a href="./src/aibanking/resources/ai/ads/generate.py">video</a>(\*\*<a href="src/aibanking/types/ai/ads/generate_video_params.py">params</a>) -> <a href="./src/aibanking/types/ai/ads/generate_video_response.py">GenerateVideoResponse</a></code>

## Advisor

### Chat

Types:

```python
from aibanking.types.ai.advisor import ChatCreateResponse, ChatRetrieveHistoryResponse
```

Methods:

- <code title="post /ai/advisor/chat">client.ai.advisor.chat.<a href="./src/aibanking/resources/ai/advisor/chat.py">create</a>(\*\*<a href="src/aibanking/types/ai/advisor/chat_create_params.py">params</a>) -> <a href="./src/aibanking/types/ai/advisor/chat_create_response.py">ChatCreateResponse</a></code>
- <code title="get /ai/advisor/chat/history">client.ai.advisor.chat.<a href="./src/aibanking/resources/ai/advisor/chat.py">retrieve_history</a>() -> <a href="./src/aibanking/types/ai/advisor/chat_retrieve_history_response.py">ChatRetrieveHistoryResponse</a></code>

### Tools

Types:

```python
from aibanking.types.ai.advisor import ToolListResponse
```

Methods:

- <code title="get /ai/advisor/tools">client.ai.advisor.tools.<a href="./src/aibanking/resources/ai/advisor/tools.py">list</a>() -> <a href="./src/aibanking/types/ai/advisor/tool_list_response.py">ToolListResponse</a></code>
- <code title="post /ai/advisor/tools/{toolId}/enable">client.ai.advisor.tools.<a href="./src/aibanking/resources/ai/advisor/tools.py">enable</a>(tool_id) -> None</code>

## Agent

Types:

```python
from aibanking.types.ai import AgentRetrieveCapabilitiesResponse
```

Methods:

- <code title="get /ai/agent/capabilities">client.ai.agent.<a href="./src/aibanking/resources/ai/agent/agent.py">retrieve_capabilities</a>() -> <a href="./src/aibanking/types/ai/agent_retrieve_capabilities_response.py">AgentRetrieveCapabilitiesResponse</a></code>

### Prompts

Types:

```python
from aibanking.types.ai.agent import PromptListResponse
```

Methods:

- <code title="put /ai/agent/prompts">client.ai.agent.prompts.<a href="./src/aibanking/resources/ai/agent/prompts.py">create</a>(\*\*<a href="src/aibanking/types/ai/agent/prompt_create_params.py">params</a>) -> None</code>
- <code title="get /ai/agent/prompts">client.ai.agent.prompts.<a href="./src/aibanking/resources/ai/agent/prompts.py">list</a>() -> <a href="./src/aibanking/types/ai/agent/prompt_list_response.py">PromptListResponse</a></code>

## Models

Types:

```python
from aibanking.types.ai import ModelFineTuneResponse, ModelRetrieveVersionsResponse
```

Methods:

- <code title="post /ai/models/fine-tune">client.ai.models.<a href="./src/aibanking/resources/ai/models.py">fine_tune</a>(\*\*<a href="src/aibanking/types/ai/model_fine_tune_params.py">params</a>) -> <a href="./src/aibanking/types/ai/model_fine_tune_response.py">ModelFineTuneResponse</a></code>
- <code title="get /ai/models/versions">client.ai.models.<a href="./src/aibanking/resources/ai/models.py">retrieve_versions</a>() -> <a href="./src/aibanking/types/ai/model_retrieve_versions_response.py">ModelRetrieveVersionsResponse</a></code>

# Corporate

Types:

```python
from aibanking.types import CorporateOnboardResponse
```

Methods:

- <code title="post /corporate/onboard">client.corporate.<a href="./src/aibanking/resources/corporate/corporate.py">onboard</a>(\*\*<a href="src/aibanking/types/corporate_onboard_params.py">params</a>) -> <a href="./src/aibanking/types/corporate_onboard_response.py">CorporateOnboardResponse</a></code>

## Compliance

Types:

```python
from aibanking.types.corporate import (
    ComplianceScreenMediaResponse,
    ComplianceScreenPepResponse,
    ComplianceScreenSanctionsResponse,
)
```

Methods:

- <code title="post /corporate/compliance/media">client.corporate.compliance.<a href="./src/aibanking/resources/corporate/compliance/compliance.py">screen_media</a>(\*\*<a href="src/aibanking/types/corporate/compliance_screen_media_params.py">params</a>) -> <a href="./src/aibanking/types/corporate/compliance_screen_media_response.py">ComplianceScreenMediaResponse</a></code>
- <code title="post /corporate/compliance/pep">client.corporate.compliance.<a href="./src/aibanking/resources/corporate/compliance/compliance.py">screen_pep</a>(\*\*<a href="src/aibanking/types/corporate/compliance_screen_pep_params.py">params</a>) -> <a href="./src/aibanking/types/corporate/compliance_screen_pep_response.py">ComplianceScreenPepResponse</a></code>
- <code title="post /corporate/compliance/sanctions">client.corporate.compliance.<a href="./src/aibanking/resources/corporate/compliance/compliance.py">screen_sanctions</a>(\*\*<a href="src/aibanking/types/corporate/compliance_screen_sanctions_params.py">params</a>) -> <a href="./src/aibanking/types/corporate/compliance_screen_sanctions_response.py">ComplianceScreenSanctionsResponse</a></code>

### Audits

Types:

```python
from aibanking.types.corporate.compliance import (
    AuditRequestAuditResponse,
    AuditRetrieveReportResponse,
)
```

Methods:

- <code title="post /corporate/compliance/audits">client.corporate.compliance.audits.<a href="./src/aibanking/resources/corporate/compliance/audits.py">request_audit</a>(\*\*<a href="src/aibanking/types/corporate/compliance/audit_request_audit_params.py">params</a>) -> <a href="./src/aibanking/types/corporate/compliance/audit_request_audit_response.py">AuditRequestAuditResponse</a></code>
- <code title="get /corporate/compliance/audits/{auditId}/report">client.corporate.compliance.audits.<a href="./src/aibanking/resources/corporate/compliance/audits.py">retrieve_report</a>(audit_id) -> <a href="./src/aibanking/types/corporate/compliance/audit_retrieve_report_response.py">AuditRetrieveReportResponse</a></code>

## Treasury

Types:

```python
from aibanking.types.corporate import TreasuryGetLiquidityPositionsResponse
```

Methods:

- <code title="post /corporate/treasury/bulk-payouts">client.corporate.treasury.<a href="./src/aibanking/resources/corporate/treasury/treasury.py">execute_bulk_payouts</a>(\*\*<a href="src/aibanking/types/corporate/treasury_execute_bulk_payouts_params.py">params</a>) -> None</code>
- <code title="get /corporate/treasury/liquidity-positions">client.corporate.treasury.<a href="./src/aibanking/resources/corporate/treasury/treasury.py">get_liquidity_positions</a>() -> <a href="./src/aibanking/types/corporate/treasury_get_liquidity_positions_response.py">TreasuryGetLiquidityPositionsResponse</a></code>

### CashFlow

Types:

```python
from aibanking.types.corporate.treasury import CashFlowForecastResponse
```

Methods:

- <code title="get /corporate/treasury/cash-flow/forecast">client.corporate.treasury.cash_flow.<a href="./src/aibanking/resources/corporate/treasury/cash_flow.py">forecast</a>(\*\*<a href="src/aibanking/types/corporate/treasury/cash_flow_forecast_params.py">params</a>) -> <a href="./src/aibanking/types/corporate/treasury/cash_flow_forecast_response.py">CashFlowForecastResponse</a></code>

### Liquidity

Types:

```python
from aibanking.types.corporate.treasury import LiquidityOptimizeResponse
```

Methods:

- <code title="post /corporate/treasury/liquidity/pooling">client.corporate.treasury.liquidity.<a href="./src/aibanking/resources/corporate/treasury/liquidity.py">configure_pooling</a>(\*\*<a href="src/aibanking/types/corporate/treasury/liquidity_configure_pooling_params.py">params</a>) -> None</code>
- <code title="post /corporate/treasury/liquidity/optimize">client.corporate.treasury.liquidity.<a href="./src/aibanking/resources/corporate/treasury/liquidity.py">optimize</a>(\*\*<a href="src/aibanking/types/corporate/treasury/liquidity_optimize_params.py">params</a>) -> <a href="./src/aibanking/types/corporate/treasury/liquidity_optimize_response.py">LiquidityOptimizeResponse</a></code>

### Sweeping

Methods:

- <code title="post /corporate/treasury/sweeping/rules">client.corporate.treasury.sweeping.<a href="./src/aibanking/resources/corporate/treasury/sweeping.py">configure_rules</a>(\*\*<a href="src/aibanking/types/corporate/treasury/sweeping_configure_rules_params.py">params</a>) -> None</code>
- <code title="post /corporate/treasury/sweeping/execute">client.corporate.treasury.sweeping.<a href="./src/aibanking/resources/corporate/treasury/sweeping.py">execute_sweep</a>(\*\*<a href="src/aibanking/types/corporate/treasury/sweeping_execute_sweep_params.py">params</a>) -> None</code>

## Cards

Types:

```python
from aibanking.types.corporate import (
    CardGetTransactionsResponse,
    CardIssueVirtualCardResponse,
    CardListAllResponse,
    CardRequestPhysicalCardResponse,
)
```

Methods:

- <code title="get /corporate/cards/{cardId}/transactions">client.corporate.cards.<a href="./src/aibanking/resources/corporate/cards.py">get_transactions</a>(card_id) -> <a href="./src/aibanking/types/corporate/card_get_transactions_response.py">CardGetTransactionsResponse</a></code>
- <code title="post /corporate/cards/virtual">client.corporate.cards.<a href="./src/aibanking/resources/corporate/cards.py">issue_virtual_card</a>(\*\*<a href="src/aibanking/types/corporate/card_issue_virtual_card_params.py">params</a>) -> <a href="./src/aibanking/types/corporate/card_issue_virtual_card_response.py">CardIssueVirtualCardResponse</a></code>
- <code title="get /corporate/cards">client.corporate.cards.<a href="./src/aibanking/resources/corporate/cards.py">list_all</a>(\*\*<a href="src/aibanking/types/corporate/card_list_all_params.py">params</a>) -> <a href="./src/aibanking/types/corporate/card_list_all_response.py">CardListAllResponse</a></code>
- <code title="post /corporate/cards/physical">client.corporate.cards.<a href="./src/aibanking/resources/corporate/cards.py">request_physical_card</a>(\*\*<a href="src/aibanking/types/corporate/card_request_physical_card_params.py">params</a>) -> <a href="./src/aibanking/types/corporate/card_request_physical_card_response.py">CardRequestPhysicalCardResponse</a></code>
- <code title="post /corporate/cards/{cardId}/freeze">client.corporate.cards.<a href="./src/aibanking/resources/corporate/cards.py">toggle_card_lock</a>(card_id, \*\*<a href="src/aibanking/types/corporate/card_toggle_card_lock_params.py">params</a>) -> None</code>
- <code title="put /corporate/cards/{cardId}/controls">client.corporate.cards.<a href="./src/aibanking/resources/corporate/cards.py">update_controls</a>(card_id, \*\*<a href="src/aibanking/types/corporate/card_update_controls_params.py">params</a>) -> None</code>

## Risk

Types:

```python
from aibanking.types.corporate import RiskGetRiskExposureResponse, RiskRunStressTestResponse
```

Methods:

- <code title="get /corporate/risk/exposure">client.corporate.risk.<a href="./src/aibanking/resources/corporate/risk/risk.py">get_risk_exposure</a>() -> <a href="./src/aibanking/types/corporate/risk_get_risk_exposure_response.py">RiskGetRiskExposureResponse</a></code>
- <code title="post /corporate/risk/stress-test">client.corporate.risk.<a href="./src/aibanking/resources/corporate/risk/risk.py">run_stress_test</a>(\*\*<a href="src/aibanking/types/corporate/risk_run_stress_test_params.py">params</a>) -> <a href="./src/aibanking/types/corporate/risk_run_stress_test_response.py">RiskRunStressTestResponse</a></code>

### Fraud

Types:

```python
from aibanking.types.corporate.risk import FraudAnalyzeTransactionResponse
```

Methods:

- <code title="post /corporate/risk/fraud/analyze">client.corporate.risk.fraud.<a href="./src/aibanking/resources/corporate/risk/fraud/fraud.py">analyze_transaction</a>(\*\*<a href="src/aibanking/types/corporate/risk/fraud_analyze_transaction_params.py">params</a>) -> <a href="./src/aibanking/types/corporate/risk/fraud_analyze_transaction_response.py">FraudAnalyzeTransactionResponse</a></code>

#### Rules

Types:

```python
from aibanking.types.corporate.risk.fraud import RuleListActiveResponse
```

Methods:

- <code title="post /corporate/risk/fraud/rules">client.corporate.risk.fraud.rules.<a href="./src/aibanking/resources/corporate/risk/fraud/rules.py">create_custom</a>(\*\*<a href="src/aibanking/types/corporate/risk/fraud/rule_create_custom_params.py">params</a>) -> None</code>
- <code title="get /corporate/risk/fraud/rules">client.corporate.risk.fraud.rules.<a href="./src/aibanking/resources/corporate/risk/fraud/rules.py">list_active</a>() -> <a href="./src/aibanking/types/corporate/risk/fraud/rule_list_active_response.py">RuleListActiveResponse</a></code>
- <code title="put /corporate/risk/fraud/rules/{ruleId}">client.corporate.risk.fraud.rules.<a href="./src/aibanking/resources/corporate/risk/fraud/rules.py">update_rule</a>(rule_id, \*\*<a href="src/aibanking/types/corporate/risk/fraud/rule_update_rule_params.py">params</a>) -> None</code>

## Governance

### Proposals

Types:

```python
from aibanking.types.corporate.governance import ProposalListActiveResponse
```

Methods:

- <code title="post /corporate/governance/proposals/{proposalId}/vote">client.corporate.governance.proposals.<a href="./src/aibanking/resources/corporate/governance/proposals.py">cast_vote</a>(proposal_id, \*\*<a href="src/aibanking/types/corporate/governance/proposal_cast_vote_params.py">params</a>) -> None</code>
- <code title="post /corporate/governance/proposals">client.corporate.governance.proposals.<a href="./src/aibanking/resources/corporate/governance/proposals.py">create_new</a>(\*\*<a href="src/aibanking/types/corporate/governance/proposal_create_new_params.py">params</a>) -> None</code>
- <code title="get /corporate/governance/proposals">client.corporate.governance.proposals.<a href="./src/aibanking/resources/corporate/governance/proposals.py">list_active</a>() -> <a href="./src/aibanking/types/corporate/governance/proposal_list_active_response.py">ProposalListActiveResponse</a></code>

## Anomalies

Types:

```python
from aibanking.types.corporate import AnomalyListDetectedResponse
```

Methods:

- <code title="get /corporate/anomalies">client.corporate.anomalies.<a href="./src/aibanking/resources/corporate/anomalies.py">list_detected</a>() -> <a href="./src/aibanking/types/corporate/anomaly_list_detected_response.py">AnomalyListDetectedResponse</a></code>
- <code title="put /corporate/anomalies/{anomalyId}/status">client.corporate.anomalies.<a href="./src/aibanking/resources/corporate/anomalies.py">update_status</a>(anomaly_id, \*\*<a href="src/aibanking/types/corporate/anomaly_update_status_params.py">params</a>) -> None</code>

# Web3

## Network

Types:

```python
from aibanking.types.web3 import NetworkGetStatusResponse
```

Methods:

- <code title="get /web3/network/status">client.web3.network.<a href="./src/aibanking/resources/web3/network.py">get_status</a>() -> <a href="./src/aibanking/types/web3/network_get_status_response.py">NetworkGetStatusResponse</a></code>

## Wallets

Types:

```python
from aibanking.types.web3 import WalletCreateResponse, WalletListResponse, WalletGetBalancesResponse
```

Methods:

- <code title="post /web3/wallets">client.web3.wallets.<a href="./src/aibanking/resources/web3/wallets.py">create</a>(\*\*<a href="src/aibanking/types/web3/wallet_create_params.py">params</a>) -> <a href="./src/aibanking/types/web3/wallet_create_response.py">WalletCreateResponse</a></code>
- <code title="get /web3/wallets">client.web3.wallets.<a href="./src/aibanking/resources/web3/wallets.py">list</a>() -> <a href="./src/aibanking/types/web3/wallet_list_response.py">WalletListResponse</a></code>
- <code title="get /web3/wallets/{walletId}/balances">client.web3.wallets.<a href="./src/aibanking/resources/web3/wallets.py">get_balances</a>(wallet_id) -> <a href="./src/aibanking/types/web3/wallet_get_balances_response.py">WalletGetBalancesResponse</a></code>
- <code title="post /web3/wallets/connect">client.web3.wallets.<a href="./src/aibanking/resources/web3/wallets.py">link</a>(\*\*<a href="src/aibanking/types/web3/wallet_link_params.py">params</a>) -> None</code>

## Transactions

Types:

```python
from aibanking.types.web3 import TransactionSendResponse
```

Methods:

- <code title="post /web3/transactions/bridge">client.web3.transactions.<a href="./src/aibanking/resources/web3/transactions.py">bridge</a>(\*\*<a href="src/aibanking/types/web3/transaction_bridge_params.py">params</a>) -> None</code>
- <code title="post /web3/transactions/initiate">client.web3.transactions.<a href="./src/aibanking/resources/web3/transactions.py">initiate</a>(\*\*<a href="src/aibanking/types/web3/transaction_initiate_params.py">params</a>) -> None</code>
- <code title="post /web3/transactions/send">client.web3.transactions.<a href="./src/aibanking/resources/web3/transactions.py">send</a>(\*\*<a href="src/aibanking/types/web3/transaction_send_params.py">params</a>) -> <a href="./src/aibanking/types/web3/transaction_send_response.py">TransactionSendResponse</a></code>
- <code title="post /web3/transactions/swap">client.web3.transactions.<a href="./src/aibanking/resources/web3/transactions.py">swap</a>(\*\*<a href="src/aibanking/types/web3/transaction_swap_params.py">params</a>) -> None</code>

## NFTs

Types:

```python
from aibanking.types.web3 import NFTListResponse
```

Methods:

- <code title="get /web3/nfts">client.web3.nfts.<a href="./src/aibanking/resources/web3/nfts.py">list</a>() -> <a href="./src/aibanking/types/web3/nft_list_response.py">NFTListResponse</a></code>
- <code title="post /web3/nfts/mint">client.web3.nfts.<a href="./src/aibanking/resources/web3/nfts.py">mint</a>(\*\*<a href="src/aibanking/types/web3/nft_mint_params.py">params</a>) -> None</code>

## Contracts

Methods:

- <code title="post /web3/contracts/deploy">client.web3.contracts.<a href="./src/aibanking/resources/web3/contracts.py">deploy</a>(\*\*<a href="src/aibanking/types/web3/contract_deploy_params.py">params</a>) -> None</code>

# Payments

Types:

```python
from aibanking.types import PaymentListResponse
```

Methods:

- <code title="get /payments/{paymentId}">client.payments.<a href="./src/aibanking/resources/payments/payments.py">retrieve</a>(payment_id) -> None</code>
- <code title="get /payments">client.payments.<a href="./src/aibanking/resources/payments/payments.py">list</a>() -> <a href="./src/aibanking/types/payment_list_response.py">PaymentListResponse</a></code>

## Domestic

Methods:

- <code title="post /payments/domestic/ach">client.payments.domestic.<a href="./src/aibanking/resources/payments/domestic.py">execute_ach</a>(\*\*<a href="src/aibanking/types/payments/domestic_execute_ach_params.py">params</a>) -> None</code>
- <code title="post /payments/domestic/rtp">client.payments.domestic.<a href="./src/aibanking/resources/payments/domestic.py">execute_rtp</a>(\*\*<a href="src/aibanking/types/payments/domestic_execute_rtp_params.py">params</a>) -> None</code>
- <code title="post /payments/domestic/wire">client.payments.domestic.<a href="./src/aibanking/resources/payments/domestic.py">execute_wire</a>(\*\*<a href="src/aibanking/types/payments/domestic_execute_wire_params.py">params</a>) -> None</code>

## International

Types:

```python
from aibanking.types.payments import InternationalGetStatusResponse
```

Methods:

- <code title="post /payments/international/sepa">client.payments.international.<a href="./src/aibanking/resources/payments/international.py">execute_sepa</a>(\*\*<a href="src/aibanking/types/payments/international_execute_sepa_params.py">params</a>) -> None</code>
- <code title="post /payments/international/swift">client.payments.international.<a href="./src/aibanking/resources/payments/international.py">execute_swift</a>(\*\*<a href="src/aibanking/types/payments/international_execute_swift_params.py">params</a>) -> None</code>
- <code title="get /payments/international/{paymentId}/status">client.payments.international.<a href="./src/aibanking/resources/payments/international.py">get_status</a>(payment_id) -> <a href="./src/aibanking/types/payments/international_get_status_response.py">InternationalGetStatusResponse</a></code>

## Fx

Types:

```python
from aibanking.types.payments import FxGetRatesResponse
```

Methods:

- <code title="post /payments/fx/deals">client.payments.fx.<a href="./src/aibanking/resources/payments/fx.py">book_deal</a>(\*\*<a href="src/aibanking/types/payments/fx_book_deal_params.py">params</a>) -> None</code>
- <code title="post /payments/fx/convert">client.payments.fx.<a href="./src/aibanking/resources/payments/fx.py">execute_conversion</a>(\*\*<a href="src/aibanking/types/payments/fx_execute_conversion_params.py">params</a>) -> None</code>
- <code title="get /payments/fx/rates">client.payments.fx.<a href="./src/aibanking/resources/payments/fx.py">get_rates</a>(\*\*<a href="src/aibanking/types/payments/fx_get_rates_params.py">params</a>) -> <a href="./src/aibanking/types/payments/fx_get_rates_response.py">FxGetRatesResponse</a></code>

# Sustainability

Types:

```python
from aibanking.types import SustainabilityRetrieveCarbonFootprintResponse
```

Methods:

- <code title="get /sustainability/carbon-footprint">client.sustainability.<a href="./src/aibanking/resources/sustainability/sustainability.py">retrieve_carbon_footprint</a>() -> <a href="./src/aibanking/types/sustainability_retrieve_carbon_footprint_response.py">SustainabilityRetrieveCarbonFootprintResponse</a></code>

## Offsets

Methods:

- <code title="post /sustainability/offsets/purchase">client.sustainability.offsets.<a href="./src/aibanking/resources/sustainability/offsets.py">purchase_credits</a>(\*\*<a href="src/aibanking/types/sustainability/offset_purchase_credits_params.py">params</a>) -> None</code>
- <code title="post /sustainability/offsets/retire">client.sustainability.offsets.<a href="./src/aibanking/resources/sustainability/offsets.py">retire_credits</a>(\*\*<a href="src/aibanking/types/sustainability/offset_retire_credits_params.py">params</a>) -> None</code>

## Impact

Types:

```python
from aibanking.types.sustainability import (
    ImpactListGlobalGreenProjectsResponse,
    ImpactRetrievePortfolioImpactResponse,
)
```

Methods:

- <code title="get /sustainability/impact/projects">client.sustainability.impact.<a href="./src/aibanking/resources/sustainability/impact.py">list_global_green_projects</a>(\*\*<a href="src/aibanking/types/sustainability/impact_list_global_green_projects_params.py">params</a>) -> <a href="./src/aibanking/types/sustainability/impact_list_global_green_projects_response.py">ImpactListGlobalGreenProjectsResponse</a></code>
- <code title="get /sustainability/impact/portfolio">client.sustainability.impact.<a href="./src/aibanking/resources/sustainability/impact.py">retrieve_portfolio_impact</a>() -> <a href="./src/aibanking/types/sustainability/impact_retrieve_portfolio_impact_response.py">ImpactRetrievePortfolioImpactResponse</a></code>

# Marketplace

Types:

```python
from aibanking.types import MarketplaceListProductsResponse
```

Methods:

- <code title="get /marketplace/products">client.marketplace.<a href="./src/aibanking/resources/marketplace/marketplace.py">list_products</a>() -> <a href="./src/aibanking/types/marketplace_list_products_response.py">MarketplaceListProductsResponse</a></code>

## Offers

Types:

```python
from aibanking.types.marketplace import OfferListOffersResponse
```

Methods:

- <code title="get /marketplace/offers">client.marketplace.offers.<a href="./src/aibanking/resources/marketplace/offers.py">list_offers</a>() -> <a href="./src/aibanking/types/marketplace/offer_list_offers_response.py">OfferListOffersResponse</a></code>
- <code title="post /marketplace/offers/{offerId}/redeem">client.marketplace.offers.<a href="./src/aibanking/resources/marketplace/offers.py">redeem_offer</a>(offer_id) -> None</code>

# Lending

## Applications

Types:

```python
from aibanking.types.lending import ApplicationSubmitResponse, ApplicationTrackStatusResponse
```

Methods:

- <code title="post /lending/applications">client.lending.applications.<a href="./src/aibanking/resources/lending/applications.py">submit</a>(\*\*<a href="src/aibanking/types/lending/application_submit_params.py">params</a>) -> <a href="./src/aibanking/types/lending/application_submit_response.py">ApplicationSubmitResponse</a></code>
- <code title="get /lending/applications/{appId}/status">client.lending.applications.<a href="./src/aibanking/resources/lending/applications.py">track_status</a>(app_id) -> <a href="./src/aibanking/types/lending/application_track_status_response.py">ApplicationTrackStatusResponse</a></code>

## Decisions

Types:

```python
from aibanking.types.lending import DecisionGetRationaleResponse
```

Methods:

- <code title="get /lending/decisions/{decisionId}/rationale">client.lending.decisions.<a href="./src/aibanking/resources/lending/decisions.py">get_rationale</a>(decision_id) -> <a href="./src/aibanking/types/lending/decision_get_rationale_response.py">DecisionGetRationaleResponse</a></code>

# Investments

## Portfolios

Types:

```python
from aibanking.types.investments import PortfolioListResponse, PortfolioRebalanceResponse
```

Methods:

- <code title="post /investments/portfolios">client.investments.portfolios.<a href="./src/aibanking/resources/investments/portfolios.py">create</a>(\*\*<a href="src/aibanking/types/investments/portfolio_create_params.py">params</a>) -> None</code>
- <code title="get /investments/portfolios/{portfolioId}">client.investments.portfolios.<a href="./src/aibanking/resources/investments/portfolios.py">retrieve</a>(portfolio_id) -> None</code>
- <code title="put /investments/portfolios/{portfolioId}">client.investments.portfolios.<a href="./src/aibanking/resources/investments/portfolios.py">update</a>(portfolio_id, \*\*<a href="src/aibanking/types/investments/portfolio_update_params.py">params</a>) -> None</code>
- <code title="get /investments/portfolios">client.investments.portfolios.<a href="./src/aibanking/resources/investments/portfolios.py">list</a>(\*\*<a href="src/aibanking/types/investments/portfolio_list_params.py">params</a>) -> <a href="./src/aibanking/types/investments/portfolio_list_response.py">PortfolioListResponse</a></code>
- <code title="post /investments/portfolios/{portfolioId}/rebalance">client.investments.portfolios.<a href="./src/aibanking/resources/investments/portfolios.py">rebalance</a>(portfolio_id, \*\*<a href="src/aibanking/types/investments/portfolio_rebalance_params.py">params</a>) -> <a href="./src/aibanking/types/investments/portfolio_rebalance_response.py">PortfolioRebalanceResponse</a></code>

## Assets

Types:

```python
from aibanking.types.investments import AssetSearchResponse
```

Methods:

- <code title="get /investments/assets/search">client.investments.assets.<a href="./src/aibanking/resources/investments/assets.py">search</a>(\*\*<a href="src/aibanking/types/investments/asset_search_params.py">params</a>) -> <a href="./src/aibanking/types/investments/asset_search_response.py">AssetSearchResponse</a></code>

## Performance

Types:

```python
from aibanking.types.investments import PerformanceGetHistoricalResponse
```

Methods:

- <code title="get /investments/performance/historical">client.investments.performance.<a href="./src/aibanking/resources/investments/performance.py">get_historical</a>(\*\*<a href="src/aibanking/types/investments/performance_get_historical_params.py">params</a>) -> <a href="./src/aibanking/types/investments/performance_get_historical_response.py">PerformanceGetHistoricalResponse</a></code>

# System

Types:

```python
from aibanking.types import SystemGetAuditLogsResponse, SystemGetStatusResponse
```

Methods:

- <code title="get /system/audit-logs">client.system.<a href="./src/aibanking/resources/system/system.py">get_audit_logs</a>(\*\*<a href="src/aibanking/types/system_get_audit_logs_params.py">params</a>) -> <a href="./src/aibanking/types/system_get_audit_logs_response.py">SystemGetAuditLogsResponse</a></code>
- <code title="get /system/status">client.system.<a href="./src/aibanking/resources/system/system.py">get_status</a>() -> <a href="./src/aibanking/types/system_get_status_response.py">SystemGetStatusResponse</a></code>

## Webhooks

Types:

```python
from aibanking.types.system import WebhookListResponse
```

Methods:

- <code title="get /system/webhooks">client.system.webhooks.<a href="./src/aibanking/resources/system/webhooks.py">list</a>() -> <a href="./src/aibanking/types/system/webhook_list_response.py">WebhookListResponse</a></code>
- <code title="delete /system/webhooks/{webhookId}">client.system.webhooks.<a href="./src/aibanking/resources/system/webhooks.py">delete</a>(webhook_id) -> None</code>
- <code title="post /system/webhooks">client.system.webhooks.<a href="./src/aibanking/resources/system/webhooks.py">register</a>(\*\*<a href="src/aibanking/types/system/webhook_register_params.py">params</a>) -> None</code>

## Sandbox

Types:

```python
from aibanking.types.system import SandboxSimulateErrorResponse
```

Methods:

- <code title="post /system/sandbox/reset">client.system.sandbox.<a href="./src/aibanking/resources/system/sandbox.py">reset</a>() -> None</code>
- <code title="post /system/sandbox/simulate-error">client.system.sandbox.<a href="./src/aibanking/resources/system/sandbox.py">simulate_error</a>(\*\*<a href="src/aibanking/types/system/sandbox_simulate_error_params.py">params</a>) -> <a href="./src/aibanking/types/system/sandbox_simulate_error_response.py">SandboxSimulateErrorResponse</a></code>

## Verification

Methods:

- <code title="post /system/verification/biometric-comparison">client.system.verification.<a href="./src/aibanking/resources/system/verification.py">compare_biometric</a>(\*\*<a href="src/aibanking/types/system/verification_compare_biometric_params.py">params</a>) -> None</code>
- <code title="post /system/verification/document">client.system.verification.<a href="./src/aibanking/resources/system/verification.py">verify_document</a>() -> None</code>

## Notifications

Types:

```python
from aibanking.types.system import NotificationListTemplatesResponse
```

Methods:

- <code title="get /system/notifications/templates">client.system.notifications.<a href="./src/aibanking/resources/system/notifications.py">list_templates</a>() -> <a href="./src/aibanking/types/system/notification_list_templates_response.py">NotificationListTemplatesResponse</a></code>
- <code title="post /system/notifications/push">client.system.notifications.<a href="./src/aibanking/resources/system/notifications.py">send_push</a>(\*\*<a href="src/aibanking/types/system/notification_send_push_params.py">params</a>) -> None</code>
