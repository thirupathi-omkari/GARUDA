from dataclasses import dataclass


# ============================================================
# CONTROLLED LIVE PAPER TRADING SESSION RESULT
# ============================================================


@dataclass
class ControlledLivePaperTradingSessionResult:
    """
    Final result returned after GARUDA completes
    one controlled multi-cycle live paper-trading session.
    """

    status: str

    started_at: object

    stopped_at: object

    requested_cycles: int

    completed_cycles: int

    polling_result: object

    runner_summary: dict

    portfolio_state: dict

    initial_capital: float

    current_capital: float

    net_realized_pnl: float


# ============================================================
# CONTROLLED LIVE PAPER TRADING SESSION
# ============================================================


class ControlledLivePaperTradingSession:
    """
    GARUDA controlled multi-cycle live paper-trading session.

    Responsibilities:

    Validate Session Request
        ↓
    Start Existing LivePaperTradingRunner
        ↓
    Run Existing LiveMultiSymbolPollingEngine
        ↓
    Preserve Existing GARUDA Runtime State
        ↓
    Stop Existing LivePaperTradingRunner
        ↓
    Collect Final Runner State
        ↓
    Collect Final Portfolio State
        ↓
    Collect Final Paper Account State
        ↓
    Return Controlled Session Result

    Important:

    This controller does NOT duplicate:

    Market Data Logic
    Strategy Logic
    Risk Logic
    Order Logic
    Position Logic
    Exit Logic
    P&L Logic
    Stale Market Data Protection
    Duplicate Candle Protection

    Those responsibilities remain inside GARUDA's
    existing tested components.
    """

    def __init__(
        self,
        polling_engine,
        current_time_provider=None,
    ):
        """
        Create the GARUDA controlled live
        paper-trading session controller.
        """

        if polling_engine is None:

            raise ValueError(
                "Polling engine is required."
            )

        self.polling_engine = polling_engine

        self.runner = polling_engine.runner

        self.session_engine = (
            polling_engine.session_engine
        )

        self.current_time_provider = (
            current_time_provider
        )


    # ========================================================
    # VALIDATION
    # ========================================================


    def _validate_requested_cycles(
        self,
        cycles,
    ):
        """
        Validate controlled session cycle count.

        The polling engine also validates cycles.

        This controller performs its own validation
        before changing runner lifecycle state.
        """

        if not isinstance(cycles, int):

            raise TypeError(
                "cycles must be an integer."
            )

        if cycles <= 0:

            raise ValueError(
                "cycles must be greater than zero."
            )


    # ========================================================
    # CURRENT TIME
    # ========================================================


    def _get_current_time(self):
        """
        Return current session time when an injectable
        current-time provider has been configured.

        None is returned when GARUDA should allow the
        existing runner lifecycle methods to use their
        default datetime behavior.
        """

        if self.current_time_provider is None:

            return None

        return self.current_time_provider()


    # ========================================================
    # PAPER ACCOUNT STATE
    # ========================================================


    def _get_account(self):
        """
        Return GARUDA's authoritative TradingAccount.
        """

        return (
            self.session_engine
            .executor
            .risk_manager
            .account
        )


    def _get_account_state(self):
        """
        Return final GARUDA paper-account values.
        """

        account = self._get_account()

        initial_capital = (
            account.initial_capital
        )

        current_capital = (
            account.current_capital
        )

        net_realized_pnl = (
            current_capital
            - initial_capital
        )

        return {
            "initial_capital": (
                initial_capital
            ),
            "current_capital": (
                current_capital
            ),
            "net_realized_pnl": (
                net_realized_pnl
            ),
        }


    # ========================================================
    # RUNNER LIFECYCLE
    # ========================================================


    def _start_runner(self):
        """
        Start the existing GARUDA live
        paper-trading runner.
        """

        started_at = self._get_current_time()

        if started_at is None:

            self.runner.start()

        else:

            self.runner.start(
                started_at=started_at
            )

        return self.runner.state.started_at


    def _stop_runner_if_running(self):
        """
        Stop the existing GARUDA runner only
        when it is currently active.

        This method supports guaranteed cleanup
        from the session run() finally block.
        """

        if not self.runner.state.running:

            return self.runner.state.stopped_at

        stopped_at = self._get_current_time()

        if stopped_at is None:

            self.runner.stop()

        else:

            self.runner.stop(
                stopped_at=stopped_at
            )

        return self.runner.state.stopped_at


    # ========================================================
    # FINAL STATE COLLECTION
    # ========================================================


    def _build_session_result(
        self,
        polling_result,
    ):
        """
        Build the final controlled GARUDA
        live paper-trading session result.
        """

        runner_summary = (
            self.runner.get_summary()
        )

        portfolio_state = (
            self.polling_engine
            .get_portfolio_state()
        )

        account_state = (
            self._get_account_state()
        )

        return ControlledLivePaperTradingSessionResult(
            status="COMPLETED",
            started_at=(
                self.runner.state.started_at
            ),
            stopped_at=(
                self.runner.state.stopped_at
            ),
            requested_cycles=(
                polling_result.requested_cycles
            ),
            completed_cycles=(
                polling_result.completed_cycles
            ),
            polling_result=polling_result,
            runner_summary=runner_summary,
            portfolio_state=portfolio_state,
            initial_capital=(
                account_state[
                    "initial_capital"
                ]
            ),
            current_capital=(
                account_state[
                    "current_capital"
                ]
            ),
            net_realized_pnl=(
                account_state[
                    "net_realized_pnl"
                ]
            ),
        )


    # ========================================================
    # CONTROLLED SESSION RUN
    # ========================================================


    def run(
        self,
        cycles,
    ):
        """
        Run one controlled GARUDA multi-cycle
        live paper-trading session.

        Flow:

        Validate Cycles
            ↓
        Start Existing Runner
            ↓
        Run Existing Finite Polling Engine
            ↓
        Preserve Existing Runtime State
            ↓
        Stop Runner In Finally Block
            ↓
        Collect Final State
            ↓
        Return Session Result

        Unexpected polling exceptions are allowed
        to propagate after runner cleanup.

        This keeps development failures visible while
        guaranteeing that the runner is not accidentally
        left active.
        """

        # ----------------------------------------------------
        # VALIDATE BEFORE RUNNER START
        # ----------------------------------------------------

        self._validate_requested_cycles(
            cycles=cycles
        )

        # ----------------------------------------------------
        # START EXISTING GARUDA RUNNER
        # ----------------------------------------------------

        self._start_runner()

        polling_result = None

        try:

            # ------------------------------------------------
            # EXISTING FINITE MULTI-SYMBOL POLLING
            # ------------------------------------------------

            polling_result = (
                self.polling_engine.run(
                    cycles=cycles
                )
            )

        finally:

            # ------------------------------------------------
            # GUARANTEED RUNNER CLEANUP
            # ------------------------------------------------

            self._stop_runner_if_running()

        # ----------------------------------------------------
        # FINAL CONTROLLED SESSION RESULT
        # ----------------------------------------------------

        return self._build_session_result(
            polling_result=polling_result
        )