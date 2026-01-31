from datetime import datetime, timezone


def now_utc() -> datetime:
    """Return tz-aware datetime in UTC."""
    return datetime.now(timezone.utc)


def data_br_para_sql(data_br: str):
    return datetime.strptime(data_br, "%d/%m/%Y").strftime("%Y-%m-%d")
