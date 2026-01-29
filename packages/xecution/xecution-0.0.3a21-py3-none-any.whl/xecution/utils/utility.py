# Lightweight helpers for kline/datasource saving.
from __future__ import annotations
from datetime import datetime, timezone
import logging
import math
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence
import pandas as pd
import requests
import re
from xecution.common.enums import OrderStatus
from xecution.models.config import RuntimeConfig

# ───────────────────────── name helpers ─────────────────────────

def parse_order_status(raw_status: str | Any) -> OrderStatus | str:
    """Shared order status parsing logic."""
    if isinstance(raw_status, str):
        s = raw_status.strip().upper().replace("-", "_").replace(" ", "_")
        aliases = {
            "CANCELLED": "CANCELED",
            "PARTIALLYFILLED": "PARTIALLY_FILLED",
            "PARTIALLY_FILLED": "PARTIALLY_FILLED"
        }
        s = aliases.get(s, s)
        try:
            return OrderStatus(s)
        except (ValueError, TypeError):
            return raw_status
    return raw_status

def to_camel(s: str) -> str:
    """Hyphen/underscore/space to UpperCamelCase; safe fallback if to_camel not imported."""
    parts = re.sub(r"[^0-9A-Za-z]+", " ", (s or "")).strip().split()
    return "".join(p[:1].upper() + p[1:] for p in parts) if parts else "Unknown"

def _provider_title(provider) -> str:
    """Brand-cased provider title from enum-like object."""
    name = str(provider).split(".")[-1] if provider is not None else "CRYPTOQUANT"
    mapping = {
        "CRYPTOQUANT": "CryptoQuant",
        "REXILION": "Rexilion",
        "GLASSNODE": "Glassnode",
    }
    return mapping.get(name.upper(), name.title())

def normalize_interval(v: str | None) -> str:
    """Unify interval for filenames."""
    if not v:
        return "1h"
    x = v.strip().lower()
    alias = {"minute": "1m", "hour": "1h", "day": "1d", "week": "1w", "month": "1M"}
    if x in alias:
        return alias[x]
    if x == "24h":
        return "1d"
    if x == "7d":
        return "1w"
    # accept patterns like '10m','1h','2h','1d','1w'
    if re.fullmatch(r"\d+[mhdwM]", x):
        return x
    return x  # last-resort: don't mangle

def qualifier_suffix(params: dict[str, list[str]]) -> str:
    """Build a short suffix like '-Binance-Bithumb-F2pool' to avoid collisions (optional)."""
    keys = [k for k in params.keys() if k.startswith(("from_", "to_", "miner", "exchange", "bank"))]
    if not keys:
        return ""
    vals = []
    for k in sorted(keys):
        val = params.get(k, [""])[0]
        if val:
            vals.append(to_camel(val))
    return ("-" + "-".join(vals)) if vals else ""

def enum_name(x: Any) -> str:
    """Return Enum.name if present; otherwise a reasonable short string."""
    if hasattr(x, "name"):
        return x.name
    s = str(x)
    if "." in s and not s.endswith(">"):
        # e.g. 'KlineType.Binance_Spot'
        return s.split(".", 1)[1]
    if s.startswith("<") and ":" in s:
        # e.g. '<KlineType.Binance_Spot: 1>'
        core = s.split(":", 1)[0].rstrip(">").rsplit(".", 1)[-1]
        return core
    return s

def split_exchange_category(kline_type: Any) -> tuple[str, str]:
    """
    From KlineType like 'Binance_Spot' -> ('Binance', 'Spot').
    Falls back gracefully if underscore not present.
    """
    raw = enum_name(kline_type)
    left, _, right = raw.partition("_")
    exchange = to_camel(left or "Unknown")
    category = to_camel(right or "Spot")
    return exchange, category

def symbol_str(symbol: Any) -> str:
    """Enum Symbol.BTCUSDT -> 'BTCUSDT', else str cleaned of module prefix."""
    if hasattr(symbol, "name"):
        return symbol.name
    s = str(symbol)
    return s.split(".", 1)[-1] if "." in s else s


# ───────────────────────── file helpers ─────────────────────────

