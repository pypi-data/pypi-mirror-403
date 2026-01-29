import json
import logging
import asyncio
import math
import aiohttp
import ast
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Union, Any

from xecution.common.datasource_constants import GlassNodeConstants
from xecution.models.config import RuntimeConfig
from xecution.models.topic import DataTopic
from xecution.services.connection.restapi import RestAPIClient


class GlassNodeClient:
    def __init__(self, config: RuntimeConfig, data_map: dict):
        self.config      = config
        self.rest_client = RestAPIClient()
        self.data_map    = data_map
        self.headers     = {"X-Api-Key": self.config.glassnode_api_key}

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────
    def _build_url(self, path: str) -> str:
        base = GlassNodeConstants.BASE_URL.rstrip("/")
        return f"{base}/{path}"

    def _extract_items(self, raw: Any) -> List[dict]:
        """
        Glassnode may return:
          - list[dict]
          - dict with 'data' or 'result'
          - dict (single item)
        Normalize to list[dict].
        """
        if isinstance(raw, list):
            return [x for x in raw if isinstance(x, dict)]

        if isinstance(raw, dict):
            candidate: Any = raw.get("data", raw.get("result", raw))
            if isinstance(candidate, str):
                try:
                    candidate = json.loads(candidate)
                except Exception:
                    return []
            if isinstance(candidate, list):
                return [x for x in candidate if isinstance(x, dict)]
            if isinstance(candidate, dict):
                return [candidate]

        return []

    def _parse_step_ms_from_params(self, params: Dict[str, str]) -> int:
        key = (params.get("i") or params.get("interval") or params.get("timeframe") or "").strip().lower()
        if not key:
            return 3_600_000  # 1h default

        def _num(s: str, default="1"):
            try:
                return int(s or default)
            except Exception:
                return int(default)

        if   key.endswith("m"):      return _num(key[:-1]) * 60_000
        if   key.endswith("h"):      return _num(key[:-1]) * 3_600_000
        if   key.endswith("d"):      return _num(key[:-1]) * 86_400_000
        if   key.endswith("w"):      return _num(key[:-1]) * 7 * 86_400_000
        if   key.endswith("month"):  return _num(key[:-5]) * 30 * 86_400_000
        if   key.endswith("y"):      return _num(key[:-1]) * 365 * 86_400_000
        return 3_600_000

    def _chunk_seconds_for_points(self, step_ms: int, points: int) -> int:
        # kept for compatibility (unused in single-call path)
        if step_ms <= 0:
            step_ms = 3_600_000
        points = max(1, points)
        return int((step_ms * points) // 1000)

    def _attach_start_time(self, item: dict) -> Optional[int]:
        ts_ms = None
        if "t" in item and isinstance(item["t"], (int, float)):
            # Glassnode usually uses t (seconds)
            ts_ms = int(item["t"]) * 1000
        elif "time" in item and isinstance(item["time"], (int, float)):
            ts_ms = int(item["time"]) * 1000
        elif "timestamp" in item and isinstance(item["timestamp"], (int, float)):
            ts_ms = int(item["timestamp"]) * 1000
        else:
            dt_str = item.get("datetime") or item.get("date")
            if dt_str:
                try:
                    ts_ms = self.parse_datetime_to_timestamp(dt_str)
                except ValueError as ex:
                    logging.warning(f"Date parsing failed ({dt_str}): {ex}")
        if ts_ms is not None:
            item["start_time"] = ts_ms
        return ts_ms

    def _attach_datetime(self, item: dict) -> None:
        ts_ms = item.get("start_time")
        if isinstance(ts_ms, (int, float)):
            dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
            item["datetime"] = dt.strftime("%Y-%m-%d %H:%M:%S")  # human-friendly UTC

    def _expand_object_payload(self, item: dict) -> None:
        """
        Special handling for Glassnode 'o' payload:
          - If item['o'] is a dict, expand its keys as columns on the item.
          - If item['o'] is a string, attempt to parse it as JSON, then as a Python literal.
        We keep the original 'o' field.
        """
        if "o" not in item:
            return

        obj = item["o"]

        # Try to parse string payload if needed
        if isinstance(obj, str):
            parsed = None
            # First, try strict JSON
            try:
                parsed = json.loads(obj)
            except Exception:
                # Fallback: Python literal (to handle single-quoted dicts)
                try:
                    parsed = ast.literal_eval(obj)
                except Exception:
                    logging.warning(f"[GlassNodeClient] Could not parse 'o' field: {obj!r}")
            if isinstance(parsed, dict):
                obj = parsed

        if not isinstance(obj, dict):
            return

        # Expand nested object as flat columns
        for k, v in obj.items():
            # Avoid overwriting core fields
            if k in {"t", "time", "timestamp", "datetime", "start_time", "topic_url", "v", "o"}:
                continue
            item[k] = v

    # ──────────────────────────────────────────────────────────────────────
    # Sanitizer
    # ──────────────────────────────────────────────────────────────────────
    def _sanitize_records(
        self,
        records: List[dict],
        step_ms: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[dict]:
        # 1) sort + dedupe by start_time
        recs = [r for r in records if isinstance(r, dict) and "start_time" in r]
        recs.sort(key=lambda x: x["start_time"])
        deduped = {r["start_time"]: r for r in recs}
        vals = sorted(deduped.values(), key=lambda x: x["start_time"])

        # 2) optional cadence reconstruction
        filled_seq: List[dict] = []
        prev = None
        if step_ms and step_ms > 0:
            for rec in vals:
                cur_ts = rec.get("start_time")
                if (
                    prev is not None
                    and isinstance(cur_ts, (int, float))
                    and isinstance(prev.get("start_time"), (int, float))
                ):
                    expected = prev["start_time"] + step_ms
                    while cur_ts > expected:
                        ghost = prev.copy()
                        ghost["start_time"] = expected
                        ghost["datetime"] = datetime.fromtimestamp(
                            expected / 1000, tz=timezone.utc
                        ).strftime("%Y-%m-%d %H:%M:%S")
                        filled_seq.append(ghost)
                        logging.debug(f"[sanitize] Gap at {expected} — cloned previous bar")
                        prev = ghost
                        expected += step_ms
                filled_seq.append(rec)
                prev = rec
        else:
            filled_seq = vals

        # 3) forward-fill None values
        cleaned: List[dict] = []
        prev = None
        for rec in filled_seq:
            rec_local = dict(rec)
            if prev is None:
                for k, v in rec_local.items():
                    if v is None:
                        rec_local[k] = math.nan
            else:
                for k, v in rec_local.items():
                    if v is None:
                        rec_local[k] = prev.get(k, math.nan)
            cleaned.append(rec_local)
            prev = rec_local

        # 4) enforce limit
        if isinstance(limit, int) and limit > 0 and len(cleaned) > limit:
            cleaned = cleaned[-limit:]

        return cleaned

    # ──────────────────────────────────────────────────────────────────────
    # fetch: last N via single s/u window
    # ──────────────────────────────────────────────────────────────────────
    async def fetch(self, data_topic: DataTopic, last_n: int = 3):
        if "?" in data_topic.url:
            path, qs = data_topic.url.split("?", 1)
            base_params = dict(part.split("=", 1) for part in qs.split("&") if "=" in part)
        else:
            path = data_topic.url
            base_params = {}

        url = self._build_url(path)

        step_ms = self._parse_step_ms_from_params(base_params)
        step_s  = max(1, step_ms // 1000)

        now   = datetime.now(timezone.utc)
        end_s = int(now.timestamp())
        total_span_s = int(((max(1, last_n) - 1) * step_ms) // 1000)
        start_s = end_s - total_span_s
        # ensure s < u to avoid 400 when last_n == 1
        if start_s >= end_s:
            start_s = max(0, end_s - step_s)

        params = {**base_params, "s": str(start_s), "u": str(end_s), "f": "json"}

        try:
            raw = await self.rest_client.request(
                method="GET",
                url=url,
                params=params,
                headers=self.headers,
                timeout=50,
            )
        except Exception as e:
            logging.error(f"[{datetime.now()}] Error fetching last {last_n} for {data_topic.url}: {e}")
            return []

        items = self._extract_items(raw)
        processed = []
        for item in items:
            ts_ms = self._attach_start_time(item)
            if ts_ms is None:
                continue
            self._attach_datetime(item)
            self._expand_object_payload(item)  # NEW: expand 'o' into flat columns
            item.setdefault("topic_url", data_topic.url)
            processed.append(item)

        sanitized = self._sanitize_records(processed, step_ms=step_ms, limit=last_n)
        self.data_map[data_topic] = sanitized
        return sanitized

    # ──────────────────────────────────────────────────────────────────────
    # fetch_all_parallel (now SINGLE-CALL): request exactly data_count points
    # ──────────────────────────────────────────────────────────────────────
    async def fetch_all_parallel(self, data_topic: DataTopic):
        """
        Single-call version (no chunking) that requests the whole time window
        needed to cover `config.data_count` points, based on the interval.
        """
        limit_points = int(self.config.data_count)
        if limit_points <= 0:
            return []

        # Extract params from topic
        if "?" in data_topic.url:
            path, qs = data_topic.url.split("?", 1)
            base_params = dict(part.split("=", 1) for part in qs.split("&") if "=" in part)
        else:
            path = data_topic.url
            base_params = {}

        url = self._build_url(path)

        # Determine interval size
        step_ms = self._parse_step_ms_from_params(base_params)
        step_s  = max(1, step_ms // 1000)

        # Compute inclusive window [s, u] covering exactly `limit_points` steps
        now              = datetime.now(timezone.utc)
        end_s_overall    = int(now.timestamp())
        total_span_s     = int(((max(1, limit_points) - 1) * step_ms) // 1000)
        start_s_overall  = end_s_overall - total_span_s
        if start_s_overall >= end_s_overall:
            start_s_overall = max(0, end_s_overall - step_s)

        params = dict(base_params)
        params["s"] = str(max(0, start_s_overall))
        params["u"] = str(end_s_overall)
        params["f"] = "json"

        try:
            raw = await self.rest_client.request(
                method="GET",
                url=url,
                params=params,
                headers=self.headers,
                timeout=120,
            )
        except Exception as e:
            logging.error(f"[{datetime.now()}] Error fetching (single-call) for {data_topic.url}: {e}")
            return []

        items = self._extract_items(raw)
        recs: List[dict] = []
        for item in items:
            ts_ms = self._attach_start_time(item)
            if ts_ms is None:
                continue
            self._attach_datetime(item)
            self._expand_object_payload(item)  # NEW: expand 'o' into flat columns
            item.setdefault("topic_url", data_topic.url)
            recs.append(item)

        sanitized = self._sanitize_records(recs, step_ms=step_ms, limit=limit_points)
        self.data_map[data_topic] = sanitized
        return sanitized

    # ──────────────────────────────────────────────────────────────────────
    # parse_datetime_to_timestamp
    # ──────────────────────────────────────────────────────────────────────
    def parse_datetime_to_timestamp(self, dt_str: str) -> int:
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(dt_str, fmt).replace(tzinfo=timezone.utc)
                return int(dt.timestamp() * 1000)
            except ValueError:
                continue
        clean = dt_str.rstrip("Z")
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
