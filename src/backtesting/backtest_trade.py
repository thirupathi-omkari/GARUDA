from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class BacktestTrade:
    """Represent one completed simulated backtest trade."""

    symbol: str
    strategy_name: str
    trade_date: date
    direction: str

    entry_time: datetime
    entry_price: float

    initial_stop_loss: Optional[float] = None
    current_stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    initial_risk: Optional[float] = None

    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None

    quantity: int = 1

    gross_pnl: float = 0.0
    costs: float = 0.0
    net_pnl: float = 0.0