from __future__ import annotations

import importlib

import pandas as pd
from sqlalchemy import text

download_mod = importlib.import_module("bageltushare.download")


def test_download_inserts_rows(engine, token: str, monkeypatch):
    def fake_tushare_download(_token: str, _api_name: str, _params=None, _fields=None):
        return pd.DataFrame(
            {
                "ts_code": ["000001.SZ"],
                "trade_date": ["20250325"],
                "open": [1.0],
            }
        )

    monkeypatch.setattr(download_mod, "tushare_download", fake_tushare_download)

    download_mod.download(engine, token, "daily", retry=1)

    rows = pd.read_sql(text("SELECT ts_code, trade_date, open FROM daily"), engine)
    assert len(rows) == 1


def test_download_logs_on_failure(engine, token: str, monkeypatch):
    def boom(*_args, **_kwargs):
        raise Exception("boom")

    monkeypatch.setattr(download_mod, "tushare_download", boom)

    # Ensure we don't sleep/retry in tests.
    download_mod.download(engine, token, "daily", retry=1)

    logs = pd.read_sql(text("SELECT update_table, message FROM log"), engine)
    assert len(logs) >= 1
    assert "daily" in str(logs.iloc[-1]["update_table"])
    assert "Error downloading" in str(logs.iloc[-1]["message"])

