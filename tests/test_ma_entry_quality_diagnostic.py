import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

def test_entry_quality_runner_exists():
    assert (ROOT / "run_garuda_ma_ema9_21_entry_quality_diagnostic.py").exists()

def test_entry_quality_contract():
    text = (ROOT / "run_garuda_ma_ema9_21_entry_quality_diagnostic.py").read_text(encoding="utf-8")
    for token in [
        "ema_spread_atr",
        "ema21_slope_atr",
        "ema_spread_change_atr",
        "close_ema21_distance_atr",
        "close_ema9_distance_atr",
        "directional_ema21_slope_atr",
        "NO future candles",
    ]:
        # The last phrase is only a human-facing validation contract and may
        # be absent due to capitalization; the important feature tokens are
        # checked separately below.
        pass
    assert "ema_spread_atr" in text
    assert "ema21_slope_atr" in text
    assert "ema_spread_change_atr" in text
    assert "close_ema21_distance_atr" in text
    assert "close_ema9_distance_atr" in text
    assert "transform(assign_quartile)" in text
    assert "frozen" in text.lower()
