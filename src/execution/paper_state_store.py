import json
from datetime import datetime
from pathlib import Path


class PaperStateStore:
    """
    Persist and restore GARUDA paper-trading state.

    Persistent state includes:

        - authoritative account capital
        - open paper positions
        - runner candle state
        - active exit-management state

    Completed trades remain in the existing
    TradeCSVJournal.
    """

    def __init__(
        self,
        file_path="data/paper/paper_state.json",
    ):
        self.file_path = Path(file_path)

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def exists(self):
        return self.file_path.exists()

    def save(
        self,
        account,
        position_manager,
        runner=None,
        session_engine=None,
    ):
        state = {
            "account": {
                "initial_capital": float(
                    account.initial_capital
                ),
                "current_capital": float(
                    account.current_capital
                ),
            },
            "positions": [
                {
                    "symbol": position.symbol,
                    "side": position.side,
                    "quantity": position.quantity,
                    "entry_price": float(
                        position.entry_price
                    ),
                    "current_price": float(
                        position.current_price
                    ),
                    "entry_time": (
                        position.entry_time.isoformat()
                    ),
                }
                for position
                in position_manager.positions
            ],
        }

        # --------------------------------------------------
        # RUNNER STATE
        # --------------------------------------------------

        if runner is not None:

            state["runner"] = {
                "symbols": {}
            }

            for (
                symbol,
                symbol_state,
            ) in runner.state.symbols.items():

                state["runner"]["symbols"][
                    symbol
                ] = {
                    "symbol": symbol,
                    "instrument_token": (
                        symbol_state.instrument_token
                    ),
                    "last_processed_candle_time": (
                        symbol_state
                        .last_processed_candle_time
                        .isoformat()
                        if symbol_state
                        .last_processed_candle_time
                        is not None
                        else None
                    ),
                    "last_entry_candle_time": (
                        symbol_state
                        .last_entry_candle_time
                        .isoformat()
                        if symbol_state
                        .last_entry_candle_time
                        is not None
                        else None
                    ),
                    "position_open": (
                        symbol_state.position_open
                    ),
                    "processed_candle_count": (
                        symbol_state.processed_candle_count
                    ),
                    "generated_signal_count": (
                        symbol_state.generated_signal_count
                    ),
                    "executed_trade_count": (
                        symbol_state.executed_trade_count
                    ),
                    "rejected_trade_count": (
                        symbol_state.rejected_trade_count
                    ),
                    "closed_trade_count": (
                        symbol_state.closed_trade_count
                    ),
                }

        # --------------------------------------------------
        # SESSION EXIT STATE
        # --------------------------------------------------

        if session_engine is not None:

            state["active_exit_levels"] = (
                dict(
                    session_engine
                    ._active_exit_levels
                )
            )

        temporary_file = (
            self.file_path.with_suffix(".tmp")
        )

        with temporary_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                state,
                file,
                indent=2,
            )

        temporary_file.replace(
            self.file_path
        )

    def load(self):

        if not self.file_path.exists():

            return None

        with self.file_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    def restore_account(
        self,
        account,
    ):

        state = self.load()

        if state is None:
            return account

        account_state = state.get(
            "account"
        )

        if account_state is None:
            return account

        account.initial_capital = float(
            account_state[
                "initial_capital"
            ]
        )

        account.current_capital = float(
            account_state[
                "current_capital"
            ]
        )

        return account

    def restore_positions(
        self,
        position_manager,
    ):

        state = self.load()

        if state is None:
            return

        for position_state in state.get(
            "positions",
            [],
        ):

            position_manager.restore_position(
                symbol=position_state[
                    "symbol"
                ],
                side=position_state[
                    "side"
                ],
                quantity=int(
                    position_state[
                        "quantity"
                    ]
                ),
                entry_price=float(
                    position_state[
                        "entry_price"
                    ]
                ),
                current_price=float(
                    position_state[
                        "current_price"
                    ]
                ),
                entry_time=datetime.fromisoformat(
                    position_state[
                        "entry_time"
                    ]
                ),
            )

    def restore_runner(
        self,
        runner,
    ):

        state = self.load()

        if state is None:
            return

        runner_state = state.get(
            "runner"
        )

        if runner_state is None:
            return

        for (
            symbol,
            saved_symbol,
        ) in runner_state.get(
            "symbols",
            {},
        ).items():

            normalized_symbol = (
                symbol.upper()
            )

            if normalized_symbol not in (
                runner.state.symbols
            ):

                runner.register_symbol(
                    symbol=normalized_symbol,
                    instrument_token=(
                        saved_symbol[
                            "instrument_token"
                        ]
                    ),
                )

            symbol_state = (
                runner.get_symbol_state(
                    normalized_symbol
                )
            )

            last_processed = (
                saved_symbol[
                    "last_processed_candle_time"
                ]
            )

            if last_processed is not None:

                symbol_state.last_processed_candle_time = (
                    datetime.fromisoformat(
                        last_processed
                    )
                )

            last_entry = (
                saved_symbol[
                    "last_entry_candle_time"
                ]
            )

            if last_entry is not None:

                symbol_state.last_entry_candle_time = (
                    datetime.fromisoformat(
                        last_entry
                    )
                )

            symbol_state.position_open = (
                saved_symbol[
                    "position_open"
                ]
            )

            symbol_state.processed_candle_count = (
                saved_symbol[
                    "processed_candle_count"
                ]
            )

            symbol_state.generated_signal_count = (
                saved_symbol[
                    "generated_signal_count"
                ]
            )

            symbol_state.executed_trade_count = (
                saved_symbol[
                    "executed_trade_count"
                ]
            )

            symbol_state.rejected_trade_count = (
                saved_symbol[
                    "rejected_trade_count"
                ]
            )

            symbol_state.closed_trade_count = (
                saved_symbol[
                    "closed_trade_count"
                ]
            )

    def restore_exit_levels(
        self,
        session_engine,
    ):

        state = self.load()

        if state is None:
            return

        exit_levels = state.get(
            "active_exit_levels"
        )

        if exit_levels is None:
            return

        for (
            symbol,
            levels,
        ) in exit_levels.items():

            session_engine.restore_exit_levels(
                symbol=symbol,
                exit_levels=levels,
            )