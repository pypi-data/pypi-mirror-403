import logging
import time
from xecution.common.enums import KlineType, Mode, OrderType, Symbol
from xecution.common.exchange.live_constants import LiveConstants
from xecution.common.exchange.testnet_constants import TestnetConstants
from xecution.models.config import OrderConfig
from xecution.services.exchange.standardize import Standardize
from xecution.services.exchange.api.binanceapi import BinanceAPIClient
from xecution.services.exchange.api.bybitapi import BybitAPIClient
from xecution.services.exchange.api.okxapi import OkxAPIClient
from xecution.services.exchange.base_order_manager import BaseOrderManager, ExchangeErrorType, StandardizedError, RetryConfig, RateLimitConfig

# Implementation of BinanceOrderManager (supports spot and futures)
class BinanceOrderManager(BaseOrderManager):
    def __init__(self, api_key: str, api_secret: str, market_type: KlineType = KlineType.Binance_Futures, mode: Mode = Mode.Live):
        super().__init__(api_key, api_secret)
        self.market_type = market_type
        self.mode = mode
        # Select Live or Testnet
        base = LiveConstants.Binance if mode == Mode.Live else TestnetConstants.Binance
        self.binanceApiClient = BinanceAPIClient(api_key=api_key, api_secret=api_secret)
        # Choose Spot or Futures URL
        self.rest_url = (
            base.RESTAPI_SPOT_URL if self.market_type == KlineType.Binance_Spot
            else base.RESTAPI_FUTURES_URL
        )
    
    async def set_leverage(self, symbol: Symbol, leverage: int):
        if self.market_type == KlineType.Binance_Spot:
            return None
        endpoint = "/v1/leverage"
        url = self.rest_url + endpoint
        payload = {
            "symbol": symbol.value.lower(),
            "leverage": int(leverage),
        }
        try:
            response = await self.binanceApiClient.request(
                method="POST",
                url=url,
                params=payload,
                auth=True,
                timestamp = await self.get_server_time()
            )
            logging.info(f"[BinanceOrderManager] set_leverage response: {response}")
            return response
        except Exception as e:
            logging.error(f"[BinanceOrderManager] set_leverage - Failed to set leverage for {symbol}: {e}")
            return None
        
    async def set_hedge_mode(self, is_hedge_mode: bool):
        if self.market_type == KlineType.Binance_Spot:
            return None
        endpoint = "/v1/positionSide/dual"
        url = self.rest_url + endpoint
        payload = {
            "dualSidePosition": bool(is_hedge_mode),
        }
        try:
            response = await self.binanceApiClient.request(
                method="POST",
                url=url,
                params=payload,
                auth=True,
                timestamp = await self.get_server_time()
            )
            logging.info(f"[BinanceOrderManager] set_hedge_mode response: {response}")
            return response
        except Exception as e:
            logging.error(f"[BinanceOrderManager] set_hedge_mode - Failed to set hedge mode to {is_hedge_mode}: {e}")
            return None

    async def get_exchange_info(self):
        # Spot uses /api/v3/exchangeInfo; Futures uses /fapi/v1/exchangeInfo
        endpoint = "/v3/exchangeInfo" if self.market_type == KlineType.Binance_Spot else "/v1/exchangeInfo"
        url = self.rest_url + endpoint
        try:
            async with self.session.get(url) as response:
                data = await response.json()
                if response.status != 200:
                    raise Exception(f"Error getting exchange info: {data}")
                return data
        except Exception as e:
            logging.error(f"[BinanceOrderManager] get_exchange_info - Error fetching exchange info: {e}")
            return None

    async def get_open_orders(self):
        # Spot: /api/v3/openOrders; Futures: /fapi/v1/openOrders
        endpoint = "/v3/openOrders" if self.market_type == KlineType.Binance_Spot else "/v1/openOrders"
        url = self.rest_url + endpoint
        try:
            response = await self.binanceApiClient.request(
                method="GET",
                url=url,
                auth=True,
                timestamp = await self.get_server_time()
                
            )
            return response
        except Exception as e:
            logging.error(f"[BinanceOrderManager] get_open_orders - Failed to fetch open orders: {e}")
            return None

    async def get_account_info(self):
        # Spot: /api/v3/account; Futures: /fapi/v2/account
        endpoint = "/v3/account" if self.market_type == KlineType.Binance_Spot else "/v2/account"
        url = self.rest_url + endpoint
        try:
            response = await self.binanceApiClient.request(
                method="GET",
                url=url,
                auth=True,
                timestamp = await self.get_server_time()
            )
            return response
        except Exception as e:
            logging.error(f"[BinanceOrderManager] get_account_info - Failed to fetch account info: {e}")
            return None
        
    async def get_wallet_balance(self) -> float:
        """Return the available USDT balance for spot or futures account."""
        account_info = await self.get_account_info()
        if account_info is None:
            return None
        try:
            if self.market_type == KlineType.Binance_Spot:
                # Spot: find USDT entry in balances and return `free` field
                balances = account_info.get("balances", [])
                usdt_balance = next((b for b in balances if b.get("asset") == "USDT"), None)
                if usdt_balance:
                    available = usdt_balance.get("free", "0")
                    logging.debug(f"[BinanceOrderManager] Spot USDT available balance: {available}")
                    return float(available)
                logging.error("[BinanceOrderManager] USDT not found in spot balances.")
                return 0.0
            else:
                # Futures: find USDT entry in assets and return `walletBalance`
                assets = account_info.get("assets", [])
                usdt_asset = next((a for a in assets if a.get("asset") == "USDT"), None)
                if usdt_asset:
                    available = usdt_asset.get("walletBalance")
                    logging.debug(f"[BinanceOrderManager] Futures USDT available balance: {available}")
                    return float(available)
                logging.error("[BinanceOrderManager] USDT not found in futures assets.")
                return 0.0
        except Exception as e:
            logging.error(f"[BinanceOrderManager] get_wallet_balance - Error retrieving USDT balance: {e}")
            return 0.0

    async def get_position_info(self, symbol: Symbol):
        # Spot has no position info; Futures uses /fapi/v2/positionRisk
        if self.market_type == KlineType.Binance_Spot:
            return []
        else:
            endpoint = "/v2/positionRisk"
            url = self.rest_url + endpoint
            params = {"symbol": symbol.value}
            try:
                response = await self.binanceApiClient.request(
                    method="GET",
                    url=url,
                    params=params,
                    auth=True,
                    timestamp = await self.get_server_time()
                )
                logging.debug(f"[BinanceOrderManager] get_position response: {response}")
                parsed = Standardize.parse_binance_position(response)
                logging.debug(f"[BinanceOrderManager] Parsed positions: {parsed}")
                return parsed
            except Exception as e:
                logging.error(f"[BinanceOrderManager] get_position_info - Error for {symbol}: {e}")
                return None
                
    async def get_current_price(self, symbol: Symbol) -> float:
        # Spot: /api/v3/ticker/price; Futures: /fapi/v1/ticker/price
        endpoint = "/v3/ticker/price" if self.market_type == KlineType.Binance_Spot else "/v1/ticker/price"
        url = self.rest_url + endpoint
        params = {"symbol": symbol.value.upper()}
        try:
            response = await self.binanceApiClient.request(
                method="GET",
                url=url,
                params=params,
                auth=True,
                timestamp = await self.get_server_time()
            )
            # Expected response: {"symbol": "BTCUSDT", "price": "12345.67"}
            price = response.get("price")
            logging.info(f"[BinanceOrderManager] get_current_price: {price}")
            return float(price) if price is not None else 0.0
        except Exception as e:
            logging.error(f"[BinanceOrderManager] get_current_price - Error fetching price: {e}")
            return 0.0
            
    async def place_order(self, order_config: OrderConfig) -> dict:
        # Order endpoint: Spot /api/v3/order; Futures /fapi/v1/order
        endpoint = "/v3/order" if self.market_type == KlineType.Binance_Spot else "/v1/order"
        url = self.rest_url + endpoint
        params = {
            "symbol": order_config.symbol.value.upper(),
            "side": order_config.side.value.upper(),
            "type": order_config.order_type.value.upper(),
            "quantity": order_config.quantity,
        }
        if order_config.order_type == OrderType.LIMIT:
            params["price"] = order_config.price
            params["timeInForce"] = order_config.time_in_force.value.upper()
        try:
            response = await self.binanceApiClient.request(
                method="POST",
                url=url,
                params=params,
                auth=True,
                timestamp = await self.get_server_time()
            )
            logging.info(f"[BinanceOrderManager] Order placed for {order_config.symbol}. Response: {response}")
            return response
        except Exception as e:
            logging.error(f"[BinanceOrderManager] place_order - Error: {e}")
            return None
    
    async def get_order_book(self, symbol: Symbol = Symbol.BTCUSDT, limit: int = 5):
        # Spot: /api/v3/depth; Futures: /fapi/v1/depth
        endpoint = "/v3/depth" if self.market_type == KlineType.Binance_Spot else "/v1/depth"
        url = self.rest_url + endpoint
        try:
            params = {'symbol': symbol.value, 'limit': limit}
            response = await self.binanceApiClient.request(
                method="GET",
                url=url,
                params=params,
                auth=True,
                timestamp = await self.get_server_time()
            )
            return response
        except Exception as e:
            logging.error(f"[BinanceOrderManager] get_order_book - Error fetching order book: {e}")
            return None
    
    async def cancel_order(self, symbol: Symbol, client_order_id: str):
        endpoint = "/v3/order" if self.market_type == KlineType.Binance_Spot else "/v1/order"
        url = self.rest_url + endpoint
        params = {
            "symbol": symbol.value.upper(),
            "origClientOrderId": client_order_id
        }
        try:
            response = await self.binanceApiClient.request(
                method="DELETE",
                url=url,
                params=params,
                auth=True,
                timestamp = await self.get_server_time()
            )
            return response
        except Exception as e:
            logging.error(f"[BinanceOrderManager] cancel_order - Error cancelling order: {e}")
            return None

    async def get_order_history(self, symbol: Symbol = None, order_id: str = None, limit: int = 50):
        """
        Fetch order history. 
        If order_id is provided, fetches that specific order.
        Otherwise fetches recent orders.
        """
        try:
            timestamp = await self.get_server_time()
            if order_id:
                # Fetch single order
                endpoint = "/v3/order" if self.market_type == KlineType.Binance_Spot else "/v1/order"
                url = self.rest_url + endpoint
                params = {
                    "orderId": order_id
                }
                if symbol:
                    params["symbol"] = symbol.value.upper()
                response = await self.binanceApiClient.request(
                    method="GET",
                    url=url,
                    params=params,
                    auth=True,
                    timestamp=timestamp
                )
                # Return as list for consistency
                return [response] if response else []
            else:
                # Fetch all orders (history)
                endpoint = "/v3/allOrders" if self.market_type == KlineType.Binance_Spot else "/v1/allOrders"
                url = self.rest_url + endpoint
                params = {
                    "symbol": symbol.value.upper(),
                    "limit": limit
                }
                response = await self.binanceApiClient.request(
                    method="GET",
                    url=url,
                    params=params,
                    auth=True,
                    timestamp=timestamp
                )
                return response
        except Exception as e:
            logging.error(f"[BinanceOrderManager] get_order_history - Error: {e}")
            return []
    
    async def get_listen_key(self):
        # Spot: /api/v3/userDataStream; Futures: /fapi/v1/listenKey
        endpoint = "/v3/userDataStream" if self.market_type == KlineType.Binance_Spot else "/v1/listenKey"
        url = self.rest_url + endpoint
        try:
            response = await self.binanceApiClient.request(
                method="POST",
                url=url,
                auth=True,
                timestamp = await self.get_server_time()
            )
            return response
        except Exception as e:
            logging.error(f"[BinanceOrderManager] get_listen_key - Error fetching listenKey: {e}")
            return None
        
    async def keepalive_listen_key(self, listen_key):
        # Spot: /api/v3/userDataStream; Futures: /fapi/v1/listenKey
        endpoint = "/v3/userDataStream" if self.market_type == KlineType.Binance_Spot else "/v1/listenKey"
        url = self.rest_url + endpoint
        params = {"listenKey": listen_key}
        try:
            response = await self.binanceApiClient.request(
                method="PUT",
                url=url,
                params=params,
                auth=True,
                timestamp = await self.get_server_time()
            )
            logging.debug(f"[BinanceOrderManager] keepalive_listen_key response: {response}")
            return response
        except Exception as e:
            logging.error(f"[BinanceOrderManager] keepalive_listen_key - Error keeping listenKey alive: {e}")
            return None
    
    async def get_server_time(self) -> int:
        """Get Binance server timestamp in milliseconds"""
        endpoint = "/v1/time"
        url = self.rest_url + endpoint
        try:
            response = await self.binanceApiClient.request(
                method="GET",
                url=url,
                auth=False
            )
            if "serverTime" in response:
                return int(response["serverTime"])
            else:
                logging.warning(f"[BinanceOrderManager] get_server_time failed: {response}")
                return int(time.time() * 1000)  # Fallback to local time
        except Exception as e:
            logging.error(f"[BinanceOrderManager] get_server_time error: {e}")
            return int(time.time() * 1000)  # Fallback to local time

    def standardize_error(self, raw_error: Exception, response: dict = None) -> StandardizedError:
        """Convert Binance-specific errors to standardized errors."""
        error_message = str(raw_error)
        error_type = ExchangeErrorType.UNKNOWN_ERROR

        # Basic error handling - can be expanded later
        if "timeout" in error_message.lower() or "connection" in error_message.lower():
            error_type = ExchangeErrorType.NETWORK_ERROR
        elif "429" in error_message or "rate limit" in error_message.lower():
            error_type = ExchangeErrorType.RATE_LIMIT_EXCEEDED

        return StandardizedError(
            error_type=error_type,
            message=error_message,
            original_error=raw_error
        )

    def get_base_url(self, is_testnet: bool = False) -> str:
        """Get Binance base URL."""
        if is_testnet:
            return "https://testnet.binance.vision"
        else:
            return "https://api.binance.com"

    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for Binance (usually just uppercase)."""
        return symbol.upper()


# Skeleton implementations for other exchanges (implement as needed)
class BybitOrderManager(BaseOrderManager):
    def __init__(self, api_key: str, api_secret: str, market_type: KlineType = KlineType.Bybit_Futures, mode: Mode = Mode.Live):
        super().__init__(api_key, api_secret)
        self.market_type = market_type
        self.mode = mode
        base = LiveConstants.Bybit if mode == Mode.Live else TestnetConstants.Bybit
        self.bybitApiClient = BybitAPIClient(api_key=api_key, api_secret=api_secret)
        self.rest_url = base.RESTAPI_URL
        self.category = "spot" if self.market_type == KlineType.Bybit_Spot else "linear"

    async def set_leverage(self, symbol: Symbol, leverage: int):
        if self.category == "spot":
            return None
        url = self.rest_url + "/v5/position/set-leverage"
        payload = {
            "category": self.category,
            "symbol": symbol.value.upper(),
            "buyLeverage": str(int(leverage)),
            "sellLeverage": str(int(leverage)),
        }
        try:
            resp = await self.bybitApiClient.request("POST", url, params=payload, auth=True,timestamp = await self.get_server_time())
            logging.info(f"[BybitOrderManager] set_leverage response: {resp}")
            return resp
        except Exception as e:
            logging.error(f"[BybitOrderManager] set_leverage - Failed to set leverage for {symbol}: {e}")
            return None

    async def set_hedge_mode(self, is_hedge_mode: bool, symbol: Symbol | None = None):
        if self.category == "spot":
            return None
        url = self.rest_url + "/v5/position/switch-mode"
        payload = {
            "category": self.category,
            # === FIX: Bybit key is 'positionMode', not 'mode' ===
            "positionMode": "BothSide" if is_hedge_mode else "MergedSingle",
        }
        # === FIX: Bybit expects symbol here (safer to include) ===
        if symbol:
            payload["symbol"] = symbol.value.upper()

        try:
            resp = await self.bybitApiClient.request("POST", url, params=payload, auth=True,timestamp = await self.get_server_time())
            logging.info(f"[BybitOrderManager] set_hedge_mode response: {resp}")
            return resp
        except Exception as e:
            logging.error(f"[BybitOrderManager] set_hedge_mode - Failed to set hedge mode to {is_hedge_mode}: {e}")
            return None

    async def get_exchange_info(self):
        url = self.rest_url + "/v5/market/instruments-info"
        params = {"category": self.category}
        try:
            resp = await self.bybitApiClient.request("GET", url, params=params, auth=False,timestamp = await self.get_server_time())
            return resp
        except Exception as e:
            logging.error(f"[BybitOrderManager] get_exchange_info - Error: {e}")
            return None

    async def get_open_orders(self, symbol: str | None = None, settle_coin: str = "USDT", limit: int = 50):
        """
        Fetch open orders.
        - For linear/inverse: include settleCoin (default USDT).
        - For spot: settleCoin is ignored by the API.
        - Set openOnly=1 to return only currently open orders.
        """
        url = self.rest_url + "/v5/order/realtime"
        params = {
            "category": self.category,     # "linear" | "inverse" | "spot" | "option"
            "openOnly": "0",               # only open orders
            "limit": str(limit),
        }
        if symbol:
            params["symbol"] = symbol.upper()
        if self.category in ("linear", "inverse"):
            params["settleCoin"] = settle_coin.upper()

        try:
            resp = await self.bybitApiClient.request("GET", url, params=params, auth=True,timestamp = await self.get_server_time())
            return resp
        except Exception as e:
            logging.error(f"[BybitOrderManager] get_open_orders - Failed to fetch open orders: {e}")
            return None

    async def get_account_info(self):
        url = self.rest_url + "/v5/account/info"
        try:
            resp = await self.bybitApiClient.request("GET", url, auth=True,timestamp = await self.get_server_time())
            return resp
        except Exception as e:
            logging.error(f"[BybitOrderManager] get_account_info - Failed to fetch account info: {e}")
            return None

    async def get_wallet_balance(self) -> float:
        url = self.rest_url + "/v5/account/wallet-balance"
        params = {"accountType": "UNIFIED"}  # adjust if needed
        try:
            resp = await self.bybitApiClient.request("GET", url, params=params, auth=True,timestamp = await self.get_server_time())
            # Expect result.list[0].coin list with {'coin':'USDT','walletBalance':...}
            coins = (((resp or {}).get("result") or {}).get("list") or [{}])[0].get("coin", [])
            usdt = next((c for c in coins if c.get("coin") == "USDT"), None)
            if usdt:
                available = usdt.get("walletBalance", "0")
                logging.debug(f"[BybitOrderManager] USDT available balance: {available}")
                return float(available)
            logging.error("[BybitOrderManager] USDT not found in wallet balance.")
            return 0.0
        except Exception as e:
            logging.error(f"[BybitOrderManager] get_wallet_balance - Error: {e}")
            return 0.0

    async def get_position_info(self, symbol: Symbol):
        if self.category == "spot":
            return []
        url = self.rest_url + "/v5/position/list"
        params = {"category": self.category, "symbol": symbol.value.upper()}
        try:
            resp = await self.bybitApiClient.request("GET", url, params=params, auth=True,timestamp = await self.get_server_time())
            logging.debug(f"[BybitOrderManager] get_position response: {resp}")
            parsed = Standardize.parse_bybit_position(resp)
            logging.debug(f"[BybitOrderManager] Parsed positions: {parsed}")
            return parsed
        except Exception as e:
            logging.error(f"[BybitOrderManager] get_position_info - Error for {symbol}: {e}")
            return None

    async def get_current_price(self, symbol: Symbol) -> float:
        url = self.rest_url + "/v5/market/tickers"
        params = {"category": self.category, "symbol": symbol.value.upper()}
        try:
            resp = await self.bybitApiClient.request("GET", url, params=params, auth=False,timestamp = await self.get_server_time())
            lst = (((resp or {}).get("result") or {}).get("list") or [])
            price = lst[0].get("lastPrice") if lst else None
            logging.info(f"[BybitOrderManager] get_current_price: {price}")
            return float(price) if price is not None else 0.0
        except Exception as e:
            logging.error(f"[BybitOrderManager] get_current_price - Error fetching price: {e}")
            return 0.0

    async def place_order(self, order_config: OrderConfig) -> dict:
        url = self.rest_url + "/v5/order/create"
        params = {
            "category": self.category,
            "symbol": order_config.symbol.value.upper(),
            "side": order_config.side.value.capitalize(),          # "Buy"/"Sell"
            "orderType": order_config.order_type.value.capitalize(),  # "Limit"/"Market"
            "qty": str(order_config.quantity),
        }
        if order_config.order_type == OrderType.LIMIT:
            params["price"] = str(order_config.price)
            params["timeInForce"] = order_config.time_in_force.value  # e.g., "GTC"
        try:
            resp = await self.bybitApiClient.request("POST", url, params=params, auth=True,timestamp = await self.get_server_time())
            logging.info(f"[BybitOrderManager] Order placed for {order_config.symbol}. Response: {resp}")
            return resp
        except Exception as e:
            logging.error(f"[BybitOrderManager] place_order - Error: {e}")
            return None

    async def get_order_book(self, symbol: Symbol = Symbol.BTCUSDT, limit: int = 5):
        url = self.rest_url + "/v5/market/orderbook"
        params = {"category": self.category, "symbol": symbol.value.upper(), "limit": str(limit)}
        try:
            resp = await self.bybitApiClient.request("GET", url, params=params, auth=False,timestamp = await self.get_server_time())
            return resp
        except Exception as e:
            logging.error(f"[BybitOrderManager] get_order_book - Error fetching order book: {e}")
            return None

    async def cancel_order(self, symbol: Symbol, client_order_id: str):
        url = self.rest_url + "/v5/order/cancel"
        params = {
            "category": self.category,
            "symbol": symbol.value.upper(),
            "orderId": client_order_id
        }
        try:
            resp = await self.bybitApiClient.request("POST", url, params=params, auth=True,timestamp = await self.get_server_time())
            return resp
        except Exception as e:
            logging.error(f"[BybitOrderManager] cancel_order - Error cancelling order: {e}")
            return None

    async def get_order_history(self, symbol: Symbol = None, order_id: str = None, limit: int = 50):
        """
        Fetch order history from Bybit.
        """
        url = self.rest_url + "/v5/order/history"
        params = {
            "category": self.category,
            "limit": str(limit),
        }
        if symbol:
            params["symbol"] = symbol.value.upper()
        if order_id:
            params["orderId"] = order_id
            
        try:
            resp = await self.bybitApiClient.request("GET", url, params=params, auth=True, timestamp=await self.get_server_time())
            # Bybit returns {result: {list: [...]}}
            return resp
        except Exception as e:
            logging.error(f"[BybitOrderManager] get_order_history - Error: {e}")
            return None

    async def get_listen_key(self):
        return None

    async def keepalive_listen_key(self, listen_key):
        return None

    async def get_server_time(self) -> int:
        """Get Bybit server timestamp in milliseconds"""
        url = self.rest_url + "/v5/market/time"
        try:
            response = await self.bybitApiClient.request(
                method="GET",
                url=url,
                auth=False
            )
            if response.get("retCode") == 0:
                return int(response["result"]["timeNano"]) // 1000000  # Convert to milliseconds
            else:
                logging.warning(f"[BybitOrderManager] get_server_time failed: {response}")
                return int(time.time() * 1000)  # Fallback to local time
        except Exception as e:
            logging.error(f"[BybitOrderManager] get_server_time error: {e}")
            return int(time.time() * 1000)  # Fallback to local time

    def standardize_error(self, raw_error: Exception, response: dict = None) -> StandardizedError:
        """Convert Bybit-specific errors to standardized errors."""
        error_message = str(raw_error)

        # Default values
        error_type = ExchangeErrorType.UNKNOWN_ERROR
        retry_after = None

        # Handle HTTP/Network errors
        if "timeout" in error_message.lower() or "connection" in error_message.lower():
            error_type = ExchangeErrorType.NETWORK_ERROR
        elif "429" in error_message or "rate limit" in error_message.lower():
            error_type = ExchangeErrorType.RATE_LIMIT_EXCEEDED
            retry_after = 60.0  # Default retry after 1 minute

        # Handle Bybit API response errors
        if response:
            ret_code = response.get("retCode", 0)
            ret_msg = response.get("retMsg", "")

            if ret_code == 10001:  # Invalid API key
                error_type = ExchangeErrorType.INVALID_CREDENTIALS
            elif ret_code == 10003:  # API key expired
                error_type = ExchangeErrorType.INVALID_CREDENTIALS
            elif ret_code == 10004:  # Invalid signature
                error_type = ExchangeErrorType.INVALID_CREDENTIALS
            elif ret_code == 10006:  # Too many requests
                error_type = ExchangeErrorType.RATE_LIMIT_EXCEEDED
                retry_after = 60.0
            elif ret_code == 110001:  # Order does not exist
                error_type = ExchangeErrorType.INVALID_ORDER
            elif ret_code == 110004:  # Insufficient balance
                error_type = ExchangeErrorType.INSUFFICIENT_BALANCE
            elif ret_code == 110007:  # Invalid symbol
                error_type = ExchangeErrorType.INVALID_SYMBOL
            elif 10000 <= ret_code < 20000:  # General API errors
                error_type = ExchangeErrorType.SERVER_ERROR
            elif ret_code >= 20000:  # Trading errors
                error_type = ExchangeErrorType.INVALID_ORDER

            error_message = f"Bybit API Error {ret_code}: {ret_msg}"

        return StandardizedError(
            error_type=error_type,
            message=error_message,
            original_error=raw_error,
            retry_after=retry_after
        )

    def get_base_url(self, is_testnet: bool = False) -> str:
        """Get Bybit base URL."""
        if is_testnet:
            return "https://api-testnet.bybit.com"
        else:
            return "https://api.bybit.com"

    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for Bybit (usually just uppercase)."""
        return symbol.upper()


