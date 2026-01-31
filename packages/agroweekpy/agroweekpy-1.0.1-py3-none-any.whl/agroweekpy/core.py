"""
Core functionality for agroweekpy.

Provides ROS-like node initialization, logging, and control flow.
"""

import time
import threading
import logging
import sys
from typing import Optional, Callable
from datetime import datetime

from .client import get_client, WebSocketClient


# Global state
_node_name: Optional[str] = None
_initialized: bool = False
_shutdown: bool = False
_shutdown_lock = threading.Lock()
_shutdown_callbacks: list = []

# Configure logging
_logger = logging.getLogger("agroweekpy")
_log_handler: Optional[logging.Handler] = None


class AgroweekpyException(Exception):
    """Base exception for agroweekpy."""
    pass


class ROSInterruptException(AgroweekpyException):
    """Exception raised when node is interrupted (like rospy.ROSInterruptException)."""
    pass


class ROSInitException(AgroweekpyException):
    """Exception raised when node initialization fails."""
    pass


def init_node(
    name: str,
    uri: str = "ws://localhost:8765",
    anonymous: bool = False,
    log_level: int = logging.INFO,
    disable_signals: bool = False,
    **kwargs
) -> None:
    """
    Initialize the agroweekpy node.
    
    This must be called before using any other agroweekpy functions.
    Similar to rospy.init_node().
    
    Args:
        name: Name of the node
        uri: WebSocket server URI (default: ws://localhost:8765)
        anonymous: If True, append timestamp to node name
        log_level: Logging level (default: logging.INFO)
        disable_signals: If True, don't register signal handlers
        **kwargs: Additional arguments passed to WebSocket client config
    
    Example:
        >>> import agroweekpy
        >>> agroweekpy.init_node('my_rover', uri='ws://192.168.1.100:8765')
    """
    global _node_name, _initialized, _shutdown, _log_handler
    
    with _shutdown_lock:
        if _initialized:
            logwarn(f"Node already initialized as '{_node_name}'")
            return
        
        if anonymous:
            name = f"{name}_{int(time.time() * 1000)}"
        
        _node_name = name
        _shutdown = False
        
        # Setup logging
        _setup_logging(log_level)
        
        # Configure and start WebSocket client
        client = get_client()
        client.configure(uri=uri, **kwargs)
        
        # Register connection callbacks
        client.on_connect(lambda: loginfo(f"Node '{_node_name}' connected to {uri}"))
        client.on_disconnect(lambda: logwarn(f"Node '{_node_name}' disconnected"))
        
        # Start client
        client.start()
        
        _initialized = True
        
        # Register signal handlers
        if not disable_signals:
            _register_signal_handlers()
        
        loginfo(f"Node '{_node_name}' initialized")


def _setup_logging(level: int) -> None:
    """Setup logging configuration."""
    global _log_handler
    
    if _log_handler is not None:
        _logger.removeHandler(_log_handler)
    
    _log_handler = logging.StreamHandler(sys.stdout)
    _log_handler.setLevel(level)
    
    formatter = logging.Formatter(
        '[%(levelname)s] [%(created).3f]: %(message)s'
    )
    _log_handler.setFormatter(formatter)
    
    _logger.addHandler(_log_handler)
    _logger.setLevel(level)


def _register_signal_handlers() -> None:
    """Register signal handlers for graceful shutdown."""
    import signal
    
    def signal_handler(signum, frame):
        loginfo(f"Received signal {signum}, shutting down...")
        signal_shutdown(f"signal-{signum}")
    
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except (ValueError, OSError):
        # Signals not available (e.g., not main thread)
        pass


def get_name() -> Optional[str]:
    """
    Get the name of the current node.
    
    Returns:
        Node name, or None if not initialized
    """
    return _node_name


def is_shutdown() -> bool:
    """
    Check if the node is shutting down.
    
    Returns:
        True if shutdown has been requested
    
    Example:
        >>> while not agroweekpy.is_shutdown():
        ...     # Do something
        ...     rate.sleep()
    """
    return _shutdown


def signal_shutdown(reason: str = "") -> None:
    """
    Signal that the node should shut down.
    
    Args:
        reason: Reason for shutdown
    """
    global _shutdown
    
    with _shutdown_lock:
        if _shutdown:
            return
        
        _shutdown = True
        loginfo(f"Shutdown requested: {reason}" if reason else "Shutdown requested")
        
        # Call shutdown callbacks
        for callback in _shutdown_callbacks:
            try:
                callback(reason)
            except Exception as e:
                logerr(f"Shutdown callback error: {e}")
        
        # Stop WebSocket client
        get_client().stop()


def on_shutdown(callback: Callable) -> None:
    """
    Register a callback to be called when the node shuts down.
    
    Args:
        callback: Function to call on shutdown (receives reason string)
    
    Example:
        >>> def cleanup(reason):
        ...     print(f"Cleaning up: {reason}")
        >>> agroweekpy.on_shutdown(cleanup)
    """
    _shutdown_callbacks.append(callback)


def spin() -> None:
    """
    Block until the node is shut down.
    
    Similar to rospy.spin().
    
    Example:
        >>> agroweekpy.spin()  # Blocks until Ctrl+C
    """
    _check_initialized()
    
    try:
        while not is_shutdown():
            time.sleep(0.1)
    except KeyboardInterrupt:
        signal_shutdown("keyboard interrupt")


