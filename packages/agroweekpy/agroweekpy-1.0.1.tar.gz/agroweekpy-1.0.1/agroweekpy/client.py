"""
WebSocket client for agroweekpy.

Handles communication with the game server via WebSocket.
"""

import asyncio
import json
import threading
import time
from typing import Optional, Dict, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    from websockets.exceptions import ConnectionClosed, InvalidURI, InvalidHandshake
except ImportError:
    raise ImportError("websockets package is required. Install with: pip install websockets")


logger = logging.getLogger("agroweekpy.client")


class ConnectionState(Enum):
    """WebSocket connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"


@dataclass
class ClientConfig:
    """Configuration for WebSocket client."""
    uri: str = "ws://localhost:8765"
    reconnect: bool = True
    reconnect_interval: float = 1.0
    max_reconnect_interval: float = 30.0
    reconnect_backoff: float = 1.5
    message_queue_size: int = 100  # Small queue since we use conflation


class WebSocketClient:
    """
    WebSocket client for game communication.
    
    Manages connection, message routing, and reconnection logic.
    Thread-safe singleton pattern for global access.
    """
    
    _instance: Optional["WebSocketClient"] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.config = ClientConfig()
        self._websocket: Optional[WebSocketClientProtocol] = None
        self._state = ConnectionState.DISCONNECTED
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        
        # Message routing
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._subscribers_lock = threading.Lock()
        
        # Outgoing message queue
        self._send_queue: asyncio.Queue = None
        
        # Conflated topics: store only latest message per topic
        self._conflated_topics: Dict[str, str] = {}
        self._conflate_lock = threading.Lock()
        
        # Connection callbacks
        self._on_connect_callbacks: Set[Callable] = set()
        self._on_disconnect_callbacks: Set[Callable] = set()
        
        # Statistics
        self._messages_sent = 0
        self._messages_received = 0
        self._connect_time: Optional[float] = None
    
    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self._state == ConnectionState.CONNECTED and self._websocket is not None
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "state": self._state.value,
            "messages_sent": self._messages_sent,
            "messages_received": self._messages_received,
            "connected_duration": time.time() - self._connect_time if self._connect_time else 0,
        }
    
    def configure(self, **kwargs) -> None:
        """
        Configure client settings.
        
        Args:
            uri: WebSocket server URI
            reconnect: Enable auto-reconnect
            reconnect_interval: Initial reconnect interval in seconds
            max_reconnect_interval: Maximum reconnect interval
            reconnect_backoff: Backoff multiplier for reconnect
            ping_interval: Ping interval in seconds
            ping_timeout: Ping timeout in seconds
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logger.warning(f"Unknown config option: {key}")
    
    def start(self) -> None:
        """Start the WebSocket client in a background thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Client already running")
            return
        
        self._shutdown_event.clear()
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()
        
        # Wait for connection
        timeout = 5.0
        start = time.time()
        while self._state == ConnectionState.DISCONNECTED and time.time() - start < timeout:
            time.sleep(0.05)
    
    def stop(self) -> None:
        """Stop the WebSocket client."""
        self._shutdown_event.set()
        self._state = ConnectionState.CLOSED
        
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
    
    def _run_event_loop(self) -> None:
        """Run the asyncio event loop in background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._send_queue = asyncio.Queue(maxsize=self.config.message_queue_size)
        
        try:
            self._loop.run_until_complete(self._connection_loop())
        except Exception as e:
            logger.error(f"Event loop error: {e}")
        finally:
            self._loop.close()
            self._loop = None
    
    async def _connection_loop(self) -> None:
        """Main connection loop with reconnection logic."""
        reconnect_interval = self.config.reconnect_interval
        
        while not self._shutdown_event.is_set():
            try:
                self._state = ConnectionState.CONNECTING
                logger.info(f"Connecting to {self.config.uri}")
                
                # Disable ping/pong - Unity server doesn't support it
                async with websockets.connect(
                    self.config.uri,
                    ping_interval=None,  # Disable ping
                    ping_timeout=None,   # Disable ping timeout
                ) as websocket:
                    self._websocket = websocket
                    self._state = ConnectionState.CONNECTED
                    self._connect_time = time.time()
                    reconnect_interval = self.config.reconnect_interval
                    
                    logger.info("Connected to server")
                    self._notify_connect()
                    
                    # Run send and receive tasks
                    await asyncio.gather(
                        self._receive_loop(websocket),
                        self._send_loop(websocket),
                    )
                    
            except (ConnectionClosed, OSError) as e:
                logger.warning(f"Connection closed: {e}")
            except InvalidURI as e:
                logger.error(f"Invalid URI: {e}")
                break
            except InvalidHandshake as e:
                logger.error(f"Handshake failed: {e}")
            except Exception as e:
                logger.error(f"Connection error: {e}")
            finally:
                self._websocket = None
                self._connect_time = None
                self._notify_disconnect()
            
            if not self.config.reconnect or self._shutdown_event.is_set():
                break
            
            self._state = ConnectionState.RECONNECTING
            logger.info(f"Reconnecting in {reconnect_interval:.1f}s")
            await asyncio.sleep(reconnect_interval)
            reconnect_interval = min(
                reconnect_interval * self.config.reconnect_backoff,
                self.config.max_reconnect_interval
            )
        
        self._state = ConnectionState.DISCONNECTED
    
    async def _receive_loop(self, websocket: WebSocketClientProtocol) -> None:
        """Receive messages from WebSocket."""
        try:
            async for message in websocket:
                self._messages_received += 1
                self._handle_message(message)
        except ConnectionClosed:
            pass
    
    async def _send_loop(self, websocket: WebSocketClientProtocol) -> None:
        """Send messages from queue to WebSocket."""
        try:
            last_conflate_send = time.time()
            conflate_interval = 0.01  # Send conflated messages every 10ms
            
            while True:
                try:
                    # Use timeout to allow checking for conflated messages
                    message = await asyncio.wait_for(
                        self._send_queue.get(),
                        timeout=0.01  # 10ms timeout
                    )
                    if message is None:
                        break
                    await websocket.send(message)
                    self._messages_sent += 1
                except asyncio.TimeoutError:
                    # No regular message, check for conflated messages
                    current_time = time.time()
                    if current_time - last_conflate_send >= conflate_interval:
                        # Send all conflated messages
                        with self._conflate_lock:
                            for topic, msg in list(self._conflated_topics.items()):
                                try:
                                    await websocket.send(msg)
                                    self._messages_sent += 1
                                except Exception as e:
                                    logger.error(f"Error sending conflated message: {e}")
                            self._conflated_topics.clear()
                        last_conflate_send = current_time
        except ConnectionClosed:
            pass
    
    def _handle_message(self, raw_message: str) -> None:
        """Parse and route incoming message."""
        try:
            data = json.loads(raw_message)
            topic = data.get("topic", "")
            payload = data.get("data", data)
            
            with self._subscribers_lock:
                callbacks = self._subscribers.get(topic, set()).copy()
            
            for callback in callbacks:
                try:
                    callback(payload)
                except Exception as e:
                    logger.error(f"Callback error for topic '{topic}': {e}")
                    
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON message: {e}")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
    
    def send(self, topic: str, data: Any, conflate: bool = False) -> bool:
        """
        Send message to server.
        
        Args:
            topic: Message topic/channel
            data: Message payload (will be JSON serialized)
            conflate: If True, only keep latest message for this topic (discard old)
        
        Returns:
            True if message was queued, False otherwise
        """
        if not self.is_connected or self._send_queue is None:
            return False
        
        message = json.dumps({
            "topic": topic,
            "data": data,
            "timestamp": time.time(),
        })
        
        if conflate:
            # For conflated topics, just update the latest message
            with self._conflate_lock:
                self._conflated_topics[topic] = message
            return True
        else:
            # For normal topics, queue the message
            def _enqueue_message():
                try:
                    self._send_queue.put_nowait(message)
                except asyncio.QueueFull:
                    # Drop oldest message to make room
                    try:
                        self._send_queue.get_nowait()
                        self._send_queue.put_nowait(message)
                        logger.debug("Send queue full, dropped oldest message")
                    except (asyncio.QueueEmpty, asyncio.QueueFull):
                        logger.warning("Send queue full, message dropped")
            
            try:
                self._loop.call_soon_threadsafe(_enqueue_message)
                return True
            except Exception as e:
                logger.error(f"Send error: {e}")
                return False
    
    def subscribe(self, topic: str, callback: Callable) -> None:
        """
        Subscribe to a topic.
        
        Args:
            topic: Topic to subscribe to
            callback: Function to call when message received
        """
        with self._subscribers_lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = set()
            self._subscribers[topic].add(callback)
    
    def unsubscribe(self, topic: str, callback: Callable) -> None:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
            callback: Callback to remove
        """
        with self._subscribers_lock:
            if topic in self._subscribers:
                self._subscribers[topic].discard(callback)
    
    def on_connect(self, callback: Callable) -> None:
        """Register callback for connection events."""
        self._on_connect_callbacks.add(callback)
    
    def on_disconnect(self, callback: Callable) -> None:
        """Register callback for disconnection events."""
        self._on_disconnect_callbacks.add(callback)
    
    def _notify_connect(self) -> None:
        """Notify all connection callbacks."""
        for callback in self._on_connect_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Connect callback error: {e}")
    
    def _notify_disconnect(self) -> None:
        """Notify all disconnection callbacks."""
        for callback in self._on_disconnect_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Disconnect callback error: {e}")
    
    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.stop()
                cls._instance = None


def get_client() -> WebSocketClient:
    """Get the global WebSocket client instance."""
    return WebSocketClient()