class OKXOrderManager(BaseOrderManager):
    def __init__(self, api_key: str, api_secret: str, market_type: KlineType = KlineType.OKX_Futures, mode: Mode = Mode.Live):
        super().__init__(api_key, api_secret)
        self.market_type = market_type
        self.mode = mode
        # Select Live or Testnet
        base = LiveConstants.OKX if mode == Mode.Live else TestnetConstants.OKX
        self.okxApiClient = OkxAPIClient(api_key=api_key, api_secret=api_secret)
        # Choose Spot or Futures URL
        self.rest_url = (
            base.RESTAPI_SPOT_URL if self.market_type == KlineType.OKX_Spot
            else base.RESTAPI_FUTURES_URL
        )

    async def get_exchange_info(self):
        pass
    async def get_open_orders(self, symbol: str):
        pass
    async def get_account_info(self):
        pass
    async def get_position_info(self, symbol: str):
        pass
    async def place_order(self, order_config: OrderConfig):
        pass
    async def set_hedge_mode(self, is_hedge_mode):
        pass
    async def set_leverage(self, leverage):
        pass
    async def get_current_price(self, symbol: str):
        """
        Use OKX's /api/v5/market/ticker API to fetch the current price.
        Convert symbol (e.g. "BTCUSDT") to OKX format ("BTC-USDT") before requesting.
        Returns `data[0]['last']` as the current price.
        """
        endpoint = "/api/v5/market/ticker"
        url = self.rest_url + endpoint
        inst_id = symbol[:-4] + "-" + symbol[-4:]
        params = (
            {"instId": inst_id, "instType": "SPOT"}
            if self.market_type == KlineType.OKX_Spot
            else {"instId": inst_id + "-SWAP", "instType": "SWAP"}
        )
        try:
            response = await self.okxApiClient.request(
                method="GET",
                url=url,
                params=params,
                auth=False,  # Public endpoint, no auth required
                timestamp = await self.get_server_time()
            )
            if response.get("code") == "0":
                data = response.get("data", [])
                if data:
                    price = data[0].get("last")
                    logging.info(f"[OKXOrderManager] get_current_price: {price}")
                    return float(price) if price is not None else None
            return None
        except Exception as e:
            logging.error(f"[OKXOrderManager] get_current_price - Error fetching price for {symbol}: {e}")
            return None

    async def get_server_time(self) -> int:
        """Get OKX server timestamp in milliseconds"""
        endpoint = "/api/v5/public/time"
        url = self.rest_url + endpoint
        try:
            response = await self.okxApiClient.request(
                method="GET",
                url=url,
                auth=False
            )
            if response.get("code") == "0" and "data" in response:
                return int(response["data"][0]["ts"])
            else:
                logging.warning(f"[OKXOrderManager] get_server_time failed: {response}")
                return int(time.time() * 1000)  # Fallback to local time
        except Exception as e:
            logging.error(f"[OKXOrderManager] get_server_time error: {e}")
            return int(time.time() * 1000)  # Fallback to local time

    def standardize_error(self, raw_error: Exception, response: dict = None) -> StandardizedError:
        """Convert OKX-specific errors to standardized errors."""
        error_message = str(raw_error)
        error_type = ExchangeErrorType.UNKNOWN_ERROR

        # Basic error handling - can be expanded later
        if "timeout" in error_message.lower() or "connection" in error_message.lower():
            error_type = ExchangeErrorType.NETWORK_ERROR
        elif "429" in error_message or "rate limit" in error_message.lower():
            error_type = ExchangeErrorType.RATE_LIMIT_EXCEEDED

        return StandardizedError(
            error_type=error_type,
            message=error_message,
            original_error=raw_error
        )

    def get_base_url(self, is_testnet: bool = False) -> str:
        """Get OKX base URL."""
        if is_testnet:
            return "https://www.okx.com"  # OKX uses same URL for testnet
        else:
            return "https://www.okx.com"

    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for OKX (convert to dash format like BTC-USDT)."""
        if len(symbol) >= 6 and symbol.endswith("USDT"):
            base = symbol[:-4]
            return f"{base}-USDT"
        return symbol.upper()
