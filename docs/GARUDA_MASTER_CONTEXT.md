# GARUDA QUANT LAB — MASTER PROJECT CONTEXT

**Document Purpose:** Authoritative continuity and development handoff document
**Project:** GARUDA Quant Lab
**Current Development Stage:** Module 9 — Paper Trading Engine
**Current Checkpoint:** 245 tests passed
**Next Development Step:** Module 9 Part 13F-1 — Single-Cycle Live Paper Trading Orchestration Engine
**Last Updated:** 12 July 2026

---

# 1. PROJECT PURPOSE

GARUDA Quant Lab is a personal AI-assisted quantitative trading platform designed for systematic market research, strategy development, backtesting, risk management, paper trading, and eventually automated live trading.

The project is being developed incrementally with a strong emphasis on:

- modular architecture;
- automated testing;
- reuse of existing components;
- separation of strategy, risk, execution, and broker responsibilities;
- visible execution output for learning and verification;
- gradual progression from research to live deployment;
- preservation of future scalability.

GARUDA is not intended to remain a single-strategy or single-market application.

The long-term platform must support expansion across:

- Indian equities;
- Indian Futures and Options;
- cryptocurrency markets;
- additional trading strategies;
- multiple brokers and market-data providers;
- cloud deployment;
- automated research;
- signal generation;
- alerts and reporting;
- paper trading;
- eventually automated order execution after sufficient validation.

---

# 2. OWNER AND DEVELOPMENT CONTEXT

GARUDA Quant Lab is being developed as a personal quantitative trading platform by Thirupathi Omkari.

The project is also a structured learning exercise.

Development explanations should therefore make clear:

- what is being built;
- why the component is necessary;
- where it fits in GARUDA;
- what input it receives;
- what output it produces;
- how it interacts with existing components;
- what visible result can be demonstrated.

Visible terminal output should be provided wherever useful without compromising the architecture.

Development speed is important, but architecture has higher priority.

The agreed rule is:

> Fast-track development when possible, but never fast-track by deviating from GARUDA's intended architecture.

---

# 3. AUTHORITATIVE DEVELOPMENT RULES

All future development must follow these rules.

## Rule 1 — Preserve Existing Architecture

Do not redesign completed modules without a demonstrated architectural reason.

## Rule 2 — Reuse Existing Components

Before creating new functionality, check whether GARUDA already contains the required logic.

Examples include:

- ORB strategy logic;
- VWAP calculation;
- strategy result models;
- exit-level calculation;
- candle exit evaluation;
- risk management;
- position sizing;
- exposure control;
- paper order management;
- simulated execution;
- virtual position management.

Do not duplicate existing business logic inside integration or runner files.

## Rule 3 — Complete Files Preferred

When code changes are required, provide complete file contents rather than isolated fragments whenever practical.

This reduces copy/paste mistakes and integration errors.

## Rule 4 — Protect Passing Tests

The current authoritative regression checkpoint is:

**245 tests passed**

New development must preserve the existing test suite.

Development sequence should normally be:

1. inspect interfaces;
2. implement one focused component;
3. add focused tests;
4. run focused tests;
5. run full regression;
6. commit a clean checkpoint.

## Rule 5 — Explain the Execution Flow

The developer should understand what GARUDA is doing.

Where useful, show flows such as:

Market Data
→ Strategy
→ Risk
→ Execution
→ Position
→ Exit
→ P&L

## Rule 6 — Use Real Components in Integrations

Demo and integration files should use the actual tested GARUDA components.

Do not create simplified duplicate strategy, risk, or execution logic merely to make a demo pass.

## Rule 7 — No Real Orders During Current Phase

Current Module 9 work uses:

- real Kite authentication;
- real Kite market data;
- real GARUDA strategy logic;
- real GARUDA risk controls;
- simulated orders;
- virtual positions;
- virtual capital.

No real broker orders should be sent during the current paper-trading phase.

## Rule 8 — Preserve Future Scaling

Architecture decisions must keep future expansion toward:

- equities;
- F&O;
- crypto;

in mind.

Avoid unnecessary hard-coding that would prevent multi-asset expansion.

## Rule 9 — Follow Agreed Phase Priority

The long-term agreed phase sequence is:

**Phase 1 first**

Then:

**Phase 3**

Then:

**Phase 2 and Phase 4 simultaneously**

Future development should preserve this priority unless the owner explicitly changes it.

## Rule 10 — Documentation Must Track Reality

This Master Context should be updated at major development checkpoints.

The repository source code and passing tests remain the final authority when documentation and implementation differ.

---

# 4. CURRENT PROJECT STRUCTURE

The main source structure is:

```text
src/
│
├── ai/
├── backtesting/
├── broker/
├── config/
├── core/
├── data/
├── execution/
├── indicators/
├── research/
├── risk/
├── scanner/
├── strategy/
└── utils/
```

The project follows a modular pipeline.

Conceptually:

```text
BROKER / MARKET DATA
        ↓
DATA PIPELINE
        ↓
MARKET SCANNER
        ↓
STRATEGY FRAMEWORK
        ↓
BACKTESTING
        ↓
RISK MANAGEMENT
        ↓
PAPER EXECUTION
        ↓
LIVE PAPER TRADING RUNNER
        ↓
ALERTING / REPORTING
        ↓
FUTURE LIVE EXECUTION
```

---

# 5. MODULE STATUS SUMMARY

## MODULE 1 — FOUNDATION AND PROJECT SETUP

**Status: COMPLETE**

Purpose:

Establish the GARUDA project structure and development environment.

Major outcomes:

- repository structure;
- Python environment;
- source package structure;
- configuration foundation;
- Git workflow;
- testing foundation.

---

## MODULE 2 — MARKET DATA ENGINE

**Status: COMPLETE**

Purpose:

Acquire, standardize, validate, store, and reload market data.

Major capabilities include:

- historical data retrieval;
- standardized OHLCV structure;
- data validation;
- data storage;
- data reload;
- data-integrity verification.

Important source area:

```text
src/data/
```

Known files include:

```text
data_loader.py
data_storage.py
data_validator.py
historical_data.py
instrument_resolver.py
```

---

## MODULE 3 — BROKER INTEGRATION

**Status: COMPLETE**

Purpose:

Connect GARUDA to Zerodha Kite Connect.

Important source area:

```text
src/broker/
```

Known files:

```text
auth.py
kite_client.py
session_manager.py
```

Capabilities verified:

- Kite client creation;
- login URL generation;
- request-token exchange;
- access-token storage;
- authenticated-session recreation;
- authentication verification;
- connected-user profile verification.

Current authentication flow:

```text
Create Kite Client
        ↓
Generate Login URL
        ↓
User Logs In
        ↓
Receive request_token
        ↓
Generate Access Token
        ↓
Save Token
        ↓
Create Authenticated Session
        ↓
Verify User Profile
```

A successful session has been demonstrated with the connected user:

