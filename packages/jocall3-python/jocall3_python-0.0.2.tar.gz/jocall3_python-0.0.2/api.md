# Users

Types:

```python
from jocall3.types import UserLoginResponse, UserRegisterResponse
```

Methods:

- <code title="post /users/login">client.users.<a href="./src/jocall3/resources/users/users.py">login</a>(\*\*<a href="src/jocall3/types/user_login_params.py">params</a>) -> <a href="./src/jocall3/types/user_login_response.py">UserLoginResponse</a></code>
- <code title="post /users/register">client.users.<a href="./src/jocall3/resources/users/users.py">register</a>(\*\*<a href="src/jocall3/types/user_register_params.py">params</a>) -> <a href="./src/jocall3/types/user_register_response.py">UserRegisterResponse</a></code>

## PasswordReset

Types:

```python
from jocall3.types.users import PasswordResetConfirmResponse, PasswordResetInitiateResponse
```

Methods:

- <code title="post /users/password-reset/confirm">client.users.password_reset.<a href="./src/jocall3/resources/users/password_reset.py">confirm</a>(\*\*<a href="src/jocall3/types/users/password_reset_confirm_params.py">params</a>) -> <a href="./src/jocall3/types/users/password_reset_confirm_response.py">PasswordResetConfirmResponse</a></code>
- <code title="post /users/password-reset/initiate">client.users.password_reset.<a href="./src/jocall3/resources/users/password_reset.py">initiate</a>(\*\*<a href="src/jocall3/types/users/password_reset_initiate_params.py">params</a>) -> <a href="./src/jocall3/types/users/password_reset_initiate_response.py">PasswordResetInitiateResponse</a></code>

## Me

Types:

```python
from jocall3.types.users import MeRetrieveResponse, MeUpdateResponse, MeListDevicesResponse
```

Methods:

- <code title="get /users/me">client.users.me.<a href="./src/jocall3/resources/users/me/me.py">retrieve</a>() -> <a href="./src/jocall3/types/users/me_retrieve_response.py">MeRetrieveResponse</a></code>
- <code title="put /users/me">client.users.me.<a href="./src/jocall3/resources/users/me/me.py">update</a>(\*\*<a href="src/jocall3/types/users/me_update_params.py">params</a>) -> <a href="./src/jocall3/types/users/me_update_response.py">MeUpdateResponse</a></code>
- <code title="get /users/me/devices">client.users.me.<a href="./src/jocall3/resources/users/me/me.py">list_devices</a>(\*\*<a href="src/jocall3/types/users/me_list_devices_params.py">params</a>) -> <a href="./src/jocall3/types/users/me_list_devices_response.py">MeListDevicesResponse</a></code>

### Preferences

Types:

```python
from jocall3.types.users.me import PreferenceRetrieveResponse, PreferenceUpdateResponse
```

Methods:

- <code title="get /users/me/preferences">client.users.me.preferences.<a href="./src/jocall3/resources/users/me/preferences.py">retrieve</a>() -> <a href="./src/jocall3/types/users/me/preference_retrieve_response.py">PreferenceRetrieveResponse</a></code>
- <code title="put /users/me/preferences">client.users.me.preferences.<a href="./src/jocall3/resources/users/me/preferences.py">update</a>(\*\*<a href="src/jocall3/types/users/me/preference_update_params.py">params</a>) -> <a href="./src/jocall3/types/users/me/preference_update_response.py">PreferenceUpdateResponse</a></code>

### Biometrics

Types:

```python
from jocall3.types.users.me import BiometricRetrieveStatusResponse, BiometricVerifyResponse
```

Methods:

- <code title="get /users/me/biometrics">client.users.me.biometrics.<a href="./src/jocall3/resources/users/me/biometrics.py">retrieve_status</a>() -> <a href="./src/jocall3/types/users/me/biometric_retrieve_status_response.py">BiometricRetrieveStatusResponse</a></code>
- <code title="post /users/me/biometrics/verify">client.users.me.biometrics.<a href="./src/jocall3/resources/users/me/biometrics.py">verify</a>(\*\*<a href="src/jocall3/types/users/me/biometric_verify_params.py">params</a>) -> <a href="./src/jocall3/types/users/me/biometric_verify_response.py">BiometricVerifyResponse</a></code>

