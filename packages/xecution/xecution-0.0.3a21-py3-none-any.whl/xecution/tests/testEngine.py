import asyncio
import sys


if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
else:
    sys.path.append("/Users/kaihock/Desktop/All In/Xecution")
import asyncio
from pathlib import Path
from urllib.parse import parse_qs
import pandas as pd
import logging
from xecution.core.engine import BaseEngine
from xecution.common.enums import DataProvider, Exchange, KlineType, Mode, OrderSide, OrderStatus, OrderType, Symbol, TimeInForce
from xecution.models.config import OrderConfig, RuntimeConfig
from xecution.models.topic import DataTopic, KlineTopic
from xecution.utils.logger import Logger
from xecution.models.order import OrderUpdate
from xecution.utils.utility import (
    to_camel,
    write_csv_overwrite,
    normalize_interval,
    qualifier_suffix,
    _provider_title
)
import numpy as np

# --------------------------------------------------------------------
candle_path1 = Path("data/candle/binance_kline_btc_1h.csv") # candle data file path
# --------------------------------------------------------------------

DATASOURCE_PATH = Path("data/datasource")
CANDLE_PATH = Path("data/candle")
KLINE_FUTURES = KlineTopic(klineType=KlineType.Bybit_Futures, symbol=Symbol.BTCUSDT, timeframe="5m")
KLINE_SPOT = KlineTopic(klineType=KlineType.Binance_Spot, symbol=Symbol.BTCUSDT, timeframe="1h")
BINANCE_FUTURES = KlineTopic(klineType=KlineType.Binance_Futures, symbol=Symbol.BTCUSDT, timeframe="1h")

BC_FDR  = DataTopic(provider=DataProvider.CRYPTOQUANT, url='btc/market-data/funding-rates?window=hour&exchange=binance')
BC_EWR = DataTopic(provider=DataProvider.CRYPTOQUANT, url='btc/flow-indicator/exchange-whale-ratio?exchange=binance&window=hour')
RX_CPG = DataTopic(provider=DataProvider.REXILION, url='btc/market-data/coinbase-premium-gap?window=1h')
BG_BC2 = DataTopic(provider=DataProvider.GLASSNODE, url='blockchain/block_height?a=BTC&i=1h')
BG_AD11 = DataTopic(provider=DataProvider.GLASSNODE, url='addresses/new_non_zero_count?a=BTC&i=1h')
BG_AD19 = DataTopic(provider=DataProvider.GLASSNODE, url='addresses/sending_to_exchanges_count?a=BTC&i=1h')
BG_BC7 = DataTopic(provider=DataProvider.GLASSNODE, url='blockchain/utxo_count?a=BTC&i=1h')
BG_BC12 = DataTopic(provider=DataProvider.GLASSNODE, url='blockchain/utxo_loss_count?a=BTC&i=1h')
BG_ID154 = DataTopic(provider=DataProvider.GLASSNODE, url='indicators/velocity?a=BTC&i=1h')
BG_MN10 = DataTopic(provider=DataProvider.GLASSNODE, url='mining/volume_mined_sum?a=BTC&i=1h')
BG_ID151 = DataTopic(provider=DataProvider.GLASSNODE, url='indicators/unrealized_profit?a=BTC&i=1h')

D_0 = [RX_CPG, BC_FDR]
D_10M_70M = [BG_BC2, BG_AD11]
D_15M_75M_135M = [BG_BC7, BG_ID154]
D_20M_80M_140M = [BG_AD19, BG_MN10]
D_25M = [BG_ID151]
D_30M = [BG_BC12]
D_57M = [BC_EWR]

delay_list = {0:D_0,
              7:D_10M_70M,
              12:D_15M_75M_135M,
              17:D_20M_80M_140M,
              22:D_25M,
              27:D_30M,
              57:D_57M,}

def _build_datatopic_name_map():
    out = {}
    for name, obj in globals().items():
        if isinstance(obj, DataTopic):
            url = getattr(obj, "url", None)
            if url:
                out[url] = name
    return out

DATATOPIC_NAME_MAP = _build_datatopic_name_map()


# Enable logging to see real-time data
class Engine(BaseEngine):
    """Base engine that initializes BinanceService and processes on_candle_closed and on_datasource_update."""
    def __init__(self, config):
        Logger(log_file="data_retrieval.log", log_level=logging.INFO)
        super().__init__(config)

    async def on_datasource_update(self, datasource_topic):
        data = self.data_map.get(datasource_topic, [])

        url = getattr(datasource_topic, "url", None)
        const_name = DATATOPIC_NAME_MAP.get(url, "UNKNOWN")

        logging.info("%s-Data Incoming: %s (len=%d)", const_name, datasource_topic, len(data))


    async def on_candle_closed(self, kline_topic):
        self.candles = self.data_map[kline_topic]
        candle = np.array(list(map(lambda c: float(c["close"]), self.candles)))        
        logging.info(
            f"Last Kline Closed | {kline_topic.symbol}-{kline_topic.timeframe} | Close: {candle[-1]}"
        )

engine = Engine(
    RuntimeConfig(
        mode= Mode.Live,
        kline_topic=[
            KLINE_FUTURES,
            # KLINE_SPOT,
            # BINANCE_FUTURES
        ],
        datasource_topic=[*D_0, *D_10M_70M, *D_15M_75M_135M, *D_20M_80M_140M, *D_25M, *D_30M, *D_57M],
        kline_count=3000,
        data_count=3000,
        exchange=Exchange.Bybit,
        API_Key="HIrzahO7vyIm25n7nQ",
        API_Secret="FA2nFBsAzWFTBAZH2Q9UfK51ImgAybdasgQT",
        cryptoquant_api_key="iG48lac3kRFcFq0q5WMm0BpnTt1XYMvRB6yz63OP",
        glassnode_api_key="37EPBGoElObddHGIQa0vXD0DqBh",
        rexilion_api_key="rexilion-api-key-2025",
        datasource_live_delay_groups_min=delay_list,
        max_dd=0.2,
    )
)

asyncio.run(engine.start())