**Thirupathi Omkari**

---

## MODULE 4 — DATA STORAGE AND VALIDATION

**Status: COMPLETE**

Purpose:

Ensure market data is reliable before it enters downstream GARUDA components.

Capabilities include:

- validation;
- standardization;
- storage;
- reload;
- data-integrity comparison;
- real market data pipeline verification.

---

## MODULE 5 — MARKET SCANNER

**Status: COMPLETE**

Purpose:

Analyze a market universe and rank/select candidate instruments.

Important source area:

```text
src/scanner/
```

Known files:

```text
activity_filter.py
activity_metrics.py
candidate_ranker.py
market_universe.py
scanner_engine.py
```

Verified components include:

- activity metrics;
- multi-stock metrics;
- candidate ranking;
- scanner engine.

---

## MODULE 6 — STRATEGY FRAMEWORK

**Status: COMPLETE**

Purpose:

Provide reusable strategy architecture.

Important source area:

```text
src/strategy/
```

Known files:

```text
base_strategy.py
orb_strategy.py
orb_vwap_strategy.py
session_utils.py
strategy_engine.py
strategy_result.py
```

Indicator source:

```text
src/indicators/vwap.py
```

Current primary strategy:

**ORB + VWAP**

Current strategy behavior:

```text
Market Data
        ↓
Select Relevant Trading Session
        ↓
Calculate Opening Range
        ↓
Calculate VWAP
        ↓
Evaluate Latest Candle
        ↓
BUY / SELL / NO_SIGNAL
        ↓
StrategyResult
```

The strategy has been successfully executed using real Kite INFY market data.

Verified real-market example:

```text
Symbol: INFY
Strategy: ORB_VWAP
Signal: SELL
Entry Price: 1068.70

Opening High: 1091.30
Opening Low: 1069.20
Latest Close: 1068.70
Latest VWAP: 1071.58

SELL Breakdown: True
SELL VWAP Confirmation: True
```

---

## MODULE 7 — BACKTESTING ENGINE

**Status: COMPLETE**

Purpose:

Replay historical market data and evaluate GARUDA strategies and trades.

Important source area:

```text
src/backtesting/
```

Known files:

```text
backtest_trade.py
candle_replay.py
entry_simulator.py
exit_rules.py
exit_simulator.py
multi_session_risk_backtester.py
performance_metrics.py
pnl_calculator.py
pre_execution_risk_backtester.py
risk_aware_backtester.py
session_backtester.py
session_iterator.py
session_preparer.py
signal_generator.py
slippage.py
trade_ledger.py
trade_lifecycle.py
transaction_costs.py
```

Major capabilities include:

- candle replay;
- historical signal generation;
- trade entry simulation;
- exit simulation;
- stop-loss evaluation;
- target evaluation;
- end-of-day exits;
- slippage;
- transaction costs;
- P&L;
- trade ledger;
- performance metrics;
- single-session backtesting;
- multi-session backtesting.

### Existing Exit Rules

GARUDA contains reusable exit-level logic.

Conceptually:

For BUY:

```text
Stop Loss = Entry below market
Target    = Entry above market
```

For SELL:

```text
Stop Loss = Entry above market
Target    = Entry below market
```

Current percentage defaults used in demos:

```text
Stop Loss = 1%
Target    = 2%
```

This represents a 1:2 risk/reward relationship when percentage-based exit levels are used.

### Existing Candle Exit Evaluation

GARUDA already evaluates whether a candle hits:

- STOP_LOSS;
- TARGET.

For BUY trades:

- candle low is checked against stop loss;
- candle high is checked against target.

For SELL trades:

- candle high is checked against stop loss;
- candle low is checked against target.

If neither is hit during historical simulation, the position may close at end of day according to existing backtesting logic.

---

## MODULE 8 — RISK AND POSITION SIZING

**Status: COMPLETE**

Purpose:

Protect trading capital and control position sizing before order execution.

Important source area:

```text
src/risk/
```

Known files:

```text
account.py
daily_loss_control.py
equity_curve.py
exposure_control.py
portfolio_risk_control.py
position_limit_control.py
position_sizer.py
quantity_rules.py
risk_calculator.py
risk_config.py
risk_manager.py
```

Major capabilities include:

- TradingAccount;
- RiskConfig;
- risk-per-trade calculation;
- position sizing;
- quantity rules;
- maximum exposure control;
- maximum portfolio-risk control;
- maximum open-position control;
- daily-loss control;
- equity curve;
- centralized RiskManager.

Known default RiskConfig values:

```text
risk_per_trade_pct          = 1.0
max_daily_loss_pct          = 3.0
max_portfolio_exposure_pct  = 50.0
max_portfolio_risk_pct      = 5.0
max_open_positions          = 5
```

### Important Risk Design Decision

GARUDA must not bypass the RiskManager merely to make a paper trade execute.

A verified real-market example:

```text
Capital: ₹100,000
Risk Amount: ₹1,000
INFY SELL Entry: ₹1068.70
Stop Loss: ₹1079.39
Raw Position Size: 93
Proposed Exposure: ₹99,389.10
Maximum Allowed Exposure: 50%
Decision: MAX_PORTFOLIO_EXPOSURE
```

The trade was correctly rejected.

This was considered successful integration behavior, not an error.

A possible future enhancement is:

```text
Risk-Based Quantity
        ↓
Apply Exposure Cap
        ↓
Resize Quantity
        ↓
Final Approved Quantity
```

However, this enhancement must be designed and tested separately.

Do not silently implement it inside a live runner.

---

## MODULE 9 — PAPER TRADING ENGINE

**Status: IN PROGRESS**

Module 9 is the current development module.

Purpose:

Execute GARUDA signals using:

- real or simulated market data;
- existing strategy logic;
- existing risk controls;
- simulated broker execution;
- virtual positions;
- virtual account capital.

No real broker orders are sent.

Important source area:

```text
src/execution/
```

Known Module 9 files include:

```text
paper_account.py
paper_order.py
paper_order_manager.py
paper_position.py
paper_position_manager.py
paper_trading_demo.py
paper_trading_session.py
risk_managed_paper_executor.py
simulated_broker.py
live_market_data_demo.py
live_strategy_demo.py
live_paper_execution_demo.py
live_paper_trading_runner.py
```

Some Module 9 files may still be untracked in Git at the current checkpoint and must be reviewed before the next commit.

---

# 6. MODULE 9 DEVELOPMENT HISTORY

## Part 1 — Paper Account

Implemented and tested:

- account creation;
- positive-capital validation;
- profit recording;
- loss recording;
- multiple trade results.

---

## Part 2 — Paper Order

Implemented and tested:

- BUY market orders;
- SELL market/limit behavior as supported;
- input normalization;
- validation;
- order lifecycle.

Order states include concepts such as:

- PENDING;
- SUBMITTED;
- FILLED;
- REJECTED;
- CANCELLED.