# Accounts

Types:

```python
from jocall3.types import (
    AccountLinkResponse,
    AccountRetrieveDetailsResponse,
    AccountRetrieveMeResponse,
    AccountRetrieveStatementsResponse,
)
```

Methods:

- <code title="post /accounts/link">client.accounts.<a href="./src/jocall3/resources/accounts/accounts.py">link</a>(\*\*<a href="src/jocall3/types/account_link_params.py">params</a>) -> <a href="./src/jocall3/types/account_link_response.py">AccountLinkResponse</a></code>
- <code title="get /accounts/{accountId}/details">client.accounts.<a href="./src/jocall3/resources/accounts/accounts.py">retrieve_details</a>(account_id) -> <a href="./src/jocall3/types/account_retrieve_details_response.py">AccountRetrieveDetailsResponse</a></code>
- <code title="get /accounts/me">client.accounts.<a href="./src/jocall3/resources/accounts/accounts.py">retrieve_me</a>(\*\*<a href="src/jocall3/types/account_retrieve_me_params.py">params</a>) -> <a href="./src/jocall3/types/account_retrieve_me_response.py">AccountRetrieveMeResponse</a></code>
- <code title="get /accounts/{accountId}/statements">client.accounts.<a href="./src/jocall3/resources/accounts/accounts.py">retrieve_statements</a>(account_id, \*\*<a href="src/jocall3/types/account_retrieve_statements_params.py">params</a>) -> <a href="./src/jocall3/types/account_retrieve_statements_response.py">AccountRetrieveStatementsResponse</a></code>

## Transactions

Types:

```python
from jocall3.types.accounts import TransactionRetrievePendingResponse
```

Methods:

- <code title="get /accounts/{accountId}/transactions/pending">client.accounts.transactions.<a href="./src/jocall3/resources/accounts/transactions.py">retrieve_pending</a>(account_id, \*\*<a href="src/jocall3/types/accounts/transaction_retrieve_pending_params.py">params</a>) -> <a href="./src/jocall3/types/accounts/transaction_retrieve_pending_response.py">TransactionRetrievePendingResponse</a></code>

## OverdraftSettings

Types:

```python
from jocall3.types.accounts import (
    OverdraftSettingRetrieveOverdraftSettingsResponse,
    OverdraftSettingUpdateOverdraftSettingsResponse,
)
```

Methods:

- <code title="get /accounts/{accountId}/overdraft-settings">client.accounts.overdraft_settings.<a href="./src/jocall3/resources/accounts/overdraft_settings.py">retrieve_overdraft_settings</a>(account_id) -> <a href="./src/jocall3/types/accounts/overdraft_setting_retrieve_overdraft_settings_response.py">OverdraftSettingRetrieveOverdraftSettingsResponse</a></code>
- <code title="put /accounts/{accountId}/overdraft-settings">client.accounts.overdraft_settings.<a href="./src/jocall3/resources/accounts/overdraft_settings.py">update_overdraft_settings</a>(account_id, \*\*<a href="src/jocall3/types/accounts/overdraft_setting_update_overdraft_settings_params.py">params</a>) -> <a href="./src/jocall3/types/accounts/overdraft_setting_update_overdraft_settings_response.py">OverdraftSettingUpdateOverdraftSettingsResponse</a></code>

# Transactions

Types:

```python
from jocall3.types import (
    TransactionRetrieveResponse,
    TransactionListResponse,
    TransactionCategorizeResponse,
    TransactionListRecurringResponse,
    TransactionUpdateNotesResponse,
)
```

Methods:

- <code title="get /transactions/{transactionId}">client.transactions.<a href="./src/jocall3/resources/transactions/transactions.py">retrieve</a>(transaction_id) -> <a href="./src/jocall3/types/transaction_retrieve_response.py">TransactionRetrieveResponse</a></code>
- <code title="get /transactions">client.transactions.<a href="./src/jocall3/resources/transactions/transactions.py">list</a>(\*\*<a href="src/jocall3/types/transaction_list_params.py">params</a>) -> <a href="./src/jocall3/types/transaction_list_response.py">TransactionListResponse</a></code>
- <code title="put /transactions/{transactionId}/categorize">client.transactions.<a href="./src/jocall3/resources/transactions/transactions.py">categorize</a>(transaction_id, \*\*<a href="src/jocall3/types/transaction_categorize_params.py">params</a>) -> <a href="./src/jocall3/types/transaction_categorize_response.py">TransactionCategorizeResponse</a></code>
- <code title="get /transactions/recurring">client.transactions.<a href="./src/jocall3/resources/transactions/transactions.py">list_recurring</a>(\*\*<a href="src/jocall3/types/transaction_list_recurring_params.py">params</a>) -> <a href="./src/jocall3/types/transaction_list_recurring_response.py">TransactionListRecurringResponse</a></code>
- <code title="put /transactions/{transactionId}/notes">client.transactions.<a href="./src/jocall3/resources/transactions/transactions.py">update_notes</a>(transaction_id, \*\*<a href="src/jocall3/types/transaction_update_notes_params.py">params</a>) -> <a href="./src/jocall3/types/transaction_update_notes_response.py">TransactionUpdateNotesResponse</a></code>

## Insights

Types:

```python
from jocall3.types.transactions import InsightGetSpendingTrendsResponse
```

Methods:

- <code title="get /transactions/insights/spending-trends">client.transactions.insights.<a href="./src/jocall3/resources/transactions/insights.py">get_spending_trends</a>() -> <a href="./src/jocall3/types/transactions/insight_get_spending_trends_response.py">InsightGetSpendingTrendsResponse</a></code>

# Budgets

Types:

```python
from jocall3.types import BudgetRetrieveResponse, BudgetUpdateResponse, BudgetListResponse
```

Methods:

- <code title="get /budgets/{budgetId}">client.budgets.<a href="./src/jocall3/resources/budgets.py">retrieve</a>(budget_id) -> <a href="./src/jocall3/types/budget_retrieve_response.py">BudgetRetrieveResponse</a></code>
- <code title="put /budgets/{budgetId}">client.budgets.<a href="./src/jocall3/resources/budgets.py">update</a>(budget_id, \*\*<a href="src/jocall3/types/budget_update_params.py">params</a>) -> <a href="./src/jocall3/types/budget_update_response.py">BudgetUpdateResponse</a></code>
- <code title="get /budgets">client.budgets.<a href="./src/jocall3/resources/budgets.py">list</a>(\*\*<a href="src/jocall3/types/budget_list_params.py">params</a>) -> <a href="./src/jocall3/types/budget_list_response.py">BudgetListResponse</a></code>

# Investments

## Portfolios

Methods:

- <code title="get /investments/portfolios/{portfolioId}">client.investments.portfolios.<a href="./src/jocall3/resources/investments/portfolios.py">retrieve</a>(portfolio_id) -> object</code>
- <code title="put /investments/portfolios/{portfolioId}">client.investments.portfolios.<a href="./src/jocall3/resources/investments/portfolios.py">update</a>(portfolio_id) -> object</code>
- <code title="get /investments/portfolios">client.investments.portfolios.<a href="./src/jocall3/resources/investments/portfolios.py">list</a>(\*\*<a href="src/jocall3/types/investments/portfolio_list_params.py">params</a>) -> object</code>
- <code title="post /investments/portfolios/{portfolioId}/rebalance">client.investments.portfolios.<a href="./src/jocall3/resources/investments/portfolios.py">rebalance</a>(portfolio_id) -> object</code>

## Assets

Methods:

- <code title="get /investments/assets/search">client.investments.assets.<a href="./src/jocall3/resources/investments/assets.py">search</a>(\*\*<a href="src/jocall3/types/investments/asset_search_params.py">params</a>) -> object</code>

# AI

## Advisor

Methods:

