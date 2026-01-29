import json
import logging
import asyncio
import math    
import aiohttp
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional  

from xecution.common.datasource_constants import CryptoQuantConstants
from xecution.models.config import RuntimeConfig
from xecution.models.topic import DataTopic, DataProvider
from xecution.services.connection.restapi import RestAPIClient


class CryptoQuantClient:
    def __init__(self, config: RuntimeConfig, data_map: dict):
        self.config      = config
        self.rest_client = RestAPIClient()
        self.data_map    = data_map
        self.headers     = {
            'Authorization': f'Bearer {self.config.cryptoquant_api_key}',
        }

    # -------------------------------------------------------------------------
    # _sanitize_records: unify cleanup for fetch() and fetch_all_parallel()
    # -------------------------------------------------------------------------
    def _sanitize_records(
        self,
        records: List[dict],
        step_ms: Optional[int] = None,   
        limit: Optional[int] = None     
    ) -> List[dict]:
        """
        <<< MOD
        Normalize raw CryptoQuant rows so downstream consumers don't choke:
        - sort + dedupe by start_time
        - optional timestamp gap-fill if step_ms provided
        - forward-fill missing values so newest bar is "as filled as possible"
        - never leave raw None in later bars
        - first bar still gets math.nan if field truly missing (we cannot invent)
        - we DO NOT delete the last bar
        - we DO NOT add new columns to bars
        """

        # 1. sort + dedupe by start_time
        recs = [r for r in records if isinstance(r, dict) and 'start_time' in r]
        recs.sort(key=lambda x: x['start_time'])
        deduped = {}
        for r in recs:
            deduped[r['start_time']] = r
        vals = list(deduped.values())
        vals.sort(key=lambda x: x['start_time'])

        # 2. optional cadence reconstruction (fill missing timestamps using previous bar clone)
        filled_seq: List[dict] = []
        prev = None
        if step_ms is not None and step_ms > 0:
            for rec in vals:
                cur_ts = rec.get('start_time')
                if (
                    prev is not None
                    and isinstance(cur_ts, (int, float))
                    and isinstance(prev.get('start_time'), (int, float))
                ):
                    expected = prev['start_time'] + step_ms
                    while cur_ts > expected:
                        ghost = prev.copy()         
                        ghost['start_time'] = expected
                        if 'datetime' in ghost:
                            ghost['datetime'] = datetime.fromtimestamp(
                                expected / 1000, tz=timezone.utc
                            ).strftime("%Y-%m-%d %H:%M:%S")
                        filled_seq.append(ghost)
                        logging.debug(
                            f"[sanitize] Gap detected at {expected} — cloned previous bar"
                        )
                        prev = ghost
                        expected += step_ms

                filled_seq.append(rec)
                prev = rec
        else:
            # no cadence invention for live polling
            filled_seq = vals

        # 3. forward-fill None values
        #
        #    - For the very first bar in sequence:
        #         None -> math.nan (we don't know true value yet)
        #
        #    - For all subsequent bars:
        #         None -> previous bar's value (forward fill)
        #         If previous bar also didn't have it (very rare), we fall back to math.nan
        #
        #    NOTE: This means the newest bar will always be "as filled as possible"
        #          using forward fill. We do NOT drop that bar anymore.
        cleaned: List[dict] = []
        prev = None
        for rec in filled_seq:
            # copy so we don't mutate shared dict objects
            rec_local = dict(rec)

            if prev is None:
                # first bar: fill missing with NaN (can't forward fill yet)
                missing_keys = []
                for k, v in rec_local.items():
                    if v is None:
                        rec_local[k] = math.nan      
                        missing_keys.append(k)
                if missing_keys:
                    logging.error(
                        f"[sanitize] First bar {rec_local.get('start_time')} "
                        f"missing {missing_keys}, set to NaN"
                    )
            else:
                # later bars: forward fill from prev
                missing_keys = []
                for k, v in rec_local.items():
                    if v is None:
                        rec_local[k] = prev.get(k, math.nan) 
                        missing_keys.append(k)
                if missing_keys:
                    logging.debug(
                        f"[sanitize] Bar {rec_local.get('start_time')} forward-filled {missing_keys}"
                    )

                # EXTRA PATCH: if prev itself had math.nan, you just copied math.nan forward.
                # This is still allowed (you said "just forward fill"). We do NOT delete.
                # We do NOT override nan with fake values.

            cleaned.append(rec_local)
            prev = rec_local

        # 4. enforce limit (keep most recent N bars)
        if isinstance(limit, int) and limit > 0 and len(cleaned) > limit:
            cleaned = cleaned[-limit:]  

        # 5. NO DELETE STEP ANYMORE  <<< MOD
        # We used to maybe drop the latest bar if it still had NaN.
        # You said "i dont want delete, i want just forward fill".
        # So we keep all bars, even if the newest still has NaN because
        # there was never any valid value to forward fill from.

        return cleaned  

    # -------------------------------------------------------------------------
    # fetch(): live-tail fetch, now sanitized
    # -------------------------------------------------------------------------
    async def fetch(self, data_topic: DataTopic, last_n: int = 3):
        """
        Fetch only the last `last_n` records for `data_topic` (no `to` param).

        <<< MOD
        After HTTP:
        - attach start_time
        - sanitize with forward-fill logic
        - we do NOT drop the last record
        - we do NOT add new columns
        """
        # parse path and base params
        if '?' in data_topic.url:
            path, qs = data_topic.url.split('?', 1)
            base_params = dict(part.split('=', 1) for part in qs.split('&'))
        else:
            path = data_topic.url
            base_params = {}

        url = CryptoQuantConstants.BASE_URL + path
        params = {**base_params, 'limit': last_n}

        try:
            raw = await self.rest_client.request(
                method='GET',
                url=url,
                params=params,
                headers=self.headers,
                timeout=50
            )
        except Exception as e:
            logging.error(
                f"[{datetime.now()}] Error fetching last {last_n} for {data_topic.url}: {e}"
            )
            return []

        result = raw.get('result', raw)
        data   = result.get('data') if isinstance(result, dict) else result
        items  = data if isinstance(data, list) else [data]

        processed = []
        for item in items or []:
            dt_str = item.get('datetime') or item.get('date')
            if dt_str:
                try:
                    item['start_time'] = self.parse_datetime_to_timestamp(dt_str)
                except ValueError as ex:
                    logging.warning(f"Date parsing failed ({dt_str}): {ex}")
            processed.append(item)

        sanitized = self._sanitize_records(
            processed,
            step_ms=None, 
            limit=last_n
        )

        self.data_map[data_topic] = sanitized  
        return sanitized                       

    # -------------------------------------------------------------------------
    # fetch_all_parallel(): bulk warm load, uses same sanitizer
    # -------------------------------------------------------------------------
    async def fetch_all_parallel(self, data_topic: DataTopic):
        """
        Fetch up to `config.data_count` bars ending now.

        - Single GET for most endpoints.
        - Batched GETs only for 'stablecoins-ratio'.

        <<< MOD
        After fetching:
        - flatten
        - infer cadence step_ms (hour/day)
        - run through _sanitize_records() for forward-fill behavior
          (including filling timestamp gaps using cloned previous bars)
        - do NOT drop newest bar
        - do NOT add new columns
        """
        limit      = self.config.data_count
        base_limit = 1000
        windows    = -(-limit // base_limit)  # ceil division
        end        = datetime.now(timezone.utc)

        # parse URL and base params
        if '?' in data_topic.url:
            path, qs = data_topic.url.split('?', 1)
            base_params = dict(part.split('=') for part in qs.split('&'))
        else:
            path = data_topic.url
            base_params = {}
        url = CryptoQuantConstants.BASE_URL + path

        session = aiohttp.ClientSession()
        try:
            if not (
                data_topic.provider is DataProvider.CRYPTOQUANT and
                'stablecoins-ratio' in data_topic.url
            ):
                # single-fetch branch
                try:
                    async with session.get(
                        url,
                        params={**base_params, 'limit': limit, 'format': 'json'},
                        headers=self.headers
                    ) as resp:
                        resp.raise_for_status()
                        raw = await resp.json()
                except Exception as e:
                    logging.error(
                        f"[{datetime.now()}] Error fetching data for {data_topic.url}: {e}"
                    )
                    batches = [[]]
                else:
                    result = raw.get('result', raw)
                    data   = result.get('data') if isinstance(result, dict) else result
                    items  = data if isinstance(data, list) else [data]

                    batch = []
                    for item in items or []:
                        dt_str = item.get('datetime') or item.get('date')
                        if dt_str:
                            try:
                                item['start_time'] = self.parse_datetime_to_timestamp(dt_str)
                            except ValueError as ex:
                                logging.warning(f"Date parsing failed ({dt_str}): {ex}")
                        batch.append(item)
                    batches = [batch]
            else:
                # batch-fetch branch for 'stablecoins-ratio'
                async def fetch_batch(to_ts: datetime):
                    from_str = to_ts.strftime('%Y%m%dT%H%M%S')
                    params   = {**base_params, 'limit': base_limit, 'to': from_str, 'format': 'json'}
                    try:
                        async with session.get(url, params=params, headers=self.headers) as resp:
                            resp.raise_for_status()
                            raw = await resp.json()
                    except Exception as e:
                        logging.error(
                            f"[{datetime.now()}] Parallel fetch error: {e}"
                        )
                        return []

                    result = raw.get('result', raw.get('data', raw))
                    if isinstance(result, dict) and 'data' in result:
                        result = result['data']
                        if isinstance(result, str):
                            result = json.loads(result)
                    if isinstance(result, dict):
                        result = [result]

                    recs = []
                    for item in result or []:
                        dt_str = item.get('datetime')
                        if dt_str:
                            try:
                                item['start_time'] = self.parse_datetime_to_timestamp(dt_str)
                            except ValueError as ex:
                                logging.warning(f"Date parsing failed ({dt_str}): {ex}")
                                continue
                        recs.append(item)
                    return recs

                tasks   = [fetch_batch(end - timedelta(hours=i * base_limit)) for i in range(windows)]
                batches = await asyncio.gather(*tasks)
        finally:
            await session.close()

        # flatten batches
        flat = [rec for batch in batches for rec in batch if isinstance(rec, dict)]

        # infer cadence (hour/day)
        HOUR_MS = 3_600_000
        DAY_MS  = 86_400_000

        def _parse_step_ms(bp: dict, sample: List[dict]) -> int:
            try:
                key = (bp.get("window") or bp.get("interval") or bp.get("timeframe") or "").lower()
            except Exception:
                key = ""
            if key.endswith("d"):
                try:
                    return (int(key[:-1] or "1")) * DAY_MS
                except Exception:
                    pass
            if key.endswith("h"):
                try:
                    return (int(key[:-1] or "1")) * HOUR_MS
                except Exception:
                    pass

            ts = [r.get("start_time") for r in sample if isinstance(r.get("start_time"), (int, float))]
            ts = sorted(set(ts))
            if len(ts) >= 2:
                d = ts[1] - ts[0]
                if abs(d - DAY_MS)  <= 0.1 * DAY_MS:
                    return DAY_MS
                if abs(d - HOUR_MS) <= 0.1 * HOUR_MS:
                    return HOUR_MS
            return HOUR_MS  # default assume hourly

        step_ms = _parse_step_ms(base_params, flat)  

        sanitized = self._sanitize_records(
            flat,
            step_ms=step_ms,
            limit=limit
        )

        self.data_map[data_topic] = sanitized  
        return sanitized                       

    def parse_datetime_to_timestamp(self, dt_str: str) -> int:
        for fmt in (
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
        ):
            try:
                dt = datetime.strptime(dt_str, fmt).replace(tzinfo=timezone.utc)
                return int(dt.timestamp() * 1000)
            except ValueError:
                continue
        try:
            clean = dt_str.rstrip('Z')
            dt    = datetime.fromisoformat(clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        except Exception:
            raise ValueError(f"Unrecognized date format: {dt_str}")