---

## Part 3 — Paper Position

Implemented and tested:

- LONG positions;
- SHORT positions;
- market-price updates;
- unrealized P&L;
- market value;
- validation.

---

## Part 4 — Paper Order Manager

Implemented and tested:

- order creation;
- sequential unique IDs;
- order lookup;
- submission;
- rejection;
- cancellation;
- order storage.

Example order ID:

```text
GARUDA-000001
```

---

## Part 5 — Simulated Broker

Implemented and tested.

Purpose:

Simulate broker execution without sending real orders.

Capabilities include:

- execute submitted market orders;
- fill BUY orders;
- fill SELL orders;
- validate market price;
- prevent repeated fills;
- update order state.

---

## Part 6 — Paper Position Manager

Implemented and tested.

Capabilities include:

- open LONG positions from filled BUY orders;
- open SHORT positions from filled SELL orders;
- retrieve positions;
- update market price;
- calculate total unrealized P&L;
- preserve position creation order;
- prevent invalid duplicate positions.

---

## Part 7 — Risk-Managed Paper Executor

Implemented and tested.

Purpose:

Connect Module 8 risk management with Module 9 paper execution.

Conceptual flow:

```text
Trade Proposal
        ↓
RiskManager
        ↓
REJECTED ─────→ No Order
        ↓
APPROVED
        ↓
PaperOrderManager
        ↓
Submit Order
        ↓
SimulatedBroker
        ↓
Fill Order
        ↓
PaperPositionManager
        ↓
Virtual Position
```

Important rule:

Risk evaluation happens before order creation.

---

## Part 8+ — Paper Trading Session and Exit Integration

Implemented and tested.

GARUDA demonstrated:

```text
Strategy Signal
        ↓
Risk Evaluation
        ↓
Paper Order
        ↓
Virtual Position
        ↓
Market Price Updates
        ↓
Unrealized P&L
        ↓
Exit
        ↓
Realized P&L
        ↓
Account Update
        ↓
Equity Update
```

An early demo manually exited a trade at +₹10 even though the configured SL/target relationship implied a different target.

This exposed an integration issue:

> Existing exit rules must be reused instead of manually choosing demo exits.

The issue was corrected by integrating existing:

```text
calculate_exit_levels()
evaluate_trade_candle()
```

This is an important architectural precedent.

---

# 7. REAL KITE MARKET DATA INTEGRATION

GARUDA has successfully connected to Kite and retrieved real market data.

Verified example:

```text
Symbol: INFY
Exchange: NSE
Instrument Token: 408065

Candles Available: 225
Latest Candle Time: 2026-07-10 15:25:00+05:30

Open: 1068.60
High: 1069.10
Low: 1067.10
Close: 1068.70
Volume: 247033
```

Verified flow:

```text
Authenticated Kite Session
        ↓
Instrument Resolution
        ↓
Historical / Intraday Data Request
        ↓
GARUDA Standard DataFrame
        ↓
Latest Market Data
```

---

# 8. REAL STRATEGY INTEGRATION

GARUDA successfully executed the existing ORB+VWAP strategy using real Kite market data.

Verified flow:

```text
Authenticated Kite Session
        ↓
Real INFY Data
        ↓
GARUDA Standard DataFrame
        ↓
Existing ORB+VWAP Strategy
        ↓
StrategyResult
        ↓
Visible Diagnostics
```

Verified output:

```text
Signal: SELL
Entry Price: 1068.70

Opening High: 1091.30
Opening Low: 1069.20
Latest Close: 1068.70
Latest VWAP: 1071.58

SELL Breakdown: True
SELL VWAP Confirmation: True
```

---

# 9. REAL STRATEGY → RISK → PAPER EXECUTION INTEGRATION

GARUDA successfully connected:

```text
Real Kite Data
        ↓
Existing ORB+VWAP
        ↓
StrategyResult
        ↓
Existing Exit Rules
        ↓
Existing RiskManager
        ↓
Existing Position Sizing
        ↓
Paper Execution Decision
```

The real INFY trade was rejected due to maximum portfolio exposure.

Verified output:

```text
Signal: SELL
Entry: 1068.70
Stop Loss: 1079.39
Target: 1047.33

Risk Amount: 1000.00
Raw Position Size: 93
Approved Quantity: 93
Proposed Exposure: 99,389.10

Decision: MAX_PORTFOLIO_EXPOSURE
Action: PAPER TRADE REJECTED
```

This verified that the real-data-to-risk pipeline works correctly.

---

# 10. LIVE PAPER TRADING RUNNER

The latest completed development component is:

```text
src/execution/live_paper_trading_runner.py
```

Focused tests:

```text
tests/test_live_paper_trading_runner.py
```

The runner control layer currently handles:

- multi-symbol registration;
- per-symbol runtime state;
- runner start;
- runner stop;
- market-session timing;
- new-entry cutoff timing;
- new-candle detection;
- duplicate-candle prevention;
- signal counting;
- duplicate-entry prevention;
- open-position state;
- trade rejection counting;
- trade execution counting;
- position-close tracking;
- multi-symbol runtime summary;
- visible runner summary.

The focused runner test result is:

**18 passed**

After integration, the full GARUDA regression result is:

**245 passed**

---

# 11. CURRENT AUTHORITATIVE TEST CHECKPOINT

The current clean development checkpoint is:

```text
245 PASSED
```

This checkpoint was reached after:

```text
227 existing tests
+
18 live paper trading runner tests
=
245 tests
```

Before further major development:

```powershell
$env:PYTHONPATH="src"; pytest -q
```

should continue to pass.

---

# 12. PYTHONPATH DEVELOPMENT NOTE

The GARUDA source directory uses a `src` layout.

Some test executions require:

```powershell
$env:PYTHONPATH="src"
```

Example:

```powershell
$env:PYTHONPATH="src"; pytest tests/test_live_paper_trading_runner.py -v
```

Without this environment setting, errors such as:

```text
ModuleNotFoundError: No module named 'execution'
```

may occur.

This is an environment/import-path issue and should not automatically be treated as a GARUDA business-logic failure.

---

# 13. CURRENT FIVE-SYMBOL INITIAL LIVE PAPER UNIVERSE

For the first controlled live paper-trading session, the recommended symbol universe is:

```text
INFY
TCS
RELIANCE
HDFCBANK
ICICIBANK
```

Purpose:

- keep the first live run manageable;
- use liquid NSE stocks;
- observe multi-symbol behavior;
- validate market-data polling;
- validate strategy evaluation;
- validate risk rejection/approval;
- validate position monitoring;
- validate runtime stability.

Do not immediately expand to the full NIFTY 50 universe before the controlled runner is stable.

---

# 14. CURRENT TARGET LIVE PAPER FLOW

The intended current live paper trading architecture is:

```text
START GARUDA
        ↓
Authenticate Kite
        ↓
Resolve Instruments
        ↓
Register Symbols
        ↓
Wait for Market Session
        ↓
Fetch Latest 5-Minute Candles
        ↓
Detect NEW Candle
        ↓
Ignore Already Processed Candle
        ↓
Run Existing ORB+VWAP
        ↓
NO_SIGNAL ───────────────→ Continue
        ↓
BUY / SELL
        ↓
Prevent Duplicate Entry
        ↓
Check Entry Cutoff Time
        ↓
Calculate Existing SL/Target
        ↓
Run Existing RiskManager
        ↓
REJECTED
        ├── Log Reason
        └── Continue
        ↓
APPROVED
        ↓
Create Paper Order
        ↓
Submit Order
        ↓
Simulated Fill
        ↓
Open Virtual Position
        ↓
Receive New Candles
        ↓
Update Position Price
        ↓
Update Unrealized P&L
        ↓
Evaluate Existing SL/Target Logic
        ↓
NO EXIT ─────────────────→ Continue
        ↓
STOP LOSS / TARGET
        ↓
Close Virtual Position
        ↓
Calculate Realized P&L
        ↓
Update Virtual Capital
        ↓
Update Equity Curve
        ↓
Update Runner State
        ↓
Continue Until Market Close
        ↓
Display Session Summary
        ↓
STOP GARUDA
```

---

# 15. NEXT DEVELOPMENT STEP

The exact next development step is:

# MODULE 9 PART 13F-1

## Single-Cycle Live Paper Trading Orchestration Engine

Do not immediately create one huge continuous polling loop.

First build a tested orchestration component that processes one symbol through one new-candle cycle.

The intended single-cycle flow is:

```text
Receive Symbol
        ↓
Receive Market DataFrame
        ↓
Check Latest Candle
        ↓
Is New Candle?
        ├── NO → SKIPPED_DUPLICATE_CANDLE
        ↓ YES
Mark Candle Processed
        ↓
Is Position Already Open?
        ├── YES → MONITOR POSITION
        │           ↓
        │      Update Market Price
        │           ↓
        │      Evaluate SL/Target
        │           ↓
        │      HOLD or EXIT
        ↓ NO
Check New-Entry Time
        ├── BLOCKED → NO_NEW_ENTRY
        ↓ ALLOWED
Run Existing ORB+VWAP
        ↓
NO_SIGNAL → NO_ACTION
        ↓
BUY / SELL
        ↓
Record Signal
        ↓
Check Duplicate Entry
        ↓
Calculate Existing Exit Levels
        ↓
Run Existing Risk-Managed Paper Executor
        ↓
REJECTED
        ├── Record Rejection
        └── Return Result
        ↓
EXECUTED
        ├── Record Execution
        └── Return Result
```

Part 13F-1 should be independently tested before creating the continuous live polling loop.

---

# 16. WHY SINGLE-CYCLE ORCHESTRATION COMES BEFORE CONTINUOUS POLLING

A large continuous runner that directly mixes:

- Kite API calls;
- market timing;
- strategy;
- risk;
- order management;
- position management;
- exit logic;
- P&L;
- logging;
- sleep intervals;

would be difficult to test and debug.

The preferred architecture is:

```text
CONTINUOUS OUTER LOOP
        ↓
FETCH DATA
        ↓
CALL TESTED SINGLE-CYCLE ENGINE
        ↓
RECEIVE RESULT
        ↓
DISPLAY / LOG
        ↓
WAIT
        ↓
REPEAT
```

This keeps the outer live loop thin.

---

# 17. KNOWN ISSUES AND FUTURE IMPROVEMENTS

## 17.1 Risk Quantity vs Exposure Limit

Current behavior:

```text
Calculate Risk-Based Quantity
        ↓
Calculate Exposure
        ↓
Reject if Exposure Too High
```

Possible future behavior:

```text
Calculate Risk-Based Quantity
        ↓
Calculate Exposure-Limited Quantity
        ↓
Choose Lower Valid Quantity
        ↓
Approve Resized Trade
```

This requires explicit design and testing.

Do not silently alter Module 8 during Module 9 integration.

---

## 17.2 Persistent Runtime State

Current live runner state is primarily in memory.

Future enhancement may require persistence for:

- open paper positions;
- processed candles;
- orders;
- daily realized P&L;
- virtual capital;
- equity curve;
- session restart recovery.

---

## 17.3 Logging

Current development emphasizes visible terminal output.

Future GARUDA should add structured logging for:

- startup;
- authentication;
- data retrieval;
- strategy decisions;
- risk decisions;
- orders;
- fills;
- positions;
- exits;
- errors;
- session summaries.

---

## 17.4 Market Data Architecture

Current development uses Kite market data.

Future architecture should allow data-provider abstraction where practical.

This is particularly relevant for future cryptocurrency support.

---

## 17.5 Broker Architecture

Current broker integration is Kite-based.

Future F&O and multi-market expansion should avoid unnecessary coupling between strategy logic and Kite-specific APIs.

---

# 18. FUTURE SCALING VISION

GARUDA should evolve progressively.

Current direction:

```text
NSE EQUITY RESEARCH
        ↓
REAL MARKET DATA
        ↓
STRATEGY VALIDATION
        ↓
BACKTESTING
        ↓
RISK MANAGEMENT
        ↓
PAPER TRADING
        ↓
LIVE PAPER VALIDATION
        ↓
REPORTING / ALERTS
        ↓
CLOUD DEPLOYMENT
        ↓
BROADER EQUITY COVERAGE
        ↓
F&O SUPPORT
        ↓
CRYPTO SUPPORT
        ↓
MULTI-ASSET RESEARCH
        ↓
VALIDATED AUTOMATED EXECUTION
```

The system should eventually support:

- larger instrument universes;
- market scanners;
- multiple strategies;
- strategy comparison;
- portfolio-level risk;
- instrument-specific quantity rules;
- derivatives;
- lot-size handling;
- margin-aware risk;
- options-specific logic;
- futures-specific logic;
- cryptocurrency markets;
- 24/7 market sessions;
- cloud execution;
- automated reports;
- alerts;
- eventual real-order routing.

---

# 19. DEVELOPMENT WORKFLOW

Preferred workflow:

```text
Understand Requirement
        ↓
Check Master Context
        ↓
Inspect Relevant Existing Components
        ↓
Reuse Existing Logic
        ↓
Design Focused Component
        ↓
Write Complete File
        ↓
Write Focused Tests
        ↓
Run Focused Tests
        ↓
Fix Errors
        ↓
Run Full Regression
        ↓
Demonstrate Visible Output
        ↓
Update Documentation
        ↓
Git Commit
```

---

# 20. GIT CHECKPOINT REQUIREMENT

At the time this Master Context was created, the repository snapshot indicated that some newer Module 9 files may not yet have been committed.

Before proceeding too far into Part 13F, inspect:

```powershell
git status
```

After confirming:

- intended Module 9 source files;
- intended Module 9 tests;
- documentation;
- no temporary files;
- no secrets;
- no access tokens;

create a clean Git checkpoint.

Never commit:

- `.env`;
- Kite API secrets;
- Kite access tokens;
- sensitive credentials.

---

# 21. NEW CHAT CONTINUITY INSTRUCTIONS

When starting a new ChatGPT conversation:

1. Upload the latest `GARUDA_MASTER_CONTEXT.md`.
2. If detailed repository inspection is necessary, also upload the latest `garuda_repository_snapshot.txt`.
3. Tell ChatGPT to read the Master Context before recommending architecture or writing code.
4. Continue from the `NEXT DEVELOPMENT STEP`.
5. Do not reconstruct completed Modules 1–9 from memory.
6. Update this Master Context after major checkpoints.

Recommended opening message:

> I am continuing development of GARUDA Quant Lab. Read the attached GARUDA_MASTER_CONTEXT.md before making recommendations or writing code. Treat it as the project continuity document, while treating current repository code and tests as the final technical authority. Preserve the existing architecture and continue from the documented NEXT DEVELOPMENT STEP. Provide complete files when code changes are needed, reuse existing GARUDA components, protect the passing-test checkpoint, and keep future equities, F&O, and crypto scaling in mind.

---

# 22. CURRENT CHECKPOINT SUMMARY

```text
PROJECT
GARUDA Quant Lab

CURRENT MODULE
Module 9 — Paper Trading Engine

COMPLETED FOUNDATION
Modules 1–8

CURRENT TEST CHECKPOINT
245 PASSED

REAL KITE AUTHENTICATION
WORKING

REAL KITE MARKET DATA
WORKING

REAL ORB+VWAP STRATEGY
WORKING

REAL STRATEGY → RISK INTEGRATION
WORKING

PAPER ORDERS
WORKING

SIMULATED BROKER
WORKING

VIRTUAL POSITIONS
WORKING

SL/TARGET INTEGRATION
WORKING

MULTI-SYMBOL RUNNER STATE
WORKING

NEW-CANDLE DETECTION
WORKING

DUPLICATE-ENTRY PREVENTION
WORKING

MARKET-TIME CONTROLS
WORKING

CURRENT INITIAL SYMBOL UNIVERSE
INFY
TCS
RELIANCE
HDFCBANK
ICICIBANK

NEXT DEVELOPMENT STEP
Module 9 Part 13F-1

NEXT COMPONENT
Single-Cycle Live Paper Trading Orchestration Engine

CURRENT PRIORITY
Preserve GARUDA architecture first.
Progress toward stable live paper trading second.

LONG-TERM SCALING
Equities → F&O → Crypto

AGREED PHASE ORDER
Phase 1 → Phase 3 → Phases 2 and 4 simultaneously
```

---

# 23. FINAL CONTINUITY RULE

The purpose of this document is to prevent future GARUDA conversations from repeatedly reconstructing the project.

Future development should begin with:

```text
READ MASTER CONTEXT
        ↓
VERIFY CURRENT GIT / TEST CHECKPOINT
        ↓
IDENTIFY NEXT DEVELOPMENT STEP
        ↓
INSPECT ONLY RELEVANT SOURCE INTERFACES
        ↓
CONTINUE DEVELOPMENT
```

Do not restart GARUDA planning from Module 1.

Do not redesign completed architecture merely because a new conversation lacks previous chat history.

Continue from the documented checkpoint and allow the repository code and passing tests to remain the final technical authority.

---

# 24. AUTHORITATIVE CHECKPOINT UPDATE — 2026-07-14

This section supersedes outdated checkpoint, test-count, current-development-step, and Module 9 status information appearing earlier in this document.

When information in earlier sections conflicts with this section, this section is authoritative.

Repository source code and passing tests remain the final technical authority.

---

# 25. CURRENT GIT CHECKPOINT

The current verified Git checkpoint is:

```text
ffde7d6
```

Commit message:

```text
Complete Module 9 multi-symbol polling and stale market data protection
```

Recent Git history:

```text
ffde7d6 Complete Module 9 multi-symbol polling and stale market data protection

4347807 Complete Module 9 single-cycle paper trading orchestration

fe47358 Complete Module 9 paper trading foundation and live runner controls

d2469b9 Complete Module 8 risk management and position sizing

1e137e5 Complete Module 7 backtesting engine and pytest migration
```

The branch is:

```text
main
```

The local branch and `origin/main` are synchronized at checkpoint:

```text
ffde7d6
```

Two temporary repository-inspection files remain untracked:

```text
garuda_part_13f2_dependencies.txt
garuda_part_13f2_interfaces.txt
```

These files are development snapshots and are not part of the authoritative GARUDA source code.

---

# 26. CURRENT AUTHORITATIVE TEST CHECKPOINT

The current full GARUDA regression checkpoint is:

```text
284 PASSED
```

Focused multi-symbol polling tests:

```text
26 PASSED
```

The progression to the current checkpoint was:

```text
245 passed
    ↓
Single-Cycle Paper Trading Orchestration
    ↓
258 passed
    ↓
Additional Module 9 Development
    ↓
274 passed
    ↓
276 passed
    ↓
Kite Market-Data Interface Regression Test
    ↓
277 passed
    ↓
Stale Market Data Protection Tests
    ↓
284 passed
```

Before continuing major development, the following command should remain successful:

```powershell
$env:PYTHONPATH="src"
pytest -q
```

Expected result:

```text
284 passed
```

Do not knowingly continue major GARUDA development with failing regression tests.

---

# 27. MODULE 9 CURRENT STATUS

Module 9 — Paper Trading Engine has progressed significantly beyond the earlier checkpoint documented in this file.

Current status:

```text
MODULE 9 — ADVANCED DEVELOPMENT
```

Completed Module 9 capabilities include:

- paper account;
- paper orders;
- paper order management;
- simulated broker execution;
- paper positions;
- paper position management;
- risk-managed paper execution;
- paper trading sessions;
- automatic stop-loss and target handling;
- account-equity integration;
- live Kite market-data adapter;
- live market-data demonstration;
- real ORB+VWAP strategy demonstration;
- real strategy-to-risk integration;
- live paper execution demonstration;
- live paper trading runner;
- single-cycle paper trading orchestration;
- finite multi-symbol polling;
- real Kite multi-symbol market-data retrieval;
- portfolio-state integration;
- current-price exposure calculation;
- stale-market-data protection.

No real broker orders are currently sent.

GARUDA remains in controlled paper-trading development.

---

# 28. MODULE 9 PART 13F-1 — COMPLETED

## Single-Cycle Paper Trading Orchestration

Status:

```text
COMPLETE
```

Git checkpoint:

```text
4347807
```

Commit:

```text
Complete Module 9 single-cycle paper trading orchestration
```

The completed single-cycle orchestration architecture connects existing GARUDA components without duplicating their responsibilities.

