import asyncio
import logging

class SafeKlineDownloader:
    def __init__(
        self,
        session,
        fetch_func,
        endpoint,
        symbol,
        interval,
        max_limit=1000,
        time_increment_ms=60_000,
        max_concurrent_requests=5,
        chunk_sleep=1.2,
        *,
        # NEW: allow different API param names & extra params (e.g., Bybit category)
        start_key: str = "startTime",
        end_key: str = "endTime",
        extra_params: dict | None = None,
    ):
        self.session = session
        self.fetch_func = fetch_func
        self.endpoint = endpoint
        self.symbol = symbol
        self.interval = interval
        self.max_limit = max_limit
        self.time_increment = time_increment_ms
        self.max_concurrent_requests = max_concurrent_requests
        self.chunk_sleep = chunk_sleep
        self.start_key = start_key
        self.end_key = end_key
        self.extra_params = extra_params or {}

    async def fetch_with_retry(self, params, retries=3):
        for attempt in range(retries):
            try:
                data = await self.fetch_func(self.session, self.endpoint, params)
                # Binance rate-limit {code:-1003,...}; keep original behavior
                if isinstance(data, dict) and data.get("code") == -1003:
                    logging.warning(f"❌ Rate limited: {data.get('msg')}")
                    await asyncio.sleep(60 + attempt * 10)
                    continue
                return data
            except Exception as e:
                logging.warning(f"⚠️ Fetch attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2 ** attempt)
        raise Exception("Exceeded retry limit")

    async def download(self, start_time: int, total_needed: int = 1000):
        num_batches = -(-total_needed // self.max_limit)  # ceiling division
        requests = []
        for i in range(num_batches):
            p = {
                "symbol": self.symbol,
                "interval": self.interval,
                "limit": min(self.max_limit, total_needed - i * self.max_limit),
                self.start_key: start_time + i * self.max_limit * self.time_increment,
            }
            if self.extra_params:
                p.update(self.extra_params)
            requests.append(p)

        total_data = []
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        async def safe_fetch(p):
            async with semaphore:
                return await self.fetch_with_retry(p)

        for i in range(0, len(requests), self.max_concurrent_requests):
            chunk = requests[i:i + self.max_concurrent_requests]
            results = await asyncio.gather(*[safe_fetch(p) for p in chunk])
            for batch in results:
                if batch:
                    total_data.extend(batch)
            logging.debug(f"已完成第 {i // self.max_concurrent_requests + 1} 輪，共累積 {len(total_data)} 筆")
            await asyncio.sleep(self.chunk_sleep)

        return total_data

    async def download_reverse(self, end_time: int, total_needed: int = 1000):
        """
        從最新時間開始，向過去拉 total_needed 筆資料
        使用 endTime/startKey 向前翻頁
        """
        total_data = []

        # First request
        params = {
            "symbol": self.symbol,
            "interval": self.interval,
            "limit": min(self.max_limit, total_needed),
            self.end_key: end_time
        }
        if self.extra_params:
            params.update(self.extra_params)

        batch = await self.fetch_with_retry(params)
        if not batch:
            return total_data

        total_data.extend(batch)
        earliest_open_time = int(batch[0][0])  # cast to int in case API returns string

        while len(total_data) < total_needed:
            remaining = total_needed - len(total_data)
            limit = min(self.max_limit, remaining)
            params = {
                "symbol": self.symbol,
                "interval": self.interval,
                "limit": limit,
                self.end_key: int(earliest_open_time) - 1,  # ensure int math
            }
            if self.extra_params:
                params.update(self.extra_params)

            batch = await self.fetch_with_retry(params)
            if not batch:
                break

            total_data = batch + total_data
            earliest_open_time = int(batch[0][0])  # keep it int each loop
            await asyncio.sleep(self.chunk_sleep)

        logging.debug(f"Retrieved {len(total_data)} {self.symbol} historical data")
        return total_data