def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def write_csv_overwrite(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    """Overwrite CSV with given rows."""
    ensure_parent(path)
    pd.DataFrame(rows).to_csv(path, index=False)

def append_rows_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    """
    Append rows to CSV, writing a header only when file does not exist.
    Accepts any mappable row objects.
    """
    ensure_parent(path)
    df = pd.DataFrame(rows)
    write_header = not path.exists()
    df.to_csv(path, index=False, mode="a", header=write_header)


# ───────────────────────── candle helpers ─────────────────────────

# Common vendor key aliases for candles (be tolerant)
CLOSE_KEYS = ("close", "c", "Close")
OPEN_TIME_KEYS = ("start_time", "t", "open_time", "T")

def extract_first_key(d: Mapping[str, Any], keys: Iterable[str]) -> Any:
    for k in keys:
        if k in d:
            return d[k]
    return None

def last_closed_log_line(symbol: str, timeframe: str, last_bar: Mapping[str, Any], human_time: str) -> str:
    close_val = extract_first_key(last_bar, CLOSE_KEYS)
    return f"Last Kline Closed | {symbol}-{timeframe} | Close: {close_val} | Time: {human_time}"

def send_notification_telegram(message: str, chat_id: str, token: str):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
        requests.get(url, timeout=5)
    except Exception as e:
        logging.error(f"Failed to send message to telegram: {e}")

def get_qty_with_percentage(
    price, precision, wallet_percentage, wallet_balance
):
    try:
        return round_with_precision(wallet_balance * wallet_percentage / price, precision)
    except:
        return 0.0
    
def round_with_precision(number: float, decimal_places: int) -> float:
    """
    Truncate a float to the specified number of decimal places.

    Args:
        number (float): The number to truncate.
        decimal_places (int): The number of decimal places to keep.

    Returns:
        float: The truncated number.
    """
    factor = 10.0**decimal_places
    return math.trunc(factor * number) / factor

def send_notification_discord(webhook:str, message:str):
    try:
        # Message payload
        message_data = {
            'content': message
        }
        # Send POST request to the webhook URL
        requests.post(webhook, json=message_data)
    except Exception as e:
        logging.error(f"Failed to send message to discord: {e}")

def send_telegram_discord_msg(
    discord_webhook,
    telegram_chat_id,
    telegram_token,
    msg,
    bot_id,
    qty,
    price,
    pair,
    total_pnl,
    position,
    entry_time,
):  
    mess = (
        str(bot_id)
        + " "
        + str(msg)
        + " with qty : "
        + str(qty)
        + " at price : "
        + str(price)
        + " with symbol : "
        + str(pair)
        + "\n"
        + "current total_pnl : "
        + str(total_pnl)
        + "\n"
        + "position : "
        + str(position)
        + "at"
        + str(entry_time)
        + "\n"
    )
    send_notification_telegram(
        message=mess,
        chat_id=telegram_chat_id,
        token=telegram_token,
    )
    send_notification_discord(
        message=mess,
        webhook=discord_webhook,
    )

def _build_live_delay_map_min(config: RuntimeConfig) -> Dict[str, int]:
    """
    Flatten {delay_min: [DataTopic,...]} into {topic.url: delay_min}
    """
    groups = getattr(config, "datasource_live_delay_groups_min", None) or {}
    out: Dict[str, int] = {}
    for delay_min, topics in groups.items():
        for t in (topics or []):
            url = getattr(t, "url", None)
            if url:
                out[url] = int(delay_min)
    return out

def _parse_interval_sec_from_url(url: str) -> int:
    if not url or "?" not in url:
        return 3600

    qs = url.split("?", 1)[1]
    params = {}
    for part in qs.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            params[k] = v

    raw = (params.get("i") or params.get("interval") or params.get("timeframe") or "").strip().lower()
    if not raw:
        return 3600

    # common words (CryptoQuant-style)
    if raw in {"hour", "hourly", "1hour", "1h", "1hr"}:
        return 3600
    if raw in {"day", "daily", "1day", "1d"}:
        return 86400

    # generic 10m/60m/4h/1w/...
    try:
        if raw.endswith("m"):
            return int(raw[:-1]) * 60
        if raw.endswith("h"):
            return int(raw[:-1]) * 3600
        if raw.endswith("d"):
            return int(raw[:-1]) * 86400
        if raw.endswith("w"):
            return int(raw[:-1]) * 7 * 86400
    except Exception:
        return 3600

    return 3600

def _next_finalize_due_utc(now_utc: datetime, interval_sec: int, delay_min: int) -> datetime:
    """
    Next run time at (bar close boundary) + delay.
    If the current bar's due time is still in the future, schedule that.
    Otherwise schedule next bar.
    Works for 10m/1h/1d.
    """
    if interval_sec <= 0:
        interval_sec = 3600

    t = int(now_utc.timestamp())

    # current close boundary (floor)
    close = (t // interval_sec) * interval_sec

    due = close + int(delay_min) * 60

    # if we've already passed this bar's due, move to next bar's due
    if due <= t:
        due += interval_sec

    return datetime.fromtimestamp(due, tz=timezone.utc).replace(microsecond=0)