Verified conceptual flow:

```text
Receive Symbol
    ↓
Receive Market DataFrame
    ↓
Check Latest Candle
    ↓
Detect Duplicate Candle
    ↓
Determine Open Position State
    ↓
NO OPEN POSITION
    ↓
Check Entry Time
    ↓
Run Existing Strategy
    ↓
NO SIGNAL → RETURN
    ↓
BUY / SELL SIGNAL
    ↓
Calculate Existing Exit Levels
    ↓
Run Existing Risk Manager
    ↓
REJECTED → RECORD AND RETURN
    ↓
APPROVED
    ↓
Create Paper Order
    ↓
Simulated Fill
    ↓
Open Virtual Position
```

For an already open position:

```text
Receive New Candle
    ↓
Update Market Price
    ↓
Calculate Unrealized P&L
    ↓
Evaluate Existing Exit Rules
    ↓
NO EXIT → HOLD
    ↓
STOP LOSS / TARGET
    ↓
Close Position
    ↓
Calculate Realized P&L
    ↓
Update Paper Account
    ↓
Update Runner State
```

A deterministic demonstration successfully verified:

```text
Cycle 1
BUY signal
    ↓
Risk approval
    ↓
Paper order
    ↓
Position opened

Cycle 2
New market candle
    ↓
Position monitored
    ↓
Unrealized profit
    ↓
Position held

Cycle 3
Target reached
    ↓
Automatic exit
    ↓
Realized profit
    ↓
Account updated
```

Verified demonstration result:

```text
Initial Capital : 100,000.00
Final Capital   : 102,000.00
Net P&L         : 2,000.00
Return          : 2.00%
Orders Created  : 1
Open Positions  : 0
Closed Trades   : 1
```

This verified the complete controlled single-cycle orchestration path.

---

# 29. MODULE 9 PART 13F-2 — COMPLETED

## Finite Real Kite Multi-Symbol Polling

Status:

```text
COMPLETE
```

Git checkpoint:

```text
ffde7d6
```

Primary files:

```text
src/execution/live_multi_symbol_polling.py
src/execution/live_multi_symbol_polling_demo.py
tests/test_live_multi_symbol_polling.py
```

The polling engine was intentionally implemented as a finite polling engine rather than an uncontrolled infinite loop.

Current architecture:

```text
Registered Symbols
    ↓
Fetch Real Intraday Market Data
    ↓
Validate Market Data
    ↓
Validate Market Data Freshness
    ↓
Calculate Current Portfolio State
    ↓
Call Existing LivePaperTradingRunner
    ↓
Call Existing PaperTradingSessionEngine
    ↓
Collect Symbol Result
    ↓
Continue Through Registered Symbols
    ↓
Complete Polling Cycle
    ↓
Optional Wait
    ↓
Next Finite Cycle
```

The polling engine does not duplicate:

- strategy logic;
- risk logic;
- order logic;
- position logic;
- stop-loss logic;
- target logic;
- realized P&L logic.

Those responsibilities remain in existing GARUDA components.

---

# 30. REAL KITE MARKET-DATA INTERFACE CORRECTION

During real multi-symbol polling integration, the following interface mismatch was discovered.

The polling engine initially attempted:

```text
lookback_days
```

as an argument to:

```text
fetch_live_intraday_data()
```

However, the actual market-data adapter interface is:

```python
fetch_live_intraday_data(
    kite,
    instrument_token,
    from_date,
    to_date,
    interval="5minute",
)
```

The polling engine was corrected to dynamically calculate:

```text
to_date = current datetime

from_date = to_date - configured lookback days
```

and call the existing adapter using:

```text
kite
instrument_token
from_date
to_date
interval
```

A dedicated regression test was added to verify that the polling engine supplies the correct date-range interface.

This correction increased the focused polling test count from:

```text
18 passed
```

to:

```text
19 passed
```

and the full regression checkpoint to:

```text
277 passed
```

Architectural lesson:

> New GARUDA components must conform to actual existing source interfaces rather than assumed interfaces.

---

# 31. PORTFOLIO STATE INTEGRATION

The multi-symbol polling engine calculates the current GARUDA portfolio state before passing a fresh market candle to the existing orchestration layer.

Current portfolio-state values include:

```text
current_exposure
current_open_risk
current_open_positions
daily_realized_pnl
```

Current exposure is calculated using:

```text
position quantity × current market price
```

rather than entry price.

This allows portfolio exposure to reflect the latest known value of open positions.

Current open risk uses active exit levels and position direction.

For LONG positions:

```text
(entry price - stop loss) × quantity
```

For SHORT positions:

```text
(stop loss - entry price) × quantity
```

The existing RiskManager remains authoritative for trade approval and rejection.

---

# 32. STALE MARKET DATA PROTECTION

## Part 13F-2C

Status:

```text
COMPLETE
```

During the first successful real Kite multi-symbol polling demonstration, GARUDA fetched old Friday candles while running outside the active trading date.

The existing entry-time protection prevented trades because the latest candles were timestamped at 15:25.

However, this exposed an architectural risk:

> GARUDA should not allow an old trading-day candle to reach strategy, risk, or paper execution merely because its intraday time happens to satisfy another validation rule.

Stale-market-data protection was therefore added to the polling layer.

Current flow:

```text
Fetch Market Data
    ↓
DataFrame Missing?
    ├── YES → NO_MARKET_DATA
    ↓ NO
DataFrame Empty?
    ├── YES → NO_MARKET_DATA
    ↓ NO
Get Latest Candle Time
    ↓
Compare Candle Date With Current Date
    ↓
OLDER DATE?
    ├── YES → STALE_MARKET_DATA
    ↓ NO
Calculate Portfolio State
    ↓
Call Existing Runner
```

Important architectural rule:

```text
STALE MARKET DATA
    ↓
BLOCKED BY POLLING ENGINE
    ↓
DO NOT CALL process_symbol_cycle()
    ↓
DO NOT RUN STRATEGY
    ↓
DO NOT RUN RISK MANAGER
    ↓
DO NOT CREATE ORDER
    ↓
DO NOT ALTER POSITION
    ↓
DO NOT ALTER ACCOUNT
```

The current-time dependency is injectable.

This allows deterministic testing rather than relying on the computer's actual clock.

Timezone handling supports:

- timezone-naive test timestamps;
- timezone-aware Kite timestamps;
- conversion between current-time and candle-time timezones.

Focused stale-data tests verify:

- current-date data is not stale;
- previous-date data is stale;
- timezone-aware current-date data is accepted;
- timezone-aware previous-date data is rejected;
- timezone conversion correctly detects stale dates;
- stale data never reaches the runner;
- stale data cannot create an order, position, or account change.

After these tests were added and existing tests were made deterministic:

```text
26 focused tests passed
```

Full regression:

```text
284 passed
```

---

# 33. REAL KITE FIVE-SYMBOL POLLING VERIFICATION

