import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pathlib import Path

def test_ma_matrix_runner_exists():
    assert (ROOT / "run_garuda_ma_ema9_21_sl_target_matrix.py").exists()

def test_matrix_contract():
    text = (ROOT / "run_garuda_ma_ema9_21_sl_target_matrix.py").read_text(encoding="utf-8")
    assert "SIGNAL_CANDLE" in text
    assert "SWING_5" in text
    assert "ATR_14_X1" in text
    assert "ATR_14_X1_5" in text
    assert "ATR_14_X2" in text
    assert "1.00" in text
    assert "3.00" in text
