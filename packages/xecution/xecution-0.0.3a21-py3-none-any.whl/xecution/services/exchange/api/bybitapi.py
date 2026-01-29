import hashlib
import hmac
import logging
import time
from urllib.parse import urlencode
from ...connection.restapi import RestAPIClient  # Note import path

logger = logging.getLogger(__name__)

class BybitAPIClient(RestAPIClient):
    """
    API client specifically for Bybit (v5-style auth).
    - Override `request` with auth=True to add signing.
    """
    def __init__(self, api_key: str = None, api_secret: str = None):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret

    async def request(self, method: str, url: str, params: dict = {}, auth: bool = False, timestamp: int = None):
        """
        Override request() to include Bybit-specific headers and signature when `auth=True`.
        - GET  : sign the query string and append it to URL.
        - POST/PUT/DELETE : sign the FORM BODY and send as x-www-form-urlencoded.
        """
        try:
            if not auth:
                # Non-authenticated request
                return await super().request(method, url, params=params)

            method = method.upper()
            p = {k: str(v) for k, v in (params or {}).items()}  # Bybit expects strings
            timestamp = str(timestamp) or str(int(time.time() * 1000))
            recv_window = "5000"

            if method == "GET":
                query_string = urlencode(sorted(p.items()))
                prehash = f"{timestamp}{self.api_key}{recv_window}{query_string}"
                signature = hmac.new(self.api_secret.encode(), prehash.encode(), hashlib.sha256).hexdigest()
                full_url = f"{url}?{query_string}" if query_string else url
                headers = {
                    "X-BAPI-API-KEY": self.api_key,
                    "X-BAPI-TIMESTAMP": timestamp,
                    "X-BAPI-RECV-WINDOW": recv_window,
                    "X-BAPI-SIGN": signature,
                    "X-BAPI-SIGN-TYPE": "2",
                }
                return await super().signed_request(method, full_url, headers)

            # POST/PUT/DELETE → sign the exact body you send
            body_string = urlencode(sorted(p.items()))
            prehash = f"{timestamp}{self.api_key}{recv_window}{body_string}"
            signature = hmac.new(self.api_secret.encode(), prehash.encode(), hashlib.sha256).hexdigest()
            headers = {
                "X-BAPI-API-KEY": self.api_key,
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-RECV-WINDOW": recv_window,
                "X-BAPI-SIGN": signature,
                "X-BAPI-SIGN-TYPE": "2",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            return await super().signed_request(method, url, headers, data=body_string)

        except Exception as e:
            raise Exception(f"[BybitAPIClient] request failed: {e}")

