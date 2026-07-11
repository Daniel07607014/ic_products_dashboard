"""Daily ETL: validate raw CSVs under data/raw/ and load them into MySQL.

Full refresh by design: at the current data size (~10k rows) a nightly
replace finishes in seconds and sidesteps upsert/reconciliation problems
(ERP re-exports, amended orders). Revisit and switch to incremental
(load only recent periods) once a full load takes minutes.

Fails loudly BEFORE touching the database: schema drift in any CSV raises
during the read step, so a bad export never half-overwrites good tables.

Usage:
    python scripts/daily_etl.py

Schedule daily at 06:00 with Windows Task Scheduler (run once, adjust paths):
    schtasks /Create /TN "ic-dashboard-daily-etl" /SC DAILY /ST 06:00 /TR ^
      "'C:\\Users\\Daniel Lin\\Desktop\\ic_products_dashboard\\ic_venv\\Scripts\\python.exe' 'C:\\Users\\Daniel Lin\\Desktop\\ic_products_dashboard\\scripts\\daily_etl.py'"
The MySQL container must be running (docker compose 'restart: unless-stopped'
keeps it alive as long as Docker Desktop starts with Windows).
"""
from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import PROJECT_ROOT  # noqa: E402
from scripts.init_db import load_data_tables, verify  # noqa: E402
from src.data.loader import load_all  # noqa: E402

LOG_FILE = PROJECT_ROOT / "logs" / "etl.log"


def _log(line: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {line}\n")
    print(line)


def main() -> int:
    try:
        # Step 1 — validate: read every CSV through the typed loader.
        # Any missing file or column/type drift raises here, before any write.
        tables = load_all(backend="csv")
        counts = {name: len(df) for name, df in tables.items()}
        empty = [name for name, n in counts.items() if n == 0]
        if empty:
            raise ValueError(f"empty input tables: {empty} — refusing to overwrite MySQL")

        # Step 2 — full refresh into MySQL.
        load_data_tables()

        # Step 3 — read back row counts as a self-check.
        verify()

        _log(f"OK — loaded {counts}")
        return 0
    except Exception:
        _log(f"FAILED — {traceback.format_exc().strip().splitlines()[-1]}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
