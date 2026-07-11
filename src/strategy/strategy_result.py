from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class StrategyResult:
    """Standard result returned by GARUDA strategies."""

    symbol: str
    strategy_name: str
    signal: str

    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None

    reason: Optional[str] = None

    diagnostics: Dict[str, Any] = field(
        default_factory=dict
    )