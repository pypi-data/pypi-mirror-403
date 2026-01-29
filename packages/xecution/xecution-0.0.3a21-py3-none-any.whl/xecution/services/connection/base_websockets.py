import asyncio
import websockets
import json
import logging
import socket
import time
from websockets.exceptions import ConnectionClosed, InvalidMessage, WebSocketException

class WebSocketService:
    def __init__(self):
        self.connections = {}  # Active WebSocket connections
        self.subscriptions = {}  # Subscription data for reconnects
        self.heartbeat_tasks = {}  # Heartbeat tasks for each connection
        self.reconnect_delay = 10  # Initial delay before reconnecting
        
    def _get_ping_config(self, exchange_name, ws_url):
        """Get ping interval and timeout based on exchange and WebSocket URL."""
        if "binance" in exchange_name.lower():
            # Binance Spot: 20 seconds ping interval, 60 seconds timeout
            if "spot" in ws_url or "stream.binance" in ws_url:
                return {"ping_interval": 20, "ping_timeout": 60}
            # Binance Futures: 180 seconds (3 minutes) ping interval, 600 seconds (10 minutes) timeout
            elif "fstream" in ws_url or "futures" in ws_url:
                return {"ping_interval": 180, "ping_timeout": 600}
            else:
                # Default to Spot settings for unknown Binance URLs
                return {"ping_interval": 20, "ping_timeout": 60}
        elif "bybit" in exchange_name.lower():
            # Bybit uses JSON ping-pong, disable websockets library ping
            return {"ping_interval": None, "ping_timeout": None}
        else:
            # Default for other exchanges
            return {"ping_interval": 15, "ping_timeout": 60}

    async def connect(self, exchange_name, ws_url, subscription_message, message_handler, auth_message_generator=None):
        """Establish a WebSocket connection, handle messages, and manage reconnects."""
        attempt = 0
        ping_config = self._get_ping_config(exchange_name, ws_url)

        while True:
            try:
                async with websockets.connect(ws_url, **ping_config) as ws:
                    self.connections[exchange_name] = ws
                    self.subscriptions[exchange_name] = (ws_url, subscription_message, message_handler, auth_message_generator)
                    
                    # Start heartbeat for this connection (only for exchanges that need JSON ping-pong)
                    if "bybit" in exchange_name.lower():
                        await self._start_heartbeat(exchange_name, ws)

                    if subscription_message:
                        messages_to_send = subscription_message

                        # If auth_message_generator is provided, regenerate auth message for reconnects
                        if auth_message_generator and attempt > 0:
                            logging.debug(f"[{exchange_name}] Regenerating auth message for reconnect attempt {attempt}")
                            try:
                                fresh_auth_msg, sub_msg = await auth_message_generator()
                                messages_to_send = [fresh_auth_msg, sub_msg]
                                logging.debug(f"[{exchange_name}] Generated fresh auth message")
                            except Exception as gen_error:
                                logging.error(f"[{exchange_name}] Failed to generate fresh auth: {gen_error}")
                                # Fall back to original messages
                                messages_to_send = subscription_message

                        # Handle both single message and list of messages (for auth + subscribe)
                        if isinstance(messages_to_send, list):
                            for msg in messages_to_send:
                                await ws.send(json.dumps(msg))
                                logging.debug(f"[{exchange_name}] Sent: {msg.get('op', 'unknown')}")
                        else:
                            await ws.send(json.dumps(messages_to_send))

                    logging.info(f"[{exchange_name}] Connected to WebSocket: {ws_url}")

                    async for message in ws:
                        await self._process_message(exchange_name, message, message_handler)
            
            except (ConnectionClosed, asyncio.TimeoutError, OSError, WebSocketException, socket.gaierror) as e:
                self._handle_error(exchange_name, e)
            except Exception as e:
                logging.error(f"[{exchange_name}] Unexpected error: {e}")
            finally:
                # Stop heartbeat when disconnecting (only for exchanges using JSON ping-pong)
                if "bybit" in exchange_name.lower():
                    await self._stop_heartbeat(exchange_name)

            attempt += 1
            await asyncio.sleep(self.reconnect_delay)
            logging.error(f"[{exchange_name}] Reconnect attempt {attempt}, retrying in {self.reconnect_delay}s...")
            
    async def _start_heartbeat(self, exchange_name, ws):
        """Start heartbeat task for the connection."""
        async def heartbeat_loop():
            while exchange_name in self.connections:
                try:
                    await asyncio.sleep(15)  # Bybit recommends 15 seconds
                    if exchange_name in self.connections:
                        ping_msg = {
                            "op": "ping",
                            "req_id": f"heartbeat_{int(time.time())}"
                        }
                        await ws.send(json.dumps(ping_msg))
                        logging.debug(f"[{exchange_name}] Sent ping heartbeat")
                except Exception as e:
                    logging.error(f"[{exchange_name}] Heartbeat failed: {e}")
                    break

        # Create and store heartbeat task
        self.heartbeat_tasks[exchange_name] = asyncio.create_task(heartbeat_loop())

    async def _stop_heartbeat(self, exchange_name):
        """Stop heartbeat task for the connection."""
        if exchange_name in self.heartbeat_tasks:
            task = self.heartbeat_tasks[exchange_name]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self.heartbeat_tasks[exchange_name]
            logging.debug(f"[{exchange_name}] Stopped heartbeat")

    async def _process_message(self, exchange_name, message, message_handler):
        """Process incoming WebSocket messages."""
        try:
            parsed_message = json.loads(message)
            await message_handler(exchange_name, parsed_message)
        except json.JSONDecodeError as e:
            logging.error(f"[{exchange_name}] JSON Decode Error: {e} - Message: {message}")
        except InvalidMessage as e:
            logging.error(f"[{exchange_name}] Invalid WebSocket Message: {e}")

    def _handle_error(self, exchange_name, error):
        """Handles WebSocket errors with appropriate logging."""
        error_type = type(error).__name__

        # More specific error handling
        if isinstance(error, socket.gaierror):
            logging.warning(f"[{exchange_name}] gaierror: {error}. Retrying in {self.reconnect_delay} sec...")
        elif isinstance(error, ConnectionClosed):
            logging.warning(f"[{exchange_name}] {error_type}: {error}. Retrying in {self.reconnect_delay} sec...")
        elif isinstance(error, asyncio.TimeoutError):
            logging.warning(f"[{exchange_name}] Connection timeout. Retrying in {self.reconnect_delay} sec...")
        else:
            logging.warning(f"[{exchange_name}] {error_type}: {error}. Retrying in {self.reconnect_delay} sec...")

    async def subscribe(self, exchange_name, ws_url, subscription_message, message_handler, auth_message_generator=None):
        """Start a WebSocket connection asynchronously."""
        # Create task but don't await - we need this to run in background
        task = asyncio.create_task(self.connect(exchange_name, ws_url, subscription_message, message_handler, auth_message_generator))
        # Give it a moment to establish connection and send initial messages
        await asyncio.sleep(1)
        return task

    async def disconnect(self, exchange_name):
        """Close a WebSocket connection gracefully."""
        if exchange_name in self.connections:
            try:
                # Stop heartbeat first (only for exchanges using JSON ping-pong)
                if "bybit" in exchange_name.lower():
                    await self._stop_heartbeat(exchange_name)
                await self.connections[exchange_name].close()
                logging.info(f"[{exchange_name}] Disconnected from WebSocket.")
            except Exception as e:
                logging.error(f"[{exchange_name}] Error while disconnecting: {e}")
            finally:
                if exchange_name in self.connections:
                    del self.connections[exchange_name]

    async def send_message(self, exchange_name, message):
        """Send a message to an active WebSocket connection."""
        if exchange_name in self.connections:
            try:
                ws = self.connections[exchange_name]
                await ws.send(json.dumps(message))
                logging.debug(f"[{exchange_name}] Sent message: {message.get('op', 'unknown')}")
                return True
            except Exception as e:
                logging.error(f"[{exchange_name}] Failed to send message: {e}")
                return False
        else:
            logging.warning(f"[{exchange_name}] No active connection to send message")
            return False

    async def restart_connection(self, exchange_name):
        """Manually restart a WebSocket connection."""
        if exchange_name in self.subscriptions:
            subscription_data = self.subscriptions[exchange_name]
            if len(subscription_data) == 4:
                ws_url, subscription_message, message_handler, auth_message_generator = subscription_data
            else:
                ws_url, subscription_message, message_handler = subscription_data
                auth_message_generator = None

            logging.info(f"[{exchange_name}] Restarting WebSocket connection...")
            await self.subscribe(exchange_name, ws_url, subscription_message, message_handler, auth_message_generator)