- <code title="get /ai/advisor/tools">client.ai.advisor.<a href="./src/jocall3/resources/ai/advisor/advisor.py">list_tools</a>(\*\*<a href="src/jocall3/types/ai/advisor_list_tools_params.py">params</a>) -> object</code>

### Chat

Methods:

- <code title="get /ai/advisor/chat/history">client.ai.advisor.chat.<a href="./src/jocall3/resources/ai/advisor/chat.py">retrieve_history</a>(\*\*<a href="src/jocall3/types/ai/advisor/chat_retrieve_history_params.py">params</a>) -> object</code>
- <code title="post /ai/advisor/chat">client.ai.advisor.chat.<a href="./src/jocall3/resources/ai/advisor/chat.py">send_message</a>(\*\*<a href="src/jocall3/types/ai/advisor/chat_send_message_params.py">params</a>) -> object</code>

## Oracle

### Simulate

Types:

```python
from jocall3.types.ai.oracle import SimulateRunStandardSimulationResponse
```

Methods:

- <code title="post /ai/oracle/simulate/advanced">client.ai.oracle.simulate.<a href="./src/jocall3/resources/ai/oracle/simulate.py">run_advanced_simulation</a>(\*\*<a href="src/jocall3/types/ai/oracle/simulate_run_advanced_simulation_params.py">params</a>) -> object</code>
- <code title="post /ai/oracle/simulate">client.ai.oracle.simulate.<a href="./src/jocall3/resources/ai/oracle/simulate.py">run_standard_simulation</a>() -> <a href="./src/jocall3/types/ai/oracle/simulate_run_standard_simulation_response.py">SimulateRunStandardSimulationResponse</a></code>

### Simulations

Types:

```python
from jocall3.types.ai.oracle import SimulationRetrieveResultsResponse
```

Methods:

- <code title="get /ai/oracle/simulations">client.ai.oracle.simulations.<a href="./src/jocall3/resources/ai/oracle/simulations.py">list_all</a>(\*\*<a href="src/jocall3/types/ai/oracle/simulation_list_all_params.py">params</a>) -> object</code>
- <code title="get /ai/oracle/simulations/{simulationId}">client.ai.oracle.simulations.<a href="./src/jocall3/resources/ai/oracle/simulations.py">retrieve_results</a>(simulation_id) -> <a href="./src/jocall3/types/ai/oracle/simulation_retrieve_results_response.py">SimulationRetrieveResultsResponse</a></code>

## Incubator

Methods:

- <code title="get /ai/incubator/pitches">client.ai.incubator.<a href="./src/jocall3/resources/ai/incubator/incubator.py">list_pitches</a>(\*\*<a href="src/jocall3/types/ai/incubator_list_pitches_params.py">params</a>) -> object</code>

### Pitch

Types:

```python
from jocall3.types.ai.incubator import PitchRetrieveAnalysisResponse
```

Methods:

- <code title="get /ai/incubator/pitch/{pitchId}/details">client.ai.incubator.pitch.<a href="./src/jocall3/resources/ai/incubator/pitch.py">retrieve_analysis</a>(pitch_id) -> <a href="./src/jocall3/types/ai/incubator/pitch_retrieve_analysis_response.py">PitchRetrieveAnalysisResponse</a></code>
- <code title="post /ai/incubator/pitch">client.ai.incubator.pitch.<a href="./src/jocall3/resources/ai/incubator/pitch.py">submit_business_plan</a>(\*\*<a href="src/jocall3/types/ai/incubator/pitch_submit_business_plan_params.py">params</a>) -> object</code>
- <code title="put /ai/incubator/pitch/{pitchId}/feedback">client.ai.incubator.pitch.<a href="./src/jocall3/resources/ai/incubator/pitch.py">submit_feedback</a>(pitch_id) -> object</code>

## Ads

Methods:

