from enum import Enum

class CIEnum(str, Enum):
    """Case-insensitive compare to strings (and tolerant to -/_/spaces)."""
    @staticmethod
    def _norm(s: str) -> str:
        return s.upper().replace("-", "_").replace(" ", "_")

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == self._norm(other)
        return NotImplemented

class KlineType(Enum):
    Binance_Spot = 1
    Binance_Futures = 2
    Bybit_Spot = 3
    Bybit_Futures = 4
    OKX_Spot = 5
    OKX_Futures = 6
    Coinbase_Spot = 7

class Mode(Enum):
    Live = 1
    Backtest = 2
    Testnet = 3
    
class ConcurrentRequest(Enum):
    Max = 3
    Chunk_Size = 5
    
class Exchange(Enum):
    Binance = 1
    Bybit = 2
    Okx = 3    
    
class Symbol(Enum):
    BTCUSDT = "BTCUSDT"
    ETHUSDT = "ETHUSDT"
    SOLUSDT = "SOLUSDT"
    BTCUSD = "BTCUSD"
    
class OrderSide(CIEnum):
    BUY = "BUY"
    SELL = "SELL"
    
class TimeInForce(str, Enum):
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"
    GTX = "GTX"

class OrderStatus(CIEnum):
    NEW              = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED           = "FILLED"
    CANCELED         = "CANCELED"
    REJECTED         = "REJECTED"
    EXPIRED          = "EXPIRED"

class OrderType(CIEnum):
    LIMIT                 = "LIMIT"
    MARKET                = "MARKET"
    STOP                  = "STOP"
    TAKE_PROFIT           = "TAKE_PROFIT"
    TRAILING_STOP_MARKET  = "TRAILING_STOP_MARKET"
    
class TimeInForce(str, Enum):
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"
    GTX = "GTX"
    
class DataProvider(str, Enum):
    CRYPTOQUANT = "CRYPTOQUANT"
    REXILION = "REXILION"
    GLASSNODE = "GLASSNODE"