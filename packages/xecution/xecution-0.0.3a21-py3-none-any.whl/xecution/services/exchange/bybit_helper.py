import logging
import aiohttp
import asyncio
import socket
from typing import Optional
from datetime import datetime, timezone
from xecution.common.enums import Exchange, KlineType, Mode, OrderSide, OrderStatus, OrderType, Symbol, TimeInForce
from xecution.common.exchange.live_constants import LiveConstants
from xecution.common.exchange.testnet_constants import TestnetConstants
from xecution.models.order import ActiveOrder, Level, OrderBookSnapshot, OrderResponse, OrderUpdate, OrderHistory
from xecution.models.config import RuntimeConfig
from xecution.models.position import Position, PositionData
from xecution.models.topic import KlineTopic
from xecution.utils.utility import parse_order_status
from .safe_kline_downloader import SafeKlineDownloader

# Utility functions for the Bybit service
class BybitHelper:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    # Mapping of interval strings to milliseconds (your internal time math)
    interval_to_ms = {
        "1m": 60 * 1000,
        "3m": 3 * 60 * 1000,
        "5m": 5 * 60 * 1000,
        "15m": 15 * 60 * 1000,
        "30m": 30 * 60 * 1000,
        "1h": 60 * 60 * 1000,
        "2h": 2 * 60 * 60 * 1000,
        "4h": 4 * 60 * 60 * 1000,
        "6h": 6 * 60 * 60 * 1000,
        "8h": 8 * 60 * 60 * 1000,
        "12h": 12 * 60 * 60 * 1000,
        "1d": 24 * 60 * 60 * 1000,
    }

    # Map your timeframe tokens to Bybit v5 interval values
    timeframe_to_bybit_interval = {
        "1m": "1",
        "3m": "3",
        "5m": "5",
        "15m": "15",
        "30m": "30",
        "1h": "60",
        "2h": "120",
        "4h": "240",
        "6h": "360",
        "8h": "480",
        "12h": "720",
        "1d": "D",
    }

    @staticmethod
    def convert_ws_kline(k: dict) -> dict:
        """
        Convert a Bybit WebSocket kline payload (v5 `kline.*`) to a simplified format.
        Expected fields in each item: start, end, open, high, low, close, volume, turnover, confirm
        """
        try:
            return {
                "start_time": int(k.get("start")),
                "end_time":   int(k.get("end")),
                "open":       float(k.get("open")),
                "high":       float(k.get("high")),
                "low":        float(k.get("low")),
                "close":      float(k.get("close")),
                "volume":     float(k.get("volume"))
            }
        except Exception:
            logging.exception(f"Failed to convert WebSocket kline: {k}")
            return {}

    @staticmethod
    def convert_rest_kline(kline: list) -> dict:
        """
        Convert a Bybit REST v5 kline (result.list entry) to a simplified format.
        Bybit v5 list entry: [start, open, high, low, close, volume, turnover]
        """
        try:
            return {
                "start_time": int(kline[0]),
                "end_time":   int(kline[0]),  # Bybit REST doesn't return end; keep start here
                "open":       float(kline[1]),
                "high":       float(kline[2]),
                "low":        float(kline[3]),
                "close":      float(kline[4]),
                "volume":     float(kline[5]),
            }
        except Exception:
            logging.exception(f"Failed to convert REST kline: {kline}")
            return {}

    @staticmethod
    def get_restapi_base_url(kline_topic: KlineTopic, mode: Mode):
        """
        Determine the REST API base URL based on kline type (spot vs derivatives) and mode.
        """
        base = TestnetConstants.Bybit if mode == Mode.Testnet else LiveConstants.Bybit
        # Both spot and derivatives use v5 under same REST base in most setups
        return base.RESTAPI_URL

    @staticmethod
    def get_websocket_base_url(kline_topic: KlineTopic, mode: Mode):
        base = LiveConstants.Bybit if mode == Mode.Live else TestnetConstants.Bybit
        is_spot = (kline_topic.klineType == KlineType.Bybit_Spot)
        return f"{base.WEBSOCKET_PUBLIC_URL}/{'spot' if is_spot else 'linear'}"

    @staticmethod
    def get_websocket_user_data_base_url(mode: Mode):
        """
        Get the WebSocket private (user data) URL for account/order events.
        """
        base = LiveConstants.Bybit if mode == Mode.Live else TestnetConstants.Bybit
        return base.WEBSOCKET_PRIVATE_URL

    async def fetch_kline(self, session, url, params):
        async with session.get(url, params=params) as response:
            data = await response.json()
            # Bybit v5 returns {"retCode":0, "result":{"list":[...]}}
            try:
                lst = (data.get("result", {}) or {}).get("list", []) or []
                return list(reversed(lst))  # now oldest→newest
            except Exception:
                return []

    def _bybit_category(self, kline_type: KlineType) -> str:
        # Map your enum to Bybit v5 category param
        return "spot" if kline_type == KlineType.Bybit_Spot else "linear"

    async def getKlineRestAPI(self, kline_topic: KlineTopic, end_time: Optional[int] = None):
        try:
            base_url = self.get_restapi_base_url(kline_topic, self.config.mode)
            endpoint = base_url + "/v5/market/kline"
            symbol = kline_topic.symbol.value
            timeframe = kline_topic.timeframe.lower()
            interval = self.timeframe_to_bybit_interval.get(timeframe, "60")  # default 1h
            category = self._bybit_category(kline_topic.klineType)

            async with aiohttp.ClientSession() as session:
                if end_time is None:
                    end_time = int(datetime.now(timezone.utc).timestamp() * 1000)

                total_needed = self.config.kline_count
                time_increment = BybitHelper.interval_to_ms.get(timeframe, 60 * 1000)

                downloader = SafeKlineDownloader(
                    session=session,
                    fetch_func=self.fetch_kline,
                    endpoint=endpoint,
                    symbol=symbol,
                    interval=interval,
                    extra_params={"category": category},
                    max_limit=1000,
                    time_increment_ms=time_increment,
                    max_concurrent_requests=10,
                    chunk_sleep=0,
                    start_key="start",
                    end_key="end",
                )

                total_data = await downloader.download_reverse(end_time=end_time, total_needed=total_needed)
                converted_data = [self.convert_rest_kline(k) for k in total_data]
                converted_data = converted_data[5:]  # Drop the first 5 bars as warm-up
                return converted_data
        except Exception as e:
            logging.error(f"getKlineRestAPI: {e}")

    async def getLatestKline(self, kline_topic: KlineTopic):
        try:
            base_url = self.get_restapi_base_url(kline_topic, self.config.mode)
            endpoint = base_url + "/v5/market/kline"
            symbol = kline_topic.symbol.value
            timeframe = kline_topic.timeframe.lower()
            interval = self.timeframe_to_bybit_interval.get(timeframe, "60")
            category = self._bybit_category(kline_topic.klineType)

            params = {
                "category": category,
                "symbol": symbol,
                "interval": interval,
                "limit": 2
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, params=params) as resp:
                    if resp.status != 200:
                        logging.error(f"Failed to fetch latest kline for {symbol}: HTTP {resp.status}")
                        return None

                    data = await resp.json()
                    kl = (data or {}).get("result", {}).get("list", [])
                    if not kl or not isinstance(kl, list):
                        logging.warning(f"No kline data received for {symbol}")
                        return None

                    latest_kline = [self.convert_rest_kline(k) for k in kl]
                    return latest_kline

        except (aiohttp.ClientError, asyncio.TimeoutError, socket.gaierror) as e:
            logging.error(f"getKlineRestAPI (latest candle): {e}")
            return None
        except Exception as e:
            logging.error(f"getKlineRestAPI (latest candle): Unexpected error: {e}")
            return None
        
    def parse_order_book(self, data: dict) -> OrderBookSnapshot:
        """
        Convert Bybit order book JSON into an OrderBookSnapshot.
        Supports:
        - top-level Bybit response with 'result'
        - direct dicts shaped like {'b': [[p, q],...], 'a': [[p, q],...]}
        - alt keys {'bids': [...], 'asks': [...]}
        """
        # unwrap Bybit top-level envelope if present
        payload = data.get("result", data) or {}

        bids_src = payload.get("b") or payload.get("bids") or []
        asks_src = payload.get("a") or payload.get("asks") or []

        def to_level(pair):
            # pair can be ['115922.3','4.63'] or {'price':..., 'size':...}
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                price, qty = pair[0], pair[1]
            elif isinstance(pair, dict):
                price, qty = pair.get("price"), pair.get("size")
            else:
                return None
            try:
                return Level(price=float(price), quantity=float(qty))
            except (TypeError, ValueError):
                return None

        bids = [lvl for p in bids_src if (lvl := to_level(p)) is not None]
        asks = [lvl for p in asks_src if (lvl := to_level(p)) is not None]

        # (optional) ensure correct book ordering
        bids.sort(key=lambda x: x.price, reverse=True)
        asks.sort(key=lambda x: x.price)

        return OrderBookSnapshot(bids=bids, asks=asks)

    def parse_order_update(self, raw_event: dict, exchange: Exchange = Exchange.Bybit) -> OrderUpdate:
        o = raw_event.get("data", {}) if "data" in raw_event else raw_event

        # --- normalize status ---
        raw_status = o.get("orderStatus")
        if raw_status is None:
            raw_status = o.get("status")

        status_out = raw_status
        if isinstance(raw_status, str):
            s = raw_status.strip().upper().replace("-", "_").replace(" ", "_")
            aliases = {
                "CANCELLED": "CANCELED",
                "PARTIALLYFILLED": "PARTIALLY_FILLED",
                "PARTIALLY_FILLED": "PARTIALLY_FILLED",
                "PARTIALLY-FILLED": "PARTIALLY_FILLED",
            }
            s = aliases.get(s, s)
            try:
                status_out = OrderStatus(s)
            except ValueError:
                status_out = raw_status  # leave as-is if truly unknown

        # --- normalize symbol -> Symbol enum ---
        raw_symbol = o.get("symbol")
        try:
            symbol_val = Symbol(raw_symbol)
        except Exception:
            # fallback if it’s something we don’t have in the enum
            symbol_val = raw_symbol  # keep string so we at least see it in logs

        # --- normalize order type ---
        raw_order_type = o.get("orderType")
        try:
            order_type_val = OrderType(str(raw_order_type).upper())
        except Exception:
            order_type_val = raw_order_type  # leave raw if not in enum

        # --- normalize side ---
        raw_side = o.get("side")
        try:
            side_val = OrderSide(str(raw_side).upper())
        except Exception:
            side_val = raw_side

        # --- normalize time in force ---
        raw_tif = o.get("timeInForce")
        try:
            tif_val = TimeInForce(str(raw_tif).upper())
        except Exception:
            tif_val = raw_tif

        # --- normalize timestamps ---
        # bybit/binance often send ms timestamps (ints as strings)
        def _to_dt(v):
            if isinstance(v, datetime):
                return v
            if v is None:
                return datetime.now(timezone.utc)
            try:
                # try numeric ms
                iv = int(v)
                # heuristic: treat > 10^12 as ms epoch
                if iv > 10**12:
                    iv = iv / 1000.0
                return datetime.fromtimestamp(iv, tz=timezone.utc)
            except Exception:
                # last resort: now
                return datetime.now(timezone.utc)

        order_time_dt = _to_dt(o.get("createdTime") or o.get("createTime") or 0)
        updated_time_dt = _to_dt(o.get("updatedTime") or raw_event.get("ts", 0))

        # --- build OrderUpdate dataclass with normalized fields ---
        return OrderUpdate(
            symbol=symbol_val,
            order_type=order_type_val,
            side=side_val,
            time_in_force=tif_val,
            exchange_order_id=str(o.get("Id")),
            order_time=order_time_dt,
            updated_time=updated_time_dt,
            size=float(o.get("qty") or 0),
            filled_size=float(o.get("cumExecQty") or 0),
            remain_size=float(o.get("leavesQty") or 0),
            price=float(o.get("avgPrice") or o.get("price") or 0),
            client_order_id=o.get("orderId"),
            status=status_out,
            is_reduce_only=bool(o.get("reduceOnly", False)),
            is_hedge_mode=None,
            exchange=exchange,
        )

    def convert_order_to_active_order(self, order: dict) -> ActiveOrder:
        symbol = Symbol(order["symbol"])
        exchange = Exchange.Bybit
        updated_time = int(order.get("updatedTime") or order.get("updateTime") or 0)
        created_time = int(order.get("createdTime") or order.get("createTime") or 0)
        exchange_order_id = str(order.get("Id"))
        client_order_id = order.get("orderId")

        side = (order.get("side") or "").upper()
        qty = float(order.get("qty") or order.get("origQty") or 0.0)
        filled_qty = float(order.get("cumExecQty"))
        remain_qty = float(order.get("leavesQty"))
        avg = float(order.get("avgPrice") or 0.0)

        if side == "BUY":
            long_data = PositionData(quantity=qty, avg_price=avg)
            short_data = PositionData(quantity=0.0, avg_price=0.0)
        elif side == "SELL":
            long_data = PositionData(quantity=0.0, avg_price=0.0)
            short_data = PositionData(quantity=qty, avg_price=avg)
        else:
            long_data = PositionData(quantity=0.0, avg_price=0.0)
            short_data = PositionData(quantity=0.0, avg_price=0.0)

        position = Position(
            symbol=symbol,
            long=long_data,
            short=short_data,
            updated_time=updated_time
        )


        active_order = ActiveOrder(
            symbol=symbol,
            exchange=exchange,
            updated_time=updated_time,
            created_time=created_time,
            exchange_order_id=exchange_order_id,
            client_order_id=client_order_id,
            position=position,
            filled_size=filled_qty,
            remain_size=remain_qty,
        )

        return active_order

    def convert_rest_order_to_order_history(self, order: dict) -> OrderHistory:
        """
        Convert a single order dict from Bybit REST API into an OrderHistory instance.
        """
        # Symbol
        raw_symbol = order.get("symbol")
        try:
            symbol_val = Symbol(raw_symbol)
        except Exception:
            symbol_val = raw_symbol

        # IDs
        client_order_id = str(order.get("orderId"))

        # Side
        raw_side = order.get("side")
        try:
            side_val = OrderSide(raw_side.upper())
        except:
            side_val = raw_side

        # Status
        status_out = parse_order_status(order.get("orderStatus"))

        # Sizes
        qty = float(order.get("qty", 0.0))
        cum_exec_qty = float(order.get("cumExecQty", 0.0))
        leaves_qty = qty - cum_exec_qty  # Calculated manually as requested

        return OrderHistory(
            client_order_id=client_order_id,
            symbol=symbol_val,
            side=side_val,
            qty=qty,
            cumExecQty=cum_exec_qty,
            leavesQty=leaves_qty,
            orderStatus=status_out
        )

    def parse_order_response(self, response: dict) -> OrderResponse:
        return OrderResponse(
            exchange_order_id="",
            client_order_id=response["result"].get("orderId")
        )