- <code title="post /ai/ads/generate">client.ai.ads.<a href="./src/jocall3/resources/ai/ads.py">generate_video_ad</a>() -> object</code>
- <code title="get /ai/ads/operations/{operationId}">client.ai.ads.<a href="./src/jocall3/resources/ai/ads.py">get_generation_status</a>(operation_id) -> object</code>
- <code title="get /ai/ads">client.ai.ads.<a href="./src/jocall3/resources/ai/ads.py">list_generated_ads</a>(\*\*<a href="src/jocall3/types/ai/ad_list_generated_ads_params.py">params</a>) -> object</code>

# Corporate

Methods:

- <code title="post /corporate/sanction-screening">client.corporate.<a href="./src/jocall3/resources/corporate/corporate.py">perform_sanction_screening</a>(\*\*<a href="src/jocall3/types/corporate_perform_sanction_screening_params.py">params</a>) -> object</code>

## Cards

Types:

```python
from jocall3.types.corporate import (
    CardCreateVirtualResponse,
    CardFreezeResponse,
    CardUpdateControlsResponse,
)
```

Methods:

- <code title="get /corporate/cards">client.corporate.cards.<a href="./src/jocall3/resources/corporate/cards.py">list</a>(\*\*<a href="src/jocall3/types/corporate/card_list_params.py">params</a>) -> object</code>
- <code title="post /corporate/cards/virtual">client.corporate.cards.<a href="./src/jocall3/resources/corporate/cards.py">create_virtual</a>(\*\*<a href="src/jocall3/types/corporate/card_create_virtual_params.py">params</a>) -> <a href="./src/jocall3/types/corporate/card_create_virtual_response.py">CardCreateVirtualResponse</a></code>
- <code title="post /corporate/cards/{cardId}/freeze">client.corporate.cards.<a href="./src/jocall3/resources/corporate/cards.py">freeze</a>(card_id) -> <a href="./src/jocall3/types/corporate/card_freeze_response.py">CardFreezeResponse</a></code>
- <code title="get /corporate/cards/{cardId}/transactions">client.corporate.cards.<a href="./src/jocall3/resources/corporate/cards.py">list_transactions</a>(card_id, \*\*<a href="src/jocall3/types/corporate/card_list_transactions_params.py">params</a>) -> object</code>
- <code title="put /corporate/cards/{cardId}/controls">client.corporate.cards.<a href="./src/jocall3/resources/corporate/cards.py">update_controls</a>(card_id) -> <a href="./src/jocall3/types/corporate/card_update_controls_response.py">CardUpdateControlsResponse</a></code>

## Anomalies

Methods:

- <code title="get /corporate/anomalies">client.corporate.anomalies.<a href="./src/jocall3/resources/corporate/anomalies.py">list</a>(\*\*<a href="src/jocall3/types/corporate/anomaly_list_params.py">params</a>) -> object</code>
- <code title="put /corporate/anomalies/{anomalyId}/status">client.corporate.anomalies.<a href="./src/jocall3/resources/corporate/anomalies.py">update_status</a>(anomaly_id) -> object</code>

## Compliance

### Audits

Types:

```python
from jocall3.types.corporate.compliance import AuditRetrieveReportResponse
```

Methods:

- <code title="post /corporate/compliance/audits">client.corporate.compliance.audits.<a href="./src/jocall3/resources/corporate/compliance/audits.py">request</a>() -> object</code>
- <code title="get /corporate/compliance/audits/{auditId}/report">client.corporate.compliance.audits.<a href="./src/jocall3/resources/corporate/compliance/audits.py">retrieve_report</a>(audit_id) -> <a href="./src/jocall3/types/corporate/compliance/audit_retrieve_report_response.py">AuditRetrieveReportResponse</a></code>

## Treasury

Types:

```python
from jocall3.types.corporate import TreasuryGetLiquidityPositionsResponse
```

Methods:

- <code title="get /corporate/treasury/liquidity-positions">client.corporate.treasury.<a href="./src/jocall3/resources/corporate/treasury/treasury.py">get_liquidity_positions</a>() -> <a href="./src/jocall3/types/corporate/treasury_get_liquidity_positions_response.py">TreasuryGetLiquidityPositionsResponse</a></code>

### CashFlow

Types:

```python
from jocall3.types.corporate.treasury import CashFlowForecastResponse
```

Methods:

- <code title="get /corporate/treasury/cash-flow/forecast">client.corporate.treasury.cash_flow.<a href="./src/jocall3/resources/corporate/treasury/cash_flow.py">forecast</a>(\*\*<a href="src/jocall3/types/corporate/treasury/cash_flow_forecast_params.py">params</a>) -> <a href="./src/jocall3/types/corporate/treasury/cash_flow_forecast_response.py">CashFlowForecastResponse</a></code>

## Risk

### Fraud

#### Rules

Types:

```python
from jocall3.types.corporate.risk.fraud import RuleUpdateResponse
```

Methods:

- <code title="put /corporate/risk/fraud/rules/{ruleId}">client.corporate.risk.fraud.rules.<a href="./src/jocall3/resources/corporate/risk/fraud/rules.py">update</a>(rule_id, \*\*<a href="src/jocall3/types/corporate/risk/fraud/rule_update_params.py">params</a>) -> <a href="./src/jocall3/types/corporate/risk/fraud/rule_update_response.py">RuleUpdateResponse</a></code>
- <code title="get /corporate/risk/fraud/rules">client.corporate.risk.fraud.rules.<a href="./src/jocall3/resources/corporate/risk/fraud/rules.py">list</a>(\*\*<a href="src/jocall3/types/corporate/risk/fraud/rule_list_params.py">params</a>) -> object</code>

# Web3

Methods:

- <code title="get /web3/nfts">client.web3.<a href="./src/jocall3/resources/web3/web3.py">retrieve_nfts</a>(\*\*<a href="src/jocall3/types/web3_retrieve_nfts_params.py">params</a>) -> object</code>

## Wallets

Methods:

- <code title="post /web3/wallets">client.web3.wallets.<a href="./src/jocall3/resources/web3/wallets.py">create</a>() -> object</code>
- <code title="get /web3/wallets">client.web3.wallets.<a href="./src/jocall3/resources/web3/wallets.py">list</a>(\*\*<a href="src/jocall3/types/web3/wallet_list_params.py">params</a>) -> object</code>
- <code title="get /web3/wallets/{walletId}/balances">client.web3.wallets.<a href="./src/jocall3/resources/web3/wallets.py">retrieve_balances</a>(wallet_id, \*\*<a href="src/jocall3/types/web3/wallet_retrieve_balances_params.py">params</a>) -> object</code>

## Transactions

Methods:

- <code title="post /web3/transactions/initiate">client.web3.transactions.<a href="./src/jocall3/resources/web3/transactions.py">initiate</a>() -> object</code>

# Payments

## International

Methods:

- <code title="get /payments/international/{paymentId}/status">client.payments.international.<a href="./src/jocall3/resources/payments/international.py">retrieve_status</a>(payment_id) -> object</code>

## Fx

Types:

```python
from jocall3.types.payments import FxRetrieveRatesResponse
```

Methods:

- <code title="post /payments/fx/convert">client.payments.fx.<a href="./src/jocall3/resources/payments/fx.py">convert_currency</a>() -> object</code>
- <code title="get /payments/fx/rates">client.payments.fx.<a href="./src/jocall3/resources/payments/fx.py">retrieve_rates</a>(\*\*<a href="src/jocall3/types/payments/fx_retrieve_rates_params.py">params</a>) -> <a href="./src/jocall3/types/payments/fx_retrieve_rates_response.py">FxRetrieveRatesResponse</a></code>

# Sustainability

Methods:

- <code title="get /sustainability/carbon-footprint">client.sustainability.<a href="./src/jocall3/resources/sustainability/sustainability.py">retrieve_carbon_footprint</a>() -> object</code>

## Investments

Types:

```python
from jocall3.types.sustainability import InvestmentAnalyzeImpactResponse
```

Methods:

- <code title="get /sustainability/investments/impact">client.sustainability.investments.<a href="./src/jocall3/resources/sustainability/investments.py">analyze_impact</a>() -> <a href="./src/jocall3/types/sustainability/investment_analyze_impact_response.py">InvestmentAnalyzeImpactResponse</a></code>
