from __future__ import annotations

import pandas as pd

from bageltushare import tushare_download


def test_tushare_download_passes_fields(monkeypatch):
    captured: dict = {}

    class DummyPro:
        def query(self, api_name: str, **kwargs):
            captured["api_name"] = api_name
            captured["kwargs"] = kwargs
            return pd.DataFrame({"a": [1]})

    def fake_pro_api(token: str):
        captured["token"] = token
        return DummyPro()

    monkeypatch.setattr("bageltushare.tushare_api.pro_api", fake_pro_api)

    df = tushare_download("TOKEN", "daily", {"ts_code": "000001.SZ"}, fields=["a", "b"])
    assert df is not None
    assert captured["token"] == "TOKEN"
    assert captured["api_name"] == "daily"
    assert captured["kwargs"]["ts_code"] == "000001.SZ"
    assert captured["kwargs"]["fields"] == "a,b"


def test_tushare_download_without_fields(monkeypatch):
    class DummyPro:
        def query(self, api_name: str, **kwargs):
            assert "fields" not in kwargs
            return pd.DataFrame({"x": [1]})

    monkeypatch.setattr("bageltushare.tushare_api.pro_api", lambda token: DummyPro())

    df = tushare_download("TOKEN", "daily", {"ts_code": "000001.SZ"})
    assert df is not None
