import logging
import asyncio
import socket
import time
from datetime import datetime
from xecution.models.config import RuntimeConfig
from xecution.models.topic import DataTopic
from xecution.common.datasource_constants import RexilionConstants
from xecution.services.connection.restapi import RestAPIClient
from typing import Optional

class RexilionClient:
    """
    Calls endpoints like:
      /v1/btc/market-data/coinbase-premium-gap
    Only supports window & limit. No datetime/start_time parsing, no sorting.
    """
    def __init__(self, config: RuntimeConfig, data_map: dict):
        self.config   = config
        self.data_map = data_map
        self.headers  = {
            "X-API-Key": f"{self.config.rexilion_api_key}",
        }
        self.max_retries = 3
        self.retry_delays = [1, 2, 5]  # seconds
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_reset_time = 300  # 5 minutes
        self.circuit_breaker_opened_at = None
        self.rest_client = RestAPIClient()

    async def fetch_all(
        self,
        data_topic: DataTopic,
        limit: Optional[int] = None,
    ):
        """
        - If `limit` is provided (and >0), use it.
        - Otherwise, use `self.config.data_count`.
        Returns the raw list (no transforms) and stores it in data_map[data_topic].
        """
        if '?' in data_topic.url:
            path, qs = data_topic.url.split('?', 1)
            base_params = dict(part.split('=', 1) for part in qs.split('&') if '=' in part)
        else:
            path = data_topic.url
            base_params = {}

        # decide limit
        effective_limit = limit if (isinstance(limit, int) and limit > 0) else self.config.data_count

        url = RexilionConstants.BASE_URL + path
        params = {**base_params, "limit": effective_limit}

        # Circuit breaker check with auto-reset
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            current_time = time.time()

            # Set the open time if not already set
            if self.circuit_breaker_opened_at is None:
                self.circuit_breaker_opened_at = current_time
                logging.warning(f"[RexilionClient] Circuit breaker opened. Will reset after {self.circuit_breaker_reset_time}s")

            # Check if enough time has passed to reset
            elif current_time - self.circuit_breaker_opened_at >= self.circuit_breaker_reset_time:
                logging.info(f"[RexilionClient] Circuit breaker reset after {self.circuit_breaker_reset_time}s. Resuming requests.")
                self.circuit_breaker_failures = 0
                self.circuit_breaker_opened_at = None
            else:
                remaining_time = self.circuit_breaker_reset_time - (current_time - self.circuit_breaker_opened_at)
                logging.warning(f"[RexilionClient] Circuit breaker open. Will reset in {remaining_time:.0f}s. Skipping request to {url}")
                self.data_map[data_topic] = []
                return []

        # Check network connectivity first
        if not await self._check_network_connectivity():
            logging.warning(f"[RexilionClient] Network connectivity issue. Skipping request to {url}")
            self.data_map[data_topic] = []
            return []

        # Retry mechanism using RestAPIClient
        for attempt in range(self.max_retries + 1):
            try:
                raw = await self.rest_client.request(
                    method="GET",
                    url=url,
                    params=params,
                    headers=self.headers,
                    timeout=1800
                )

                # Reset circuit breaker on success
                self.circuit_breaker_failures = 0
                self.circuit_breaker_opened_at = None
                break

            except Exception as e:
                if attempt < self.max_retries:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    logging.warning(f"[RexilionClient] Attempt {attempt + 1} failed for {url}: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    # Only increment circuit breaker on final failure
                    self.circuit_breaker_failures += 1
                    logging.error(f"[{datetime.now()}] All retry attempts failed for {url} {params}: {e}")
                    self.data_map[data_topic] = []
                    return []

        # Accept either a plain list or {result:{data:[...]}} shapes.
        result = raw.get("result", raw) if isinstance(raw, dict) else raw
        data   = result.get("data") if isinstance(result, dict) else result
        items  = data if isinstance(data, list) else ([data] if data is not None else [])

        self.data_map[data_topic] = items
        return items

    async def _check_network_connectivity(self) -> bool:
        """Check basic network connectivity by attempting DNS resolution."""
        try:
            # Try to resolve the hostname
            socket.gethostbyname("api.rexilion.com")
            return True
        except (socket.gaierror, OSError):
            return False


