"""SWEEP-003 / BOOK-001 (2026-10-09): agent/scoreboard.py writes scoreboard.json and scoreboard.html beside-and-replace through agent/atomicio.py (the byte-identical mirror of stock-radar's).
It truncated both in place; the resolver's check_crypto_scoreboard_* and the dashboards read them. The four CRYPTO-006 forecaster writes (horizon_forecaster.py:139,141, minute_forecaster.py:221,225) are NOT touched: retired, unloaded, byte-pinned.
Pinned: the mirror; no truncating open in scoreboard.py; old == new byte for byte; scoreboard.py loads by path from a foreign cwd.
Run: /opt/anaconda3/bin/python -m pytest -q agent/test_book001_sweep003.py"""
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

AG = Path(__file__).resolve().parent
sys.path.insert(0, str(AG))
import atomicio  # noqa: E402


def test_the_mirror_is_byte_identical_to_stock_radar():
    src = Path.home() / "stock-radar" / "atomicio.py"
    if not src.exists():
        pytest.skip("stock-radar is not on this machine")
    assert (AG / "atomicio.py").read_bytes() == src.read_bytes()


def test_scoreboard_does_not_truncate_in_place():
    for n in ast.walk(ast.parse((AG / "scoreboard.py").read_text())):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open":
            mode = n.args[1] if len(n.args) > 1 else None
            assert not (isinstance(mode, ast.Constant) and str(mode.value).startswith("w")), f"scoreboard.py:{n.lineno} opens for truncating write"


def test_atomic_writes_equal_the_old_ones(tmp_path):
    d = {"built_utc": "2026-10-09T17:00:00Z", "horizons": {"1": {"resolved": 3, "hit_rate": 0.5}}, "note": "café"}
    with open(tmp_path / "old.json", "w") as f:
        json.dump(d, f, indent=1)
    atomicio.atomic_json(str(tmp_path / "new.json"), d, indent=1)
    assert (tmp_path / "old.json").read_bytes() == (tmp_path / "new.json").read_bytes()
    html = "<html>café — scoreboard</html>\n"
    with open(tmp_path / "old.html", "w") as f:
        f.write(html)
    atomicio.atomic_write_text(str(tmp_path / "new.html"), html)
    assert (tmp_path / "old.html").read_bytes() == (tmp_path / "new.html").read_bytes()
    assert sorted(os.listdir(tmp_path)) == ["new.html", "new.json", "old.html", "old.json"]


def test_scoreboard_loads_by_path_from_any_cwd(tmp_path):
    code = "import importlib.util as u,sys; s=u.spec_from_file_location('probe', sys.argv[1]); m=u.module_from_spec(s); s.loader.exec_module(m)"
    r = subprocess.run([sys.executable, "-c", code, str(AG / "scoreboard.py")], cwd=tmp_path, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-300:]
