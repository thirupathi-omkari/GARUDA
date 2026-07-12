# GARUDA Quant Lab

## Module 8 — Risk & Position Sizing

## Status

Completed.

Final regression result:

100 tests passed.

---

## 1. Module Objective

Module 8 introduces the risk-management and position-sizing layer for GARUDA Quant Lab.

The module ensures that proposed trades are evaluated against account capital, position-sizing rules, portfolio exposure limits, daily loss limits, open-position limits, and portfolio risk limits before execution.

It also extends the backtesting architecture with pre-execution risk evaluation, multi-session capital progression, equity-curve tracking, and multi-session performance reporting.

---

## 2. Risk Architecture

The Module 8 risk architecture consists of the following components:

- Trading Account
- Risk Configuration
- Risk Calculator
- Position Sizer
- Quantity Rules
- Daily Loss Control
- Exposure Control
- Position Limit Control
- Portfolio Risk Control
- Risk Manager
- Equity Curve

The central coordinator is the Risk Manager.

The Risk Manager evaluates proposed trades against GARUDA's configured risk rules and returns a Risk Decision.

---

## 3. Trading Account

File:

`src/risk/account.py`

The Trading Account maintains:

- Initial capital
- Current capital

Current capital is updated as executed trades generate profits or losses.

---

## 4. Risk Configuration

File:

`src/risk/risk_config.py`

The Risk Configuration defines GARUDA's risk parameters, including:

- Risk per trade percentage
- Maximum daily loss percentage
- Maximum portfolio exposure percentage
- Maximum portfolio risk percentage
- Maximum open positions

These parameters are used by the Risk Manager during trade evaluation.

---

## 5. Risk Calculation

File:

`src/risk/risk_calculator.py`

The Risk Calculator determines the maximum capital amount that GARUDA may risk on a proposed trade.

The calculation uses:

- Current account capital
- Configured risk-per-trade percentage

---

## 6. Position Sizing

Files:

`src/risk/position_sizer.py`

`src/risk/quantity_rules.py`

Position sizing calculates the raw trade quantity using:

- Allowed risk amount
- Entry price
- Stop-loss price

Quantity rules then adjust the raw position size according to the required lot size.

Trades that cannot satisfy the minimum lot-size requirement are rejected.

---

## 7. Daily Loss Control

File:

`src/risk/daily_loss_control.py`

Daily loss control prevents new trades when the configured maximum daily loss limit has been reached.

---

## 8. Exposure Control

File:

`src/risk/exposure_control.py`

Exposure control verifies that a proposed trade will not exceed GARUDA's configured maximum portfolio exposure.

---

## 9. Position Limit Control

File:

`src/risk/position_limit_control.py`

Position limit control prevents GARUDA from opening more positions than the configured maximum.

---

## 10. Portfolio Risk Control

File:

`src/risk/portfolio_risk_control.py`

Portfolio risk control verifies that the proposed trade risk, combined with current open risk, remains within the configured maximum portfolio risk limit.

---

## 11. Risk Manager

File:

`src/risk/risk_manager.py`

The Risk Manager is the central coordinator of Module 8.

Trade evaluation follows this sequence:

1. Daily loss check
2. Open-position limit check
3. Risk amount calculation
4. Raw position-size calculation
5. Lot-size adjustment
6. Portfolio exposure check
7. Portfolio risk check
8. Final trade approval or rejection

The Risk Manager returns a Risk Decision containing:

- Approval status
- Decision reason
- Risk amount
- Raw position size
- Approved quantity
- Proposed exposure

---

## 12. Risk-Aware Backtesting

File:

`src/backtesting/risk_aware_backtester.py`

The risk-aware backtesting layer connects the existing Module 7 backtesting engine with the Module 8 Risk Manager.

Generated trades are evaluated using GARUDA's risk rules.

Possible results include:

- Approved
- Rejected
- No Trade

---

## 13. Pre-Execution Risk Backtesting

File:

`src/backtesting/pre_execution_risk_backtester.py`

The pre-execution risk backtester evaluates proposed trades before trade execution.

The workflow is:

1. Validate session data
2. Generate historical signals
3. Find the first valid signal
4. Prevent last-candle entries
5. Create the proposed entry
6. Calculate stop-loss and target levels
7. Evaluate the proposed trade using the Risk Manager
8. Reject trades that fail risk checks
9. Create approved trades
10. Simulate trade exit
11. Apply slippage
12. Calculate final P&L
13. Return the completed result

This architecture ensures that risk evaluation occurs before historical trade execution.

---

## 14. Multi-Session Risk Backtesting

File:

`src/backtesting/multi_session_risk_backtester.py`

The multi-session risk backtester processes historical trading sessions sequentially.

It tracks:

- Total sessions
- Executed trades
- Rejected trades
- No-trade sessions
- Initial capital
- Final capital
- Total net P&L
- Return percentage
- Performance summary

Only executed trades update account capital.

Rejected trades and no-trade sessions do not change capital.

---

## 15. Equity Curve Tracking

File:

`src/risk/equity_curve.py`

The Equity Curve tracks account equity across completed trades.

It supports:

- Initial equity
- Current equity
- Sequential trade P&L recording
- Equity history
- Trade count
- Net P&L
- Return percentage
- Peak equity
- Lowest equity

Initial equity must be greater than zero.

---

## 16. Multi-Session Performance Summary

The multi-session backtesting architecture reuses the existing Module 7 performance metrics engine.

Only executed trades are included in the performance summary.

The summary includes:

- Total trades
- Winning trades
- Losing trades
- Breakeven trades
- Total net P&L
- Win rate
- Profit factor
- Expectancy
- Maximum drawdown

This avoids duplicating performance-calculation logic.

---

## 17. Multi-Session Risk Integration

Module 8 integration tests verify that:

- Only executed trades update account capital
- Rejected trades preserve capital
- No-trade sessions preserve capital
- Session counts remain consistent
- Multiple executed trades update capital sequentially
- Performance summaries contain only executed trades
- Multi-session P&L matches performance-summary P&L
- Account capital matches final backtest capital
- Equity-curve results match multi-session results

---

## 18. Final Module Integration

The final Module 8 integration test connects:

- Trading Account
- Risk Configuration
- Risk Manager
- Multi-Session Risk Backtester
- Performance Summary
- Equity Curve

The integration test verifies consistency between:

- Account capital
- Multi-session final capital
- Total net P&L
- Performance-summary P&L
- Executed trade count
- Equity-curve trade count
- Equity-curve final equity

---

## 19. Testing

Module 8 includes tests for:

- Trading account
- Risk configuration
- Risk calculation
- Position sizing
- Quantity rules
- Daily loss control
- Exposure control
- Position limit control
- Portfolio risk control
- Risk Manager
- Risk-aware backtesting
- Pre-execution risk backtesting
- Multi-session risk backtesting
- Equity-curve tracking
- Multi-session performance summary
- Multi-session risk integration
- Final Module 8 integration

Final regression result:

`100 passed`

---

## 20. Module 8 Completion Status

Module 8 — Risk & Position Sizing is complete.

GARUDA Quant Lab now has a tested risk-management architecture capable of evaluating proposed trades before execution, calculating position size, enforcing portfolio risk controls, tracking capital across multiple sessions, generating performance summaries, and validating equity progression.

The project is ready to proceed to Module 9.