The controlled real Kite multi-symbol demonstration has been successfully executed.

Current initial universe:

```text
INFY
TCS
RELIANCE
HDFCBANK
ICICIBANK
```

Verified symbol resolution:

```text
INFY       → 408065
TCS        → 2953217
RELIANCE   → 738561
HDFCBANK   → 341249
ICICIBANK  → 1270529
```

Verified polling result:

```text
Requested Symbols  : 5
Registered Symbols : 5
Failed Symbols     : 0

Requested Cycles   : 1
Completed Cycles   : 1

Total Symbol Polls : 5
Successful Polls   : 5
Failed Polls       : 0
```

The latest verified real-market demonstration used current-date candles:

```text
2026-07-14 15:25:00+05:30
```

Therefore stale-data protection correctly allowed the candles to continue through the pipeline.

The existing runner then returned:

```text
ENTRY_TIME_CLOSED
```

for all five symbols because new entries were no longer permitted at 15:25.

Verified final state:

```text
Initial Capital     : 100,000.00
Current Capital     : 100,000.00
Net Realized P&L    : 0.00

Current Exposure    : 0.00
Current Open Risk   : 0.00
Open Positions      : 0

Orders Created      : 0
Positions Open      : 0

Processed Candles   : 5
Generated Signals   : 0
Executed Trades     : 0
Rejected Trades     : 0
Closed Trades       : 0
```

This is correct behavior.

Verified flow:

```text
REAL KITE DATA
    ↓
FRESHNESS CHECK
    ↓
CURRENT TRADING DATE
    ↓
PASS
    ↓
POLLING ENGINE
    ↓
EXISTING RUNNER
    ↓
ENTRY-TIME CHECK
    ↓
15:25 CANDLE
    ↓
ENTRY_TIME_CLOSED
    ↓
NO STRATEGY SIGNAL
    ↓
NO ORDER
    ↓
NO POSITION
```

---

# 34. KITE AUTHENTICATION WORKFLOW

Kite access tokens may expire or become invalid.

The current `auth.py` defines authentication functions but may not execute an interactive authentication flow when run directly.

Running:

```powershell
python src/broker/auth.py
```

may therefore produce no output.

Current manual authentication workflow:

Generate login URL:

```powershell
$env:PYTHONPATH="src"
python -c "from broker.auth import generate_login_url; generate_login_url()"
```

Open the generated URL and complete Kite login.

Copy only the actual `request_token` value from the redirected URL.

Do not share the request token in ChatGPT or commit it to Git.

Generate and save the access token:

```powershell
python -c "from broker.auth import generate_access_token; generate_access_token('ACTUAL_REQUEST_TOKEN')"
```

Verify session:

```powershell
python -c "from broker.session_manager import create_authenticated_session; create_authenticated_session()"
```

Expected successful status:

```text
GARUDA Broker Session: READY
```

Then run the required real Kite demonstration.

Future improvement:

Create a safe interactive authentication command that:

```text
Generate Login URL
    ↓
Display URL
    ↓
Ask User for Request Token
    ↓
Generate Access Token
    ↓
Save Access Token
    ↓
Verify Session
```

This is a usability enhancement and should not disrupt the current verified broker architecture.

---

# 35. CURRENT MODULE 9 ARCHITECTURE

The verified Module 9 development architecture is now:

```text
KITE AUTHENTICATION
    ↓
INSTRUMENT RESOLUTION
    ↓
REAL MARKET DATA
    ↓
GARUDA STANDARD DATAFRAME
    ↓
FINITE MULTI-SYMBOL POLLING ENGINE
    ↓
MARKET DATA AVAILABILITY CHECK
    ↓
STALE MARKET DATA CHECK
    ↓
CURRENT PORTFOLIO STATE
    ↓
LIVE PAPER TRADING RUNNER
    ↓
NEW-CANDLE DETECTION
    ↓
DUPLICATE-CANDLE PREVENTION
    ↓
OPEN POSITION?
    ├── YES
    │     ↓
    │   UPDATE MARKET PRICE
    │     ↓
    │   UNREALIZED P&L
    │     ↓
    │   EXISTING EXIT RULES
    │     ↓
    │   HOLD OR EXIT
    │
    ↓ NO
ENTRY-TIME CHECK
    ↓
EXISTING STRATEGY
    ↓
NO SIGNAL → CONTINUE
    ↓
BUY / SELL
    ↓
EXISTING EXIT-LEVEL CALCULATION
    ↓
EXISTING RISK MANAGER
    ↓
REJECTED → RECORD AND CONTINUE
    ↓
APPROVED
    ↓
PAPER ORDER
    ↓
SIMULATED BROKER
    ↓
VIRTUAL POSITION
    ↓
NEXT MARKET CANDLE
```

This architecture should be preserved.

---

# 36. CURRENT DEVELOPMENT PRINCIPLES

The following principles have been reinforced during Module 9 development.

## 36.1 Repository Code Is Final Technical Authority

The Master Context provides continuity.

However:

```text
CURRENT SOURCE CODE
+
CURRENT TESTS
+
CURRENT GIT CHECKPOINT
```

remain the final technical authority.

---

## 36.2 Do Not Guess Existing Interfaces

Before integrating a new component:

```text
Inspect Existing Function
    ↓
Confirm Parameters
    ↓
Confirm Return Type
    ↓
Confirm Existing Tests
    ↓
Write Integration
```

Do not design against an assumed interface.

---

## 36.3 Reuse Existing Components

Do not duplicate:

- strategy logic;
- VWAP logic;
- ORB logic;
- exit logic;
- risk logic;
- quantity logic;
- account logic;
- order logic;
- position logic;
- P&L logic.

Use existing tested components.

---

## 36.4 Keep Outer Polling Thin

The polling layer should coordinate.

It should not become a second strategy, risk, or execution engine.

Preferred architecture:

```text
POLL
    ↓
VALIDATE DATA
    ↓
CALCULATE REQUIRED STATE
    ↓
CALL TESTED ORCHESTRATION
    ↓
COLLECT RESULT
```

---

## 36.5 Prefer Deterministic Tests

Dependencies such as:

```text
current time
sleep
market-data fetcher
```

should be injectable where practical.

This prevents tests from depending unnecessarily on:

- real clock time;
- real sleeping;
- live broker data.

---

## 36.6 Protect the Regression Checkpoint

Current authoritative checkpoint:

```text
284 PASSED
```

Focused polling checkpoint:

```text
26 PASSED
```

Major changes should follow:

```text
WRITE COMPONENT
    ↓
RUN FOCUSED TESTS
    ↓
FIX FAILURES
    ↓
RUN FULL REGRESSION
    ↓
RUN VISIBLE DEMO WHEN APPROPRIATE
    ↓
CREATE GIT CHECKPOINT
    ↓
UPDATE MASTER CONTEXT
```

---

