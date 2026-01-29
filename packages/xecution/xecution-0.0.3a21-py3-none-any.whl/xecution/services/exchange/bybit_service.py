import time, hmac, hashlib, logging, asyncio
from typing import Optional, List
from xecution.models.order import ActiveOrder, OrderHistory
from xecution.models.config import RuntimeConfig, OrderConfig
from xecution.models.topic import KlineTopic
from xecution.services.connection.base_websockets import WebSocketService
from xecution.services.exchange.bybit_helper import BybitHelper
from xecution.common.enums import Mode, Symbol
from xecution.services.exchange.exchange_order_manager import BybitOrderManager

class BybitService:

    def __init__(self, config: RuntimeConfig, data_map: dict):
        self.config = config
        self.ws_service = WebSocketService()
        self.data_map = data_map
        self.bybitHelper = BybitHelper(self.config)
        self.manager = BybitOrderManager(
            api_key=config.API_Key,
            api_secret=config.API_Secret,
            mode=config.mode
        )

    async def check_connection(self):
        account_info = await self.get_account_info()
        if not account_info or account_info.get("retCode", 0) != 0:
            error_msg = (account_info or {}).get("retMsg", "Unknown error")
            logging.error(f"[BybitService] check_connection: API Key validation failed: {error_msg}")
            raise ConnectionError(f"API Key validation failed: {error_msg}")
        logging.info("[BybitService] check_connection: Successfully connected to Bybit")

    async def get_klines(self, kline_topic, on_candle_closed):
        if self.config.mode == Mode.Backtest:
            candles = await self.bybitHelper.getKlineRestAPI(kline_topic)
            self.data_map[kline_topic] = candles
            await on_candle_closed(kline_topic)
        elif self.config.mode in (Mode.Live, Mode.Testnet):
            await self.listen_kline(on_candle_closed, kline_topic)

    async def listen_kline(self, on_candle_closed, kline_topic: KlineTopic):
        try:
            ws_url = self.bybitHelper.get_websocket_base_url(kline_topic, self.config.mode)
            symbol = kline_topic.symbol.value
            interval = self.bybitHelper.timeframe_to_bybit_interval.get(kline_topic.timeframe.lower(), "60")
            topic = f"kline.{interval}.{symbol}"

            self.data_map[kline_topic] = []

            async def message_handler(exchange, message):
                try:
                    if message.get("topic") != topic:
                        return
                    data = message.get("data") or []
                    for item in data:
                        if not item.get("confirm", False):
                            continue

                        recent = await self.bybitHelper.getLatestKline(kline_topic)
                        converted = self.bybitHelper.convert_ws_kline(item)
                        start_ts = converted.get("start_time")
                        end_ts = converted.get("end_time")
                        if any(c["start_time"] == start_ts for c in recent or []):
                            self.data_map[kline_topic] = await self.bybitHelper.getKlineRestAPI(kline_topic, end_ts)
                            logging.debug(
                                f"[{exchange}] Candle closed | "
                                f"{kline_topic.klineType.name}-{kline_topic.symbol}-{kline_topic.timeframe} | "
                                f"Close: {item.get('close')}"
                            )
                            await on_candle_closed(kline_topic)
                except Exception as e:
                    logging.error(f"[BybitService] on_candle_closed failed: {e}")

            sub_msg = {"op": "subscribe", "args": [topic]}
            logging.debug(f"[BybitService] Connecting to WebSocket: {ws_url} | sub: {sub_msg}")
            await self.ws_service.subscribe(topic, ws_url, sub_msg, message_handler)
            logging.info(f"[BybitService] Subscribed to {kline_topic.klineType.name}-{kline_topic.symbol}-{kline_topic.timeframe}")

        except Exception as e:
            logging.error(f"[BybitService] listen_kline failed: {e}")

    async def listen_order_status(self, on_order_update):
        """
        Authenticate to Bybit v5 private WS and subscribe to order updates.
        Sends `auth` first, then `subscribe` to 'order'.
        """
        try:
            ws_url = self.bybitHelper.get_websocket_user_data_base_url(self.config.mode)  # e.g. wss://stream-testnet.bybit.com/v5/private
            topic = "order"

            # === MOD START: build auth + subscribe frames ===
            # Create auth message generator function for dynamic regeneration
            async def generate_auth_messages():
                """Generate fresh auth and subscribe messages."""
                try:
                    expires = await self.manager.get_synchronized_timestamp(safety_margin_ms=2000)
                    logging.debug(f"[BybitService] Generated fresh timestamp: {expires}")
                except Exception as e:
                    logging.warning(f"[BybitService] Failed to get synchronized timestamp: {e}, using fallback")
                    expires = int((time.time() + 2) * 1000)  # Final fallback to local time

                payload = f"GET/realtime{expires}"
                sign = hmac.new(self.manager.api_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

                fresh_auth_msg = {"op": "auth", "args": [self.manager.api_key, expires, sign]}
                fresh_sub_msg = {"op": "subscribe", "args": [topic]}
                return fresh_auth_msg, fresh_sub_msg

            # Generate initial messages
            auth_msg, sub_msg = await generate_auth_messages()
            # === MOD END ===

            async def message_handler(_, message):
                """
                Bybit private WS messages:
                - auth ack: {"op":"auth","success":true}
                - data push: {"topic":"order","data":[{...}, ...]}
                """
                try:
                    # auth acknowledgement
                    if message.get("op") == "auth":
                        if message.get("success") is True:
                            logging.info("[BybitService] WS auth success")
                        else:
                            logging.error(f"[BybitService] WS auth failed: {message}")
                        return

                    # order updates
                    if message.get("topic") == topic:
                        rows = message.get("data") or []
                        for row in rows:
                            try:
                                order = self.bybitHelper.parse_order_update(row, self.config.exchange)
                                await on_order_update(order)
                            except Exception as e:
                                logging.error(f"[BybitService] listen_order_status parse error: {e}")
                        return

                    # (optional) log subscription ack / errors
                    if message.get("op") in ("subscribe", "unsubscribe") and "success" in message:
                        logging.info(f"[BybitService] WS {message.get('op')} ack: {message}")
                except Exception as e:
                    logging.error(f"[BybitService] listen_order_status handler error: {e}")

            # === MOD START: send auth first, then subscribe with dynamic regeneration ===
            await self.ws_service.subscribe(
                "bybit_private_order",
                ws_url,
                [auth_msg, sub_msg],   # Initial messages
                message_handler,
                auth_message_generator=generate_auth_messages  # For reconnects
            )
            # === MOD END ===

        except Exception as e:
            logging.error(f"[BybitService] listen_order_status failed: {e}")

    async def place_order(self, order_config: OrderConfig):
        resp = await self.manager.place_order(order_config)
        return self.bybitHelper.parse_order_response(resp)

    async def get_account_info(self):
        return await self.manager.get_account_info()

    async def get_wallet_balance(self):
        return await self.manager.get_wallet_balance()

    async def set_hedge_mode(self, is_hedge_mode: bool, symbol: Symbol):
        await self.manager.set_hedge_mode(is_hedge_mode, symbol)

    async def set_leverage(self, symbol: Symbol, leverage: int):
        await self.manager.set_leverage(symbol, leverage)

    async def get_position_info(self, symbol: Symbol):
        return await self.manager.get_position_info(symbol)

    async def get_current_price(self, symbol: Symbol):
        return await self.manager.get_current_price(symbol)

    async def get_order_book(self, symbol: Symbol):
        ob = await self.manager.get_order_book(symbol)
        snapshot = self.bybitHelper.parse_order_book(ob)
        logging.debug(f"[BybitService] get_order_book: {snapshot}")
        return snapshot

    async def get_open_orders(self, on_active_order_interval: Optional[ActiveOrder] = None):
        """Fetch all open orders and forward ActiveOrder list to the provided callback."""
        # === MOD START: normalize Bybit open orders payload to list ===
        resp = await self.manager.get_open_orders()
        items = []
        if isinstance(resp, dict):
            items = (((resp.get("result") or {}).get("list")) or [])
        elif isinstance(resp, list):
            items = resp

        active_orders = [self.bybitHelper.convert_order_to_active_order(o) for o in items if isinstance(o, dict)]
        if on_active_order_interval is None:
            return active_orders
        return await on_active_order_interval(active_orders)

    async def cancel_order(self, symbol: Symbol, client_order_id: str):
        return await self.manager.cancel_order(symbol, client_order_id)

    async def get_order_history(self, symbol: Symbol = None, order_id: str = None, limit: int = 50) -> List[OrderHistory]:
        """
        Fetch order history or a specific order.
        Returns a list of OrderHistory objects.
        """
        # Symbol is handled by Manager or API client if needed, or ignored if not required by endpoint.
        # But we accept it in signature to be consistent and to match test calls.
        resp = await self.manager.get_order_history(symbol, order_id, limit)
        
        # Bybit structure: {"result": {"list": [...]}}
        items = []
        if resp:
            items = (((resp.get("result") or {}).get("list")) or [])
            
        return [self.bybitHelper.convert_rest_order_to_order_history(o) for o in items]
