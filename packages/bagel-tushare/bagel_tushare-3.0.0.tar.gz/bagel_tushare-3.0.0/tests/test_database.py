from sqlalchemy import inspect


def test_create_all_tables(engine):
    insp = inspect(engine)
    tables = set(insp.get_table_names())

    # Spot-check a couple core tables.
    assert "log" in tables
    assert "trade_cal" in tables