# 37. EXACT NEXT DEVELOPMENT STEP

Parts 13F-1 and 13F-2 are complete.

Do not restart them.

The next development step should continue progressing toward a controlled real-time paper-trading session.

Recommended next component:

```text
MODULE 9 PART 13F-3
```

## Controlled Multi-Cycle Live Paper Trading Session

Purpose:

Move from a one-cycle real Kite demonstration to a controlled multi-cycle session while preserving the tested architecture.

The next development should first inspect the current interfaces of:

```text
src/execution/live_multi_symbol_polling.py
src/execution/live_paper_trading_runner.py
src/execution/paper_trading_session.py
src/data/live_market_data.py
```

and the relevant tests.

Do not immediately create an infinite unattended trading process.

The preferred next progression is:

```text
CURRENT FINITE POLLING ENGINE
    ↓
CONTROLLED MULTI-CYCLE SESSION
    ↓
MARKET-SESSION START/STOP CONTROL
    ↓
SAFE POLLING INTERVAL
    ↓
NEW-CANDLE PROCESSING
    ↓
POSITION MONITORING ACROSS CYCLES
    ↓
VISIBLE SESSION SUMMARY
    ↓
ERROR ISOLATION
    ↓
GRACEFUL STOP
```

Potential Part 13F-3 requirements should include:

- configurable finite cycle count or controlled duration;
- safe polling interval;
- preservation of runner state across cycles;
- preservation of paper account state across cycles;
- preservation of open positions across cycles;
- duplicate-candle protection across cycles;
- stale-market-data protection;
- symbol-level failure isolation;
- clear cycle summaries;
- clear final session summary;
- no real orders;
- no infinite loop during initial development;
- deterministic focused tests;
- full regression protection.

Before writing Part 13F-3 code:

```text
READ THIS MASTER CONTEXT
    ↓
VERIFY GIT CHECKPOINT ffde7d6
    ↓
VERIFY 284 TESTS PASS
    ↓
INSPECT ONLY RELEVANT CURRENT INTERFACES
    ↓
DESIGN PART 13F-3
    ↓
WRITE COMPLETE FILES
```

---

# 38. UPDATED NEW-CHAT CONTINUITY INSTRUCTIONS

When starting a new ChatGPT conversation:

1. Upload the latest `GARUDA_MASTER_CONTEXT.md`.
2. Tell ChatGPT to read the complete Master Context before recommending architecture or writing code.
3. Treat repository source code and tests as the final technical authority.
4. Verify Git checkpoint `ffde7d6`.
5. Verify the documented regression checkpoint of `284 passed`.
6. Continue from `MODULE 9 PART 13F-3`.
7. Do not reconstruct Modules 1–9 from memory.
8. Do not restart Part 13F-1.
9. Do not restart Part 13F-2.
10. Inspect only source interfaces relevant to the next development task.
11. Provide complete files rather than fragmented patches when practical.
12. Preserve the existing architecture.
13. Protect the passing-test checkpoint.
14. Update this Master Context after the next major Git checkpoint.

Recommended new-chat opening message:

> I am continuing development of GARUDA Quant Lab. Read the attached GARUDA_MASTER_CONTEXT.md completely before making recommendations or writing code. Treat it as the project continuity document, while treating the current repository source code and tests as the final technical authority. The current verified Git checkpoint is ffde7d6, the full regression checkpoint is 284 passed, focused multi-symbol polling tests are 26 passed, and Module 9 Parts 13F-1 and 13F-2 are complete. Continue from the documented next development step, Module 9 Part 13F-3. Preserve the existing architecture, inspect actual source interfaces before integration, reuse existing GARUDA components, provide complete files when code changes are required, and protect the passing-test checkpoint.

---

# 39. UPDATED CURRENT CHECKPOINT SUMMARY

```text
PROJECT
GARUDA Quant Lab

CURRENT MODULE
Module 9 — Paper Trading Engine

COMPLETED FOUNDATION
Modules 1–8

MODULE 9 STATUS
Advanced Development

PART 13F-1
COMPLETE

PART 13F-2
COMPLETE

CURRENT GIT CHECKPOINT
ffde7d6

CURRENT FULL TEST CHECKPOINT
284 PASSED

FOCUSED MULTI-SYMBOL POLLING TESTS
26 PASSED

REAL KITE AUTHENTICATION
WORKING

REAL KITE MARKET DATA
WORKING

REAL ORB+VWAP STRATEGY
WORKING

REAL STRATEGY → RISK INTEGRATION
WORKING

PAPER ORDERS
WORKING

SIMULATED BROKER
WORKING

VIRTUAL POSITIONS
WORKING

SL/TARGET INTEGRATION
WORKING

SINGLE-CYCLE ORCHESTRATION
WORKING

MULTI-SYMBOL RUNNER STATE
WORKING

FINITE MULTI-SYMBOL POLLING
WORKING

REAL FIVE-SYMBOL POLLING
VERIFIED

NEW-CANDLE DETECTION
WORKING

DUPLICATE-CANDLE PREVENTION
WORKING

MARKET-TIME CONTROLS
WORKING

STALE-MARKET-DATA PROTECTION
WORKING

CURRENT INITIAL SYMBOL UNIVERSE
INFY
TCS
RELIANCE
HDFCBANK
ICICIBANK

NEXT DEVELOPMENT STEP
Module 9 Part 13F-3

NEXT COMPONENT
Controlled Multi-Cycle Live Paper Trading Session

CURRENT PRIORITY
Preserve verified GARUDA architecture.
Progress toward stable controlled live paper trading.

CURRENT DEVELOPMENT RULE
No real orders.

LONG-TERM SCALING
Equities → F&O → Crypto

FINAL TECHNICAL AUTHORITY
Current Repository Code + Current Tests
```

---

# 40. UPDATED FINAL CONTINUITY RULE

Future GARUDA development should begin with:

```text
READ LATEST MASTER CONTEXT
    ↓
VERIFY GIT CHECKPOINT
    ↓
VERIFY TEST CHECKPOINT
    ↓
IDENTIFY DOCUMENTED NEXT STEP
    ↓
INSPECT ONLY RELEVANT SOURCE INTERFACES
    ↓
REUSE EXISTING TESTED COMPONENTS
    ↓
WRITE FOCUSED COMPONENT
    ↓
RUN FOCUSED TESTS
    ↓
RUN FULL REGRESSION
    ↓
RUN VISIBLE DEMONSTRATION
    ↓
CREATE GIT CHECKPOINT
    ↓
UPDATE MASTER CONTEXT
```

Do not restart GARUDA planning from Module 1.

Do not redesign completed architecture merely because a new ChatGPT conversation lacks previous conversation history.

Do not assume interfaces from memory.

Do not bypass existing RiskManager behavior merely to force trade execution.

Do not send real broker orders during the current development stage.

Continue from the documented checkpoint.

Allow repository code and passing tests to remain the final technical authority.
