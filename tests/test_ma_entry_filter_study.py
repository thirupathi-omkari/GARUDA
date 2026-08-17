
def test_filter_study_definitions():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "run_garuda_ma_ema9_21_entry_filter_study.py"
    spec = importlib.util.spec_from_file_location("ma_filter_study", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    specs = mod.make_filter_specs()
    assert specs[0] == ("NO_FILTER", None, None)
    assert len(specs) == 21
    assert len(mod.SL_MODES) == 5
    assert mod.TARGET_RS[0] == 1.0
    assert mod.TARGET_RS[-1] == 3.0
    assert len(mod.TARGET_RS) == 9
