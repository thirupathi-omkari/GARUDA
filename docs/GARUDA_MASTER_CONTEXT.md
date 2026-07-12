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

**END OF GARUDA MASTER PROJECT CONTEXT**
