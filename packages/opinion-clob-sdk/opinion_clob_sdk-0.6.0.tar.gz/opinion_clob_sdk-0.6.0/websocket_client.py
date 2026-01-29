"""
WebSocket client for Opinion CLOB SDK

This module provides WebSocket connectivity for real-time market data and updates.
"""

import json
import logging
import threading
import time
from typing import Optional, Callable, Dict, Any, Set, Tuple
from urllib.parse import urlencode

import websocket

logger = logging.getLogger(__name__)


class WebSocketClient:
    """
    WebSocket client for Opinion CLOB SDK with heartbeat support and event callbacks.
    
    This client maintains a persistent WebSocket connection to the Opinion WebSocket server,
    automatically sending heartbeat messages to keep the connection alive.
    
    Example:
        ```python
        from opinion_clob_sdk import Client, WebSocketClient
        
        client = Client(...)
        ws_client = WebSocketClient(
            apikey='your_api_key',
            wallet_address='0x...',
            on_message=lambda msg: print(f"Received: {msg}"),
            on_open=lambda: print("Connected"),
            on_close=lambda: print("Disconnected"),
            on_error=lambda error: print(f"Error: {error}")
        )
        
        # Connect
        ws_client.connect()
        
        # Keep connection alive (blocking)
        ws_client.run_forever()
        
        # Or run in background thread
        ws_client.start()
        
        # Later, close the connection
        ws_client.close()
        ```
    """
    
    def __init__(
        self,
        apikey: str,
        wallet_address: str,
        ws_url: str = "wss://ws.opinion.trade",
        heartbeat_interval: int = 30,
        on_message: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_open: Optional[Callable[[], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        ping_interval: int = 20,
        ping_timeout: int = 10,
    ):
        """
        Initialize WebSocket client.
        
        Args:
            apikey: API key for authentication
            wallet_address: Wallet address for heartbeat messages
            ws_url: WebSocket server URL (default: wss://ws.opinion.trade)
            heartbeat_interval: Interval in seconds between application-level heartbeat messages (default: 30).
                This sends a JSON message {"action":"HEARTBEAT","wallet_address":"..."} to keep the
                application session alive. This is different from ping_interval which is at the protocol level.
            on_message: Callback function called when a message is received.
                Should accept a dict parameter: on_message(message: dict) -> None
            on_open: Callback function called when connection is opened.
                Should accept no parameters: on_open() -> None
            on_close: Callback function called when connection is closed.
                Should accept no parameters: on_close() -> None
            on_error: Callback function called when an error occurs.
                Should accept an Exception parameter: on_error(error: Exception) -> None
            ping_interval: Interval in seconds between WebSocket protocol-level ping frames (default: 20).
                This is handled automatically by the WebSocket library to detect if the TCP connection is alive.
                This is different from heartbeat_interval which sends application-level messages.
            ping_timeout: Timeout in seconds for WebSocket pong response (default: 10).
                If no pong is received within this time, the connection is considered dead.
        """
        if not apikey:
            raise ValueError("apikey is required")
        if not wallet_address:
            raise ValueError("wallet_address is required")
        
        self.apikey = apikey
        self.wallet_address = wallet_address
        self.ws_url = ws_url
        self.heartbeat_interval = heartbeat_interval
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        
        # Callbacks
        self.on_message_callback = on_message
        self.on_open_callback = on_open
        self.on_close_callback = on_close
        self.on_error_callback = on_error
        
        # Subscription management
        # Map: (channel, market_id) -> callback
        self._subscriptions: Dict[Tuple[str, int], Callable] = {}
        # Track active subscriptions: set of (channel, market_id)
        self._active_subscriptions: Set[Tuple[str, int]] = set()
        
        # Internal state
        self.ws: Optional[websocket.WebSocketApp] = None
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.is_connected = False
        self._stop_event = threading.Event()
        
        # Build WebSocket URL with apikey parameter
        self._build_ws_url()
    
    def _build_ws_url(self) -> None:
        """Build WebSocket URL with apikey query parameter."""
        params = {"apikey": self.apikey}
        query_string = urlencode(params)
        if "?" in self.ws_url:
            self.full_ws_url = f"{self.ws_url}&{query_string}"
        else:
            self.full_ws_url = f"{self.ws_url}?{query_string}"
    
    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        """Internal handler for WebSocket open event."""
        logger.info("WebSocket connection opened")
        self.is_connected = True
        
        # Start heartbeat thread
        if self.heartbeat_interval > 0:
            self._start_heartbeat()
        
        # Call user callback
        if self.on_open_callback:
            try:
                self.on_open_callback()
            except Exception as e:
                logger.error(f"Error in on_open callback: {e}", exc_info=True)
    
    def _on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Internal handler for WebSocket message event."""
        try:
            # Parse JSON message
            data = json.loads(message)
            logger.debug(f"Received message: {data}")
            
            # Try to route to subscription-specific callback
            msg_type = data.get('msgType', '')
            market_id = data.get('marketId')
            root_market_id = data.get('rootMarketId')
            
            if msg_type == 'market.depth.diff' and market_id is not None:
                # Route market depth diff messages to subscription callbacks
                channel = 'market.depth.diff'
                subscription_key = (channel, int(market_id))
                
                # Look for subscription callback
                if subscription_key in self._subscriptions:
                    callback = self._subscriptions[subscription_key]
                    try:
                        # Import model here to avoid circular imports
                        from .websocket_models import MarketDepthDiffMessage
                        
                        # Parse message and call callback
                        parsed_msg = MarketDepthDiffMessage.from_dict(data)
                        callback(parsed_msg)
                    except Exception as e:
                        logger.error(f"Error in subscription callback: {e}", exc_info=True)
            
            elif msg_type == 'market.last.price':
                # Route market last price messages to subscription callbacks
                channel = 'market.last.price'
                # Use marketId if available, otherwise use rootMarketId
                # For categorical markets, use rootMarketId as the key
                if root_market_id is not None:
                    subscription_key = (channel, int(root_market_id))
                elif market_id is not None:
                    subscription_key = (channel, int(market_id))
                else:
                    subscription_key = None
                
                # Look for subscription callback
                if subscription_key and subscription_key in self._subscriptions:
                    callback = self._subscriptions[subscription_key]
                    try:
                        # Import model here to avoid circular imports
                        from .websocket_models import MarketLastPriceMessage
                        
                        # Parse message and call callback
                        parsed_msg = MarketLastPriceMessage.from_dict(data)
                        callback(parsed_msg)
                    except Exception as e:
                        logger.error(f"Error in subscription callback: {e}", exc_info=True)
            
            elif msg_type == 'market.last.trade':
                # Route market last trade messages to subscription callbacks
                channel = 'market.last.trade'
                # Use marketId if available, otherwise use rootMarketId
                # For categorical markets, use rootMarketId as the key
                if root_market_id is not None:
                    subscription_key = (channel, int(root_market_id))
                elif market_id is not None:
                    subscription_key = (channel, int(market_id))
                else:
                    subscription_key = None
                
                # Look for subscription callback
                if subscription_key and subscription_key in self._subscriptions:
                    callback = self._subscriptions[subscription_key]
                    try:
                        # Import model here to avoid circular imports
                        from .websocket_models import MarketLastTradeMessage
                        
                        # Parse message and call callback
                        parsed_msg = MarketLastTradeMessage.from_dict(data)
                        callback(parsed_msg)
                    except Exception as e:
                        logger.error(f"Error in subscription callback: {e}", exc_info=True)
            
            elif msg_type == 'trade.order.update':
                # Route trade order update messages to subscription callbacks
                channel = 'trade.order.update'
                # Use marketId if available, otherwise use rootMarketId
                # For categorical markets, use rootMarketId as the key
                if root_market_id is not None and root_market_id != 0:
                    subscription_key = (channel, int(root_market_id))
                elif market_id is not None:
                    subscription_key = (channel, int(market_id))
                else:
                    subscription_key = None
                
                # Look for subscription callback
                if subscription_key and subscription_key in self._subscriptions:
                    callback = self._subscriptions[subscription_key]
                    try:
                        # Import model here to avoid circular imports
                        from .websocket_models import TradeOrderUpdateMessage
                        
                        # Parse message and call callback
                        parsed_msg = TradeOrderUpdateMessage.from_dict(data)
                        callback(parsed_msg)
                    except Exception as e:
                        logger.error(f"Error in subscription callback: {e}", exc_info=True)
            
            elif msg_type == 'trade.record.new':
                # Route trade record new messages to subscription callbacks
                channel = 'trade.record.new'
                # Use marketId if available, otherwise use rootMarketId
                # For categorical markets, use rootMarketId as the key
                if root_market_id is not None and root_market_id != 0:
                    subscription_key = (channel, int(root_market_id))
                elif market_id is not None:
                    subscription_key = (channel, int(market_id))
                else:
                    subscription_key = None
                
                # Look for subscription callback
                if subscription_key and subscription_key in self._subscriptions:
                    callback = self._subscriptions[subscription_key]
                    try:
                        # Import model here to avoid circular imports
                        from .websocket_models import TradeRecordNewMessage
                        
                        # Parse message and call callback
                        parsed_msg = TradeRecordNewMessage.from_dict(data)
                        callback(parsed_msg)
                    except Exception as e:
                        logger.error(f"Error in subscription callback: {e}", exc_info=True)
            
            # Also call general message callback if provided
            if self.on_message_callback:
                try:
                    self.on_message_callback(data)
                except Exception as e:
                    logger.error(f"Error in on_message callback: {e}", exc_info=True)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message as JSON: {message}, error: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
    
    def _on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        """Internal handler for WebSocket error event."""
        logger.error(f"WebSocket error: {error}", exc_info=True)
        self.is_connected = False
        
        # Call user callback
        if self.on_error_callback:
            try:
                self.on_error_callback(error)
            except Exception as e:
                logger.error(f"Error in on_error callback: {e}", exc_info=True)
    
    def _on_close(self, ws: websocket.WebSocketApp, close_status_code: int, close_msg: str) -> None:
        """Internal handler for WebSocket close event."""
        logger.info(f"WebSocket connection closed: status={close_status_code}, msg={close_msg}")
        self.is_connected = False
        self._stop_heartbeat()
        
        # Call user callback
        if self.on_close_callback:
            try:
                self.on_close_callback()
            except Exception as e:
                logger.error(f"Error in on_close callback: {e}", exc_info=True)
    
    def _send_heartbeat(self) -> None:
        """Send heartbeat message to keep connection alive."""
        if not self.is_connected or not self.ws:
            return
        
        try:
            heartbeat_msg = {
                "action": "HEARTBEAT"
            }
            message = json.dumps(heartbeat_msg)
            self.ws.send(message)
            logger.debug(f"Sent heartbeat: {heartbeat_msg}")
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}", exc_info=True)
    
    def _heartbeat_loop(self) -> None:
        """Heartbeat thread loop."""
        logger.info(f"Heartbeat thread started (interval: {self.heartbeat_interval}s)")
        
        while not self._stop_event.is_set():
            if self._stop_event.wait(self.heartbeat_interval):
                # Event was set, exit loop
                break
            
            if self.is_connected:
                self._send_heartbeat()
        
        logger.info("Heartbeat thread stopped")
    
    def _start_heartbeat(self) -> None:
        """Start heartbeat thread."""
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            return
        
        self._stop_event.clear()
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="WebSocketHeartbeat"
        )
        self.heartbeat_thread.start()
    
    def _stop_heartbeat(self) -> None:
        """Stop heartbeat thread."""
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self._stop_event.set()
            self.heartbeat_thread.join(timeout=5)
    
    def connect(self) -> None:
        """
        Connect to WebSocket server.
        
        This method creates the WebSocket connection but does not start the event loop.
        Use run_forever() or start() to begin processing messages.
        """
        if self.ws is not None:
            logger.warning("WebSocket already initialized. Closing existing connection.")
            self.close()
        
        logger.info(f"Connecting to WebSocket: {self.full_ws_url}")
        
        self.ws = websocket.WebSocketApp(
            self.full_ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
        self.is_running = True
    
    def run_forever(
        self,
        ping_interval: Optional[int] = None,
        ping_timeout: Optional[int] = None,
        **kwargs
    ) -> None:
        """
        Run WebSocket event loop forever (blocking).
        
        This method will block until the connection is closed.
        
        Args:
            ping_interval: Override ping interval (seconds)
            ping_timeout: Override ping timeout (seconds)
            **kwargs: Additional arguments passed to websocket.WebSocketApp.run_forever()
        """
        if self.ws is None:
            raise RuntimeError("WebSocket not initialized. Call connect() first.")
        
        ping_interval = ping_interval or self.ping_interval
        ping_timeout = ping_timeout or self.ping_timeout
        
        logger.info(f"Starting WebSocket event loop (ping_interval={ping_interval}s, ping_timeout={ping_timeout}s)")
        
        try:
            self.ws.run_forever(
                ping_interval=ping_interval,
                ping_timeout=ping_timeout,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error in WebSocket event loop: {e}", exc_info=True)
            raise
        finally:
            self.is_running = False
    
    def start(self) -> None:
        """
        Start WebSocket connection in a background thread (non-blocking).
        
        This method connects and runs the WebSocket event loop in a separate thread,
        allowing your main program to continue execution.
        """
        if self.ws is None:
            self.connect()
        
        def run_in_thread():
            try:
                self.run_forever()
            except Exception as e:
                logger.error(f"Error in WebSocket thread: {e}", exc_info=True)
        
        thread = threading.Thread(
            target=run_in_thread,
            daemon=True,
            name="WebSocketClient"
        )
        thread.start()
        logger.info("WebSocket client started in background thread")
    
    def send(self, message: Dict[str, Any]) -> None:
        """
        Send a message to the WebSocket server.
        
        Args:
            message: Dictionary to send as JSON message
            
        Raises:
            RuntimeError: If WebSocket is not connected
        """
        if not self.is_connected or self.ws is None:
            raise RuntimeError("WebSocket is not connected")
        
        try:
            json_message = json.dumps(message)
            self.ws.send(json_message)
            logger.debug(f"Sent message: {message}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}", exc_info=True)
            raise
    
    def subscribe_market_depth_diff(
        self,
        market_id: int,
        callback: Callable[[Any], None]
    ) -> None:
        """
        Subscribe to market depth diff updates for a specific market.
        
        Args:
            market_id: Market ID to subscribe to
            callback: Callback function that receives MarketDepthDiffMessage objects.
                The callback will be called whenever a depth update is received.
        
        Raises:
            RuntimeError: If WebSocket is not connected
            ValueError: If market_id is invalid
        
        Example:
            ```python
            def handle_depth_update(msg: MarketDepthDiffMessage):
                print(f"Market {msg.market_id}: {msg.side} {msg.price} @ {msg.size}")
            
            ws.subscribe_market_depth_diff(market_id=1274, callback=handle_depth_update)
            ```
        """
        if not isinstance(market_id, int) or market_id <= 0:
            raise ValueError(f"market_id must be a positive integer, got: {market_id}")
        
        if not self.is_connected or self.ws is None:
            raise RuntimeError("WebSocket is not connected. Call connect() and start() first.")
        
        channel = "market.depth.diff"
        subscription_key = (channel, market_id)
        
        # Store callback
        from .websocket_models import MarketDepthDiffMessage
        self._subscriptions[subscription_key] = callback
        
        # Send subscription message
        subscribe_msg = {
            "action": "SUBSCRIBE",
            "channel": channel,
            "marketId": market_id
        }
        self.send(subscribe_msg)
        
        # Track active subscription
        self._active_subscriptions.add(subscription_key)
        logger.info(f"Subscribed to {channel} for market {market_id}")
    
    def unsubscribe_market_depth_diff(self, market_id: int) -> None:
        """
        Unsubscribe from market depth diff updates for a specific market.
        
        Args:
            market_id: Market ID to unsubscribe from
        
        Raises:
            RuntimeError: If WebSocket is not connected
            ValueError: If market_id is invalid
        """
        if not isinstance(market_id, int) or market_id <= 0:
            raise ValueError(f"market_id must be a positive integer, got: {market_id}")
        
        if not self.is_connected or self.ws is None:
            raise RuntimeError("WebSocket is not connected")
        
        channel = "market.depth.diff"
        subscription_key = (channel, market_id)
        
        # Send unsubscribe message
        unsubscribe_msg = {
            "action": "UNSUBSCRIBE",
            "channel": channel,
            "marketId": market_id
        }
        self.send(unsubscribe_msg)
        
        # Remove subscription
        self._subscriptions.pop(subscription_key, None)
        self._active_subscriptions.discard(subscription_key)
        logger.info(f"Unsubscribed from {channel} for market {market_id}")
    
    def subscribe_market_last_price(
        self,
        market_id: Optional[int] = None,
        root_market_id: Optional[int] = None,
        callback: Callable[[Any], None] = None
    ) -> None:
        """
        Subscribe to market last price updates.
        
        Args:
            market_id: Market ID to subscribe to (for binary markets).
                Either market_id or root_market_id must be provided, but not both.
            root_market_id: Root market ID to subscribe to (for categorical markets).
                Either market_id or root_market_id must be provided, but not both.
            callback: Callback function that receives MarketLastPriceMessage objects.
                The callback will be called whenever a last price update is received.
        
        Raises:
            RuntimeError: If WebSocket is not connected
            ValueError: If both or neither market_id and root_market_id are provided
        
        Example:
            ```python
            # For binary market
            def handle_last_price(msg: MarketLastPriceMessage):
                print(f"Market {msg.market_id}: Last price {msg.price}")
            
            ws.subscribe_market_last_price(market_id=1274, callback=handle_last_price)
            
            # For categorical market
            ws.subscribe_market_last_price(root_market_id=61, callback=handle_last_price)
            ```
        """
        # Check that exactly one of market_id or root_market_id is provided
        if market_id is not None and root_market_id is not None:
            raise ValueError("Cannot provide both market_id and root_market_id. Provide only one of them.")
        
        if market_id is None and root_market_id is None:
            raise ValueError("Either market_id or root_market_id must be provided.")
        
        if market_id is not None and (not isinstance(market_id, int) or market_id <= 0):
            raise ValueError(f"market_id must be a positive integer, got: {market_id}")
        
        if root_market_id is not None and (not isinstance(root_market_id, int) or root_market_id <= 0):
            raise ValueError(f"root_market_id must be a positive integer, got: {root_market_id}")
        
        if not self.is_connected or self.ws is None:
            raise RuntimeError("WebSocket is not connected. Call connect() and start() first.")
        
        channel = "market.last.price"
        
        # Use root_market_id as key if provided, otherwise use market_id
        if root_market_id is not None:
            subscription_key = (channel, root_market_id)
            subscribe_msg = {
                "action": "SUBSCRIBE",
                "channel": channel,
                "rootMarketId": root_market_id
            }
        else:
            subscription_key = (channel, market_id)
            subscribe_msg = {
                "action": "SUBSCRIBE",
                "channel": channel,
                "marketId": market_id
            }
        
        # Store callback
        from .websocket_models import MarketLastPriceMessage
        self._subscriptions[subscription_key] = callback
        
        # Send subscription message
        self.send(subscribe_msg)
        
        # Track active subscription
        self._active_subscriptions.add(subscription_key)
        if root_market_id is not None:
            logger.info(f"Subscribed to {channel} for root market {root_market_id}")
        else:
            logger.info(f"Subscribed to {channel} for market {market_id}")
    
    def unsubscribe_market_last_price(
        self,
        market_id: Optional[int] = None,
        root_market_id: Optional[int] = None
    ) -> None:
        """
        Unsubscribe from market last price updates.
        
        Args:
            market_id: Market ID to unsubscribe from (for binary markets).
                Either market_id or root_market_id must be provided, but not both.
            root_market_id: Root market ID to unsubscribe from (for categorical markets).
                Either market_id or root_market_id must be provided, but not both.
        
        Raises:
            RuntimeError: If WebSocket is not connected
            ValueError: If both or neither market_id and root_market_id are provided
        """
        # Check that exactly one of market_id or root_market_id is provided
        if market_id is not None and root_market_id is not None:
            raise ValueError("Cannot provide both market_id and root_market_id. Provide only one of them.")
        
        if market_id is None and root_market_id is None:
            raise ValueError("Either market_id or root_market_id must be provided.")
        
        if market_id is not None and (not isinstance(market_id, int) or market_id <= 0):
            raise ValueError(f"market_id must be a positive integer, got: {market_id}")
        
        if root_market_id is not None and (not isinstance(root_market_id, int) or root_market_id <= 0):
            raise ValueError(f"root_market_id must be a positive integer, got: {root_market_id}")
        
        if not self.is_connected or self.ws is None:
            raise RuntimeError("WebSocket is not connected")
        
        channel = "market.last.price"
        
        # Use root_market_id as key if provided, otherwise use market_id
        if root_market_id is not None:
            subscription_key = (channel, root_market_id)
            unsubscribe_msg = {
                "action": "UNSUBSCRIBE",
                "channel": channel,
                "rootMarketId": root_market_id
            }
        else:
            subscription_key = (channel, market_id)
            unsubscribe_msg = {
                "action": "UNSUBSCRIBE",
                "channel": channel,
                "marketId": market_id
            }
        
        # Send unsubscribe message
        self.send(unsubscribe_msg)
        
        # Remove subscription
        self._subscriptions.pop(subscription_key, None)
        self._active_subscriptions.discard(subscription_key)
        if root_market_id is not None:
            logger.info(f"Unsubscribed from {channel} for root market {root_market_id}")
        else:
            logger.info(f"Unsubscribed from {channel} for market {market_id}")
    
    def subscribe_market_last_trade(
        self,
        market_id: Optional[int] = None,
        root_market_id: Optional[int] = None,
        callback: Callable[[Any], None] = None
    ) -> None:
        """
        Subscribe to market last trade updates.
        
        Args:
            market_id: Market ID to subscribe to (for binary markets).
                Either market_id or root_market_id must be provided, but not both.
            root_market_id: Root market ID to subscribe to (for categorical markets).
                Either market_id or root_market_id must be provided, but not both.
            callback: Callback function that receives MarketLastTradeMessage objects.
                The callback will be called whenever a last trade update is received.
        
        Raises:
            RuntimeError: If WebSocket is not connected
            ValueError: If both or neither market_id and root_market_id are provided
        
        Example:
            ```python
            # For binary market
            def handle_last_trade(msg: MarketLastTradeMessage):
                print(f"Market {msg.market_id}: {msg.side} {msg.shares} shares @ {msg.price}")
            
            ws.subscribe_market_last_trade(market_id=1274, callback=handle_last_trade)
            
            # For categorical market
            ws.subscribe_market_last_trade(root_market_id=61, callback=handle_last_trade)
            ```
        """
        # Check that exactly one of market_id or root_market_id is provided
        if market_id is not None and root_market_id is not None:
            raise ValueError("Cannot provide both market_id and root_market_id. Provide only one of them.")
        
        if market_id is None and root_market_id is None:
            raise ValueError("Either market_id or root_market_id must be provided.")
        
        if market_id is not None and (not isinstance(market_id, int) or market_id <= 0):
            raise ValueError(f"market_id must be a positive integer, got: {market_id}")
        
        if root_market_id is not None and (not isinstance(root_market_id, int) or root_market_id <= 0):
            raise ValueError(f"root_market_id must be a positive integer, got: {root_market_id}")
        
        if not self.is_connected or self.ws is None:
            raise RuntimeError("WebSocket is not connected. Call connect() and start() first.")
        
        channel = "market.last.trade"
        
        # Use root_market_id as key if provided, otherwise use market_id
        if root_market_id is not None:
            subscription_key = (channel, root_market_id)
            subscribe_msg = {
                "action": "SUBSCRIBE",
                "channel": channel,
                "rootMarketId": root_market_id
            }
        else:
            subscription_key = (channel, market_id)
            subscribe_msg = {
                "action": "SUBSCRIBE",
                "channel": channel,
                "marketId": market_id
            }
        
        # Store callback
        from .websocket_models import MarketLastTradeMessage
        self._subscriptions[subscription_key] = callback
        
        # Send subscription message
        self.send(subscribe_msg)
        
        # Track active subscription
        self._active_subscriptions.add(subscription_key)
        if root_market_id is not None:
            logger.info(f"Subscribed to {channel} for root market {root_market_id}")
        else:
            logger.info(f"Subscribed to {channel} for market {market_id}")
    
    def unsubscribe_market_last_trade(
        self,
        market_id: Optional[int] = None,
        root_market_id: Optional[int] = None
    ) -> None:
        """
        Unsubscribe from market last trade updates.
        
        Args:
            market_id: Market ID to unsubscribe from (for binary markets).
                Either market_id or root_market_id must be provided, but not both.
            root_market_id: Root market ID to unsubscribe from (for categorical markets).
                Either market_id or root_market_id must be provided, but not both.
        
        Raises:
            RuntimeError: If WebSocket is not connected
            ValueError: If both or neither market_id and root_market_id are provided
        """
        # Check that exactly one of market_id or root_market_id is provided
        if market_id is not None and root_market_id is not None:
            raise ValueError("Cannot provide both market_id and root_market_id. Provide only one of them.")
        
        if market_id is None and root_market_id is None:
            raise ValueError("Either market_id or root_market_id must be provided.")
        
        if market_id is not None and (not isinstance(market_id, int) or market_id <= 0):
            raise ValueError(f"market_id must be a positive integer, got: {market_id}")
        
        if root_market_id is not None and (not isinstance(root_market_id, int) or root_market_id <= 0):
            raise ValueError(f"root_market_id must be a positive integer, got: {root_market_id}")
        
        if not self.is_connected or self.ws is None:
            raise RuntimeError("WebSocket is not connected")
        
        channel = "market.last.trade"
        
        # Use root_market_id as key if provided, otherwise use market_id
        if root_market_id is not None:
            subscription_key = (channel, root_market_id)
            unsubscribe_msg = {
                "action": "UNSUBSCRIBE",
                "channel": channel,
                "rootMarketId": root_market_id
            }
        else:
            subscription_key = (channel, market_id)
            unsubscribe_msg = {
                "action": "UNSUBSCRIBE",
                "channel": channel,
                "marketId": market_id
            }
        
        # Send unsubscribe message
        self.send(unsubscribe_msg)
        
        # Remove subscription
        self._subscriptions.pop(subscription_key, None)
        self._active_subscriptions.discard(subscription_key)
        if root_market_id is not None:
            logger.info(f"Unsubscribed from {channel} for root market {root_market_id}")
        else:
            logger.info(f"Unsubscribed from {channel} for market {market_id}")
    
    def subscribe_trade_order_update(
        self,
        market_id: Optional[int] = None,
        root_market_id: Optional[int] = None,
        callback: Callable[[Any], None] = None
    ) -> None:
        """
        Subscribe to trade order update messages.
        
        Args:
            market_id: Market ID to subscribe to (for binary markets).
                Either market_id or root_market_id must be provided, but not both.
            root_market_id: Root market ID to subscribe to (for categorical markets).
                Either market_id or root_market_id must be provided, but not both.
            callback: Callback function that receives TradeOrderUpdateMessage objects.
                The callback will be called whenever an order update is received.
        
        Raises:
            RuntimeError: If WebSocket is not connected
            ValueError: If both or neither market_id and root_market_id are provided
        
        Example:
            ```python
            # For binary market
            def handle_order_update(msg: TradeOrderUpdateMessage):
                print(f"Order {msg.order_id}: {msg.order_update_type}, Status: {msg.status}")
            
            ws.subscribe_trade_order_update(market_id=1274, callback=handle_order_update)
            
            # For categorical market
            ws.subscribe_trade_order_update(root_market_id=61, callback=handle_order_update)
            ```
        """
        # Check that exactly one of market_id or root_market_id is provided
        if market_id is not None and root_market_id is not None:
            raise ValueError("Cannot provide both market_id and root_market_id. Provide only one of them.")
        
        if market_id is None and root_market_id is None:
            raise ValueError("Either market_id or root_market_id must be provided.")
        
        if market_id is not None and (not isinstance(market_id, int) or market_id <= 0):
            raise ValueError(f"market_id must be a positive integer, got: {market_id}")
        
        if root_market_id is not None and (not isinstance(root_market_id, int) or root_market_id <= 0):
            raise ValueError(f"root_market_id must be a positive integer, got: {root_market_id}")
        
        if not self.is_connected or self.ws is None:
            raise RuntimeError("WebSocket is not connected. Call connect() and start() first.")
        
        channel = "trade.order.update"
        
        # Use root_market_id as key if provided, otherwise use market_id
        if root_market_id is not None:
            subscription_key = (channel, root_market_id)
            subscribe_msg = {
                "action": "SUBSCRIBE",
                "channel": channel,
                "rootMarketId": root_market_id
            }
        else:
            subscription_key = (channel, market_id)
            subscribe_msg = {
                "action": "SUBSCRIBE",
                "channel": channel,
                "marketId": market_id
            }
        
        # Store callback
        from .websocket_models import TradeOrderUpdateMessage
        self._subscriptions[subscription_key] = callback
        
        # Send subscription message
        self.send(subscribe_msg)
        
        # Track active subscription
        self._active_subscriptions.add(subscription_key)
        if root_market_id is not None:
            logger.info(f"Subscribed to {channel} for root market {root_market_id}")
        else:
            logger.info(f"Subscribed to {channel} for market {market_id}")
    
    def unsubscribe_trade_order_update(
        self,
        market_id: Optional[int] = None,
        root_market_id: Optional[int] = None
    ) -> None:
        """
        Unsubscribe from trade order update messages.
        
        Args:
            market_id: Market ID to unsubscribe from (for binary markets).
                Either market_id or root_market_id must be provided, but not both.
            root_market_id: Root market ID to unsubscribe from (for categorical markets).
                Either market_id or root_market_id must be provided, but not both.
        
        Raises:
            RuntimeError: If WebSocket is not connected
            ValueError: If both or neither market_id and root_market_id are provided
        """
        # Check that exactly one of market_id or root_market_id is provided
        if market_id is not None and root_market_id is not None:
            raise ValueError("Cannot provide both market_id and root_market_id. Provide only one of them.")
        
        if market_id is None and root_market_id is None:
            raise ValueError("Either market_id or root_market_id must be provided.")
        
        if market_id is not None and (not isinstance(market_id, int) or market_id <= 0):
            raise ValueError(f"market_id must be a positive integer, got: {market_id}")
        
        if root_market_id is not None and (not isinstance(root_market_id, int) or root_market_id <= 0):
            raise ValueError(f"root_market_id must be a positive integer, got: {root_market_id}")
        
        if not self.is_connected or self.ws is None:
            raise RuntimeError("WebSocket is not connected")
        
        channel = "trade.order.update"
        
        # Use root_market_id as key if provided, otherwise use market_id
        if root_market_id is not None:
            subscription_key = (channel, root_market_id)
            unsubscribe_msg = {
                "action": "UNSUBSCRIBE",
                "channel": channel,
                "rootMarketId": root_market_id
            }
        else:
            subscription_key = (channel, market_id)
            unsubscribe_msg = {
                "action": "UNSUBSCRIBE",
                "channel": channel,
                "marketId": market_id
            }
        
        # Send unsubscribe message
        self.send(unsubscribe_msg)
        
        # Remove subscription
        self._subscriptions.pop(subscription_key, None)
        self._active_subscriptions.discard(subscription_key)
        if root_market_id is not None:
            logger.info(f"Unsubscribed from {channel} for root market {root_market_id}")
        else:
            logger.info(f"Unsubscribed from {channel} for market {market_id}")
    
    def subscribe_trade_record_new(
        self,
        market_id: Optional[int] = None,
        root_market_id: Optional[int] = None,
        callback: Callable[[Any], None] = None
    ) -> None:
        """
        Subscribe to trade record new messages.
        
        Args:
            market_id: Market ID to subscribe to (for binary markets).
                Either market_id or root_market_id must be provided, but not both.
            root_market_id: Root market ID to subscribe to (for categorical markets).
                Either market_id or root_market_id must be provided, but not both.
            callback: Callback function that receives TradeRecordNewMessage objects.
                The callback will be called whenever a new trade record is received.
        
        Raises:
            RuntimeError: If WebSocket is not connected
            ValueError: If both or neither market_id and root_market_id are provided
        
        Example:
            ```python
            # For binary market
            def handle_trade_record(msg: TradeRecordNewMessage):
                print(f"Trade {msg.trade_no}: {msg.side} {msg.shares} shares @ {msg.price}")
            
            ws.subscribe_trade_record_new(market_id=1274, callback=handle_trade_record)
            
            # For categorical market
            ws.subscribe_trade_record_new(root_market_id=61, callback=handle_trade_record)
            ```
        """
        # Check that exactly one of market_id or root_market_id is provided
        if market_id is not None and root_market_id is not None:
            raise ValueError("Cannot provide both market_id and root_market_id. Provide only one of them.")
        
        if market_id is None and root_market_id is None:
            raise ValueError("Either market_id or root_market_id must be provided.")
        
        if market_id is not None and (not isinstance(market_id, int) or market_id <= 0):
            raise ValueError(f"market_id must be a positive integer, got: {market_id}")
        
        if root_market_id is not None and (not isinstance(root_market_id, int) or root_market_id <= 0):
            raise ValueError(f"root_market_id must be a positive integer, got: {root_market_id}")
        
        if not self.is_connected or self.ws is None:
            raise RuntimeError("WebSocket is not connected. Call connect() and start() first.")
        
        channel = "trade.record.new"
        
        # Use root_market_id as key if provided, otherwise use market_id
        if root_market_id is not None:
            subscription_key = (channel, root_market_id)
            subscribe_msg = {
                "action": "SUBSCRIBE",
                "channel": channel,
                "rootMarketId": root_market_id
            }
        else:
            subscription_key = (channel, market_id)
            subscribe_msg = {
                "action": "SUBSCRIBE",
                "channel": channel,
                "marketId": market_id
            }
        
        # Store callback
        from .websocket_models import TradeRecordNewMessage
        self._subscriptions[subscription_key] = callback
        
        # Send subscription message
        self.send(subscribe_msg)
        
        # Track active subscription
        self._active_subscriptions.add(subscription_key)
        if root_market_id is not None:
            logger.info(f"Subscribed to {channel} for root market {root_market_id}")
        else:
            logger.info(f"Subscribed to {channel} for market {market_id}")
    
    def unsubscribe_trade_record_new(
        self,
        market_id: Optional[int] = None,
        root_market_id: Optional[int] = None
    ) -> None:
        """
        Unsubscribe from trade record new messages.
        
        Args:
            market_id: Market ID to unsubscribe from (for binary markets).
                Either market_id or root_market_id must be provided, but not both.
            root_market_id: Root market ID to unsubscribe from (for categorical markets).
                Either market_id or root_market_id must be provided, but not both.
        
        Raises:
            RuntimeError: If WebSocket is not connected
            ValueError: If both or neither market_id and root_market_id are provided
        """
        # Check that exactly one of market_id or root_market_id is provided
        if market_id is not None and root_market_id is not None:
            raise ValueError("Cannot provide both market_id and root_market_id. Provide only one of them.")
        
        if market_id is None and root_market_id is None:
            raise ValueError("Either market_id or root_market_id must be provided.")
        
        if market_id is not None and (not isinstance(market_id, int) or market_id <= 0):
            raise ValueError(f"market_id must be a positive integer, got: {market_id}")
        
        if root_market_id is not None and (not isinstance(root_market_id, int) or root_market_id <= 0):
            raise ValueError(f"root_market_id must be a positive integer, got: {root_market_id}")
        
        if not self.is_connected or self.ws is None:
            raise RuntimeError("WebSocket is not connected")
        
        channel = "trade.record.new"
        
        # Use root_market_id as key if provided, otherwise use market_id
        if root_market_id is not None:
            subscription_key = (channel, root_market_id)
            unsubscribe_msg = {
                "action": "UNSUBSCRIBE",
                "channel": channel,
                "rootMarketId": root_market_id
            }
        else:
            subscription_key = (channel, market_id)
            unsubscribe_msg = {
                "action": "UNSUBSCRIBE",
                "channel": channel,
                "marketId": market_id
            }
        
        # Send unsubscribe message
        self.send(unsubscribe_msg)
        
        # Remove subscription
        self._subscriptions.pop(subscription_key, None)
        self._active_subscriptions.discard(subscription_key)
        if root_market_id is not None:
            logger.info(f"Unsubscribed from {channel} for root market {root_market_id}")
        else:
            logger.info(f"Unsubscribed from {channel} for market {market_id}")
    
    def close(self) -> None:
        """
        Close WebSocket connection.
        
        This method stops the heartbeat thread and closes the WebSocket connection.
        """
        logger.info("Closing WebSocket connection")
        
        self.is_running = False
        self._stop_heartbeat()
        
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}", exc_info=True)
            finally:
                self.ws = None
        
        self.is_connected = False
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