def sleep(duration: float) -> None:
    """
    Sleep for the specified duration.
    
    Args:
        duration: Time to sleep in seconds
    
    Raises:
        ROSInterruptException: If shutdown is requested during sleep
    """
    if duration <= 0:
        return
    
    end_time = time.time() + duration
    while time.time() < end_time:
        if is_shutdown():
            raise ROSInterruptException("Sleep interrupted by shutdown")
        time.sleep(min(0.1, end_time - time.time()))


def get_time() -> float:
    """
    Get current time in seconds.
    
    Returns:
        Current time as float seconds since epoch
    """
    return time.time()


def get_rostime():
    """
    Get current time (alias for get_time for ROS compatibility).
    
    Returns:
        Current time as float seconds
    """
    return get_time()


class Time:
    """Time class for ROS compatibility."""
    
    def __init__(self, secs: float = 0, nsecs: int = 0):
        self.secs = int(secs)
        self.nsecs = nsecs + int((secs - self.secs) * 1e9)
    
    @classmethod
    def now(cls) -> "Time":
        """Get current time."""
        t = time.time()
        return cls(secs=t)
    
    def to_sec(self) -> float:
        """Convert to seconds."""
        return self.secs + self.nsecs / 1e9
    
    def __sub__(self, other: "Time") -> "Duration":
        return Duration(secs=self.to_sec() - other.to_sec())
    
    def __str__(self) -> str:
        return f"Time({self.secs}.{self.nsecs:09d})"


class Duration:
    """Duration class for ROS compatibility."""
    
    def __init__(self, secs: float = 0, nsecs: int = 0):
        self.secs = int(secs)
        self.nsecs = nsecs + int((secs - self.secs) * 1e9)
    
    def to_sec(self) -> float:
        """Convert to seconds."""
        return self.secs + self.nsecs / 1e9
    
    def __str__(self) -> str:
        return f"Duration({self.secs}.{self.nsecs:09d})"


class Rate:
    """
    Rate controller for maintaining loop frequency.
    
    Similar to rospy.Rate().
    
    Example:
        >>> rate = agroweekpy.Rate(10)  # 10 Hz
        >>> while not agroweekpy.is_shutdown():
        ...     # Do something
        ...     rate.sleep()
    """
    
    def __init__(self, hz: float):
        """
        Initialize rate controller.
        
        Args:
            hz: Desired frequency in Hz
        """
        if hz <= 0:
            raise ValueError("Rate must be positive")
        
        self._period = 1.0 / hz
        self._last_time = time.time()
    
    @property
    def period(self) -> float:
        """Get period in seconds."""
        return self._period
    
    def sleep(self) -> None:
        """
        Sleep to maintain the specified rate.
        
        Raises:
            ROSInterruptException: If shutdown is requested during sleep
        """
        if is_shutdown():
            raise ROSInterruptException("Sleep interrupted by shutdown")
        
        current_time = time.time()
        elapsed = current_time - self._last_time
        sleep_time = self._period - elapsed
        
        if sleep_time > 0:
            end_time = current_time + sleep_time
            while time.time() < end_time:
                if is_shutdown():
                    raise ROSInterruptException("Sleep interrupted by shutdown")
                remaining = end_time - time.time()
                if remaining > 0:
                    time.sleep(min(0.01, remaining))
        
        self._last_time = time.time()
    
    def remaining(self) -> float:
        """Get remaining time until next cycle."""
        elapsed = time.time() - self._last_time
        return max(0, self._period - elapsed)


# Logging functions
def logdebug(msg: str, *args) -> None:
    """Log a debug message."""
    _logger.debug(msg, *args)


def loginfo(msg: str, *args) -> None:
    """Log an info message."""
    _logger.info(msg, *args)


def logwarn(msg: str, *args) -> None:
    """Log a warning message."""
    _logger.warning(msg, *args)


def logerr(msg: str, *args) -> None:
    """Log an error message."""
    _logger.error(msg, *args)


def logfatal(msg: str, *args) -> None:
    """Log a fatal message."""
    _logger.critical(msg, *args)


# Aliases for ROS compatibility
rospy_logdebug = logdebug
rospy_loginfo = loginfo
rospy_logwarn = logwarn
rospy_logerr = logerr
rospy_logfatal = logfatal


def _check_initialized() -> None:
    """Check if node is initialized."""
    if not _initialized:
        raise ROSInitException(
            "Node not initialized. Call agroweekpy.init_node() first."
        )


def wait_for_connection(timeout: float = 10.0) -> bool:
    """
    Wait for WebSocket connection to be established.
    
    Args:
        timeout: Maximum time to wait in seconds
    
    Returns:
        True if connected, False if timeout
    """
    _check_initialized()
    
    client = get_client()
    start = time.time()
    
    while not client.is_connected and time.time() - start < timeout:
        if is_shutdown():
            return False
        time.sleep(0.1)
    
    return client.is_connected


def get_connection_stats() -> dict:
    """Get WebSocket connection statistics."""
    _check_initialized()
    return get_client().stats
