"""
Subscriber class for agroweekpy.

Provides ROS-like subscription interface over WebSocket.
"""

from typing import Any, Optional, Type, Callable, Union
import threading
import time
from collections import deque

from .client import get_client
from .core import logwarn, logdebug, loginfo, _check_initialized
from .msg import Odometry, Yaw


class Subscriber:
    """
    Subscriber for receiving messages from topics.
    
    Similar to rospy.Subscriber().
    
    Example:
        >>> from agroweekpy import Subscriber
        >>> from agroweekpy.msg import Odometry
        >>> 
        >>> def callback(msg):
        ...     print(f"Distance: {msg.total_distance}")
        >>> 
        >>> sub = Subscriber('/odometry', Odometry, callback)
    """
    
    def __init__(
        self,
        topic: str,
        data_class: Optional[Type] = None,
        callback: Optional[Callable] = None,
        queue_size: int = 10,
        buff_size: int = 65536
    ):
        """
        Initialize subscriber.
        
        Args:
            topic: Topic name to subscribe to
            data_class: Message class for deserialization
            callback: Function to call when message received
            queue_size: Size of the message queue
            buff_size: Buffer size (not used, for ROS compatibility)
        """
        _check_initialized()
        
        self._topic = topic
        self._data_class = data_class
        self._callback = callback
        self._queue_size = queue_size
        self._client = get_client()
        self._lock = threading.Lock()
        
        # Message queue for polling mode
        self._message_queue: deque = deque(maxlen=queue_size)
        
        # Statistics
        self._num_received = 0
        self._last_receive_time: Optional[float] = None
        self._last_message: Optional[Any] = None
        
        # Register with client
        self._client.subscribe(topic, self._internal_callback)
        
        logdebug(f"Subscriber created for topic '{topic}'")
    
    @property
    def topic(self) -> str:
        """Get the topic name."""
        return self._topic
    
    @property
    def data_class(self) -> Optional[Type]:
        """Get the message data class."""
        return self._data_class
    
    @property
    def num_received(self) -> int:
        """Get number of messages received."""
        return self._num_received
    
    @property
    def last_message(self) -> Optional[Any]:
        """Get the last received message."""
        return self._last_message
    
    def _internal_callback(self, data: dict) -> None:
        """Internal callback that handles message conversion."""
        try:
            # Convert dict to message class if specified
            if self._data_class is not None and hasattr(self._data_class, 'from_dict'):
                msg = self._data_class.from_dict(data)
            else:
                msg = data
            
            with self._lock:
                self._num_received += 1
                self._last_receive_time = time.time()
                self._last_message = msg
                
                # Add to queue for polling
                self._message_queue.append(msg)
            
            # Call user callback
            if self._callback is not None:
                self._callback(msg)
                
        except Exception as e:
            logwarn(f"Error processing message on '{self._topic}': {e}")
    
    def get(self, timeout: Optional[float] = None) -> Optional[Any]:
        """
        Get the next message from the queue (polling mode).
        
        Args:
            timeout: Maximum time to wait for message (None = no wait)
        
        Returns:
            Message or None if no message available
        """
        if timeout is None:
            with self._lock:
                if self._message_queue:
                    return self._message_queue.popleft()
                return None
        
        start = time.time()
        while time.time() - start < timeout:
            with self._lock:
                if self._message_queue:
                    return self._message_queue.popleft()
            time.sleep(0.01)
        
        return None
    
    def wait_for_message(self, timeout: float = 10.0) -> Optional[Any]:
        """
        Wait for the next message.
        
        Args:
            timeout: Maximum time to wait in seconds
        
        Returns:
            Message or None if timeout
        """
        return self.get(timeout)
    
    def unregister(self) -> None:
        """Unregister the subscriber."""
        self._client.unsubscribe(self._topic, self._internal_callback)
        logdebug(f"Subscriber for '{self._topic}' unregistered")


class OdometrySubscriber(Subscriber):
    """
    Specialized subscriber for full 2D odometry data.
    
    Provides convenient methods for accessing pose, velocities, and distances.
    Now includes pose (x, y, theta) from dead reckoning.
    
    Example:
        >>> odom_sub = OdometrySubscriber('/odometry')
        >>> pose = odom_sub.get_pose()
        >>> print(f"Position: ({pose[0]:.2f}, {pose[1]:.2f}), Heading: {pose[2]:.1f}°")
    """
    
    def __init__(
        self,
        topic: str = "/odometry",
        callback: Optional[Callable] = None,
        queue_size: int = 10
    ):
        """Initialize odometry subscriber."""
        super().__init__(topic, Odometry, callback, queue_size)
        self._last_sequence = -1
        self._missed_messages = 0
    
    def _internal_callback(self, data: dict) -> None:
        """Track sequence numbers for missed message detection."""
        seq = data.get("sequence", 0)
        if self._last_sequence >= 0:
            expected = self._last_sequence + 1
            if seq != expected:
                self._missed_messages += seq - expected
        self._last_sequence = seq
        
        # Call parent callback
        super()._internal_callback(data)
    
    def get_odometry(self) -> Optional[Odometry]:
        """
        Get the latest odometry data.
        
        Returns:
            Odometry message or None
        """
        return self._last_message
    
    # === Pose Methods ===
    
    def get_pose(self) -> tuple:
        """
        Get current pose as (x, y, theta_degrees).
        
        Returns:
            Tuple of (x, y, theta_degrees)
        """
        if self._last_message is None:
            return (0.0, 0.0, 0.0)
        return (
            self._last_message.x,
            self._last_message.y,
            self._last_message.theta_degrees
        )
    
    def get_position(self) -> tuple:
        """
        Get current position as (x, y).
        
        Returns:
            Tuple of (x, y)
        """
        if self._last_message is None:
            return (0.0, 0.0)
        return (self._last_message.x, self._last_message.y)
    
    def get_x(self) -> float:
        """Get X position."""
        return self._last_message.x if self._last_message else 0.0
    
    def get_y(self) -> float:
        """Get Y position."""
        return self._last_message.y if self._last_message else 0.0
    
    def get_theta(self) -> float:
        """Get heading in radians."""
        return self._last_message.theta if self._last_message else 0.0
    
    def get_theta_degrees(self) -> float:
        """Get heading in degrees."""
        return self._last_message.theta_degrees if self._last_message else 0.0
    
    # === Distance Methods ===
    
    def get_distance(self) -> float:
        """
        Get the total distance traveled (average of both motors).
        
        Returns:
            Total distance traveled
        """
        if self._last_message is None:
            return 0.0
        return self._last_message.total_distance
    
    def get_left_distance(self) -> float:
        """Get distance traveled by left motor."""
        if self._last_message is None:
            return 0.0
        return self._last_message.left_distance
    
    def get_right_distance(self) -> float:
        """Get distance traveled by right motor."""
        if self._last_message is None:
            return 0.0
        return self._last_message.right_distance
    
    # === Velocity Methods ===
    
    def get_linear_velocity(self) -> float:
        """Get forward/backward velocity (units/s)."""
        return self._last_message.linear_velocity if self._last_message else 0.0
    
    def get_angular_velocity(self) -> float:
        """Get rotation rate (rad/s)."""
        return self._last_message.angular_velocity if self._last_message else 0.0
    
    def get_angular_velocity_degrees(self) -> float:
        """Get rotation rate (deg/s)."""
        import math
        return math.degrees(self.get_angular_velocity())
    
    def get_left_velocity(self) -> float:
        """Get measured left wheel velocity (units/s)."""
        return self._last_message.left_velocity if self._last_message else 0.0
    
    def get_right_velocity(self) -> float:
        """Get measured right wheel velocity (units/s)."""
        return self._last_message.right_velocity if self._last_message else 0.0
    
    # === State Methods ===
    
    def is_moving(self) -> bool:
        """Check if robot is moving."""
        return self._last_message.is_moving if self._last_message else False
    
    def is_turning(self) -> bool:
        """Check if robot is turning in place."""
        return self._last_message.is_turning if self._last_message else False
    
    # === Navigation Methods ===
    
    def distance_to(self, target_x: float, target_y: float) -> float:
        """Calculate Euclidean distance to target point."""
        if self._last_message is None:
            return 0.0
        return self._last_message.distance_to(target_x, target_y)
    
    def heading_error_to(self, target_x: float, target_y: float) -> float:
        """
        Calculate heading error to face target point.
        Returns angle in radians [-pi, pi].
        """
        if self._last_message is None:
            return 0.0
        return self._last_message.heading_error_to(target_x, target_y)
    
    # === Diagnostic Methods ===
    
    def get_sequence(self) -> int:
        """Get current sequence number."""
        return self._last_message.sequence if self._last_message else 0
    
    def get_missed_messages(self) -> int:
        """Get count of missed messages (sequence gaps)."""
        return self._missed_messages


class YawSubscriber(Subscriber):
    """
    Specialized subscriber for yaw (rotation) data.
    
    Provides convenient methods for accessing orientation information.
    
    Example:
        >>> yaw_sub = YawSubscriber('/yaw')
        >>> angle = yaw_sub.get_angle()
        >>> print(f"Current heading: {angle}°")
    """
    
    def __init__(
        self,
        topic: str = "/yaw",
        callback: Optional[Callable] = None,
        queue_size: int = 10
    ):
        """Initialize yaw subscriber."""
        super().__init__(topic, Yaw, callback, queue_size)
        self._initial_angle: Optional[float] = None
    
    def _internal_callback(self, data: dict) -> None:
        """Track initial angle for relative calculations."""
        if self._initial_angle is None:
            self._initial_angle = data.get("angle", 0.0)
        super()._internal_callback(data)
    
    def get_yaw(self) -> Optional[Yaw]:
        """
        Get the latest yaw data.
        
        Returns:
            Yaw message or None
        """
        return self._last_message
    
    def get_angle(self) -> float:
        """
        Get the current yaw angle in degrees.
        
        Returns:
            Yaw angle in degrees
        """
        if self._last_message is None:
            return 0.0
        return self._last_message.angle
    
    def get_angle_radians(self) -> float:
        """
        Get the current yaw angle in radians.
        
        Returns:
            Yaw angle in radians
        """
        if self._last_message is None:
            return 0.0
        return self._last_message.radians
    
    def get_normalized_angle(self) -> float:
        """
        Get the yaw angle normalized to -180 to 180 range.
        
        Returns:
            Normalized yaw angle in degrees
        """
        if self._last_message is None:
            return 0.0
        return self._last_message.normalized_angle
    
    def get_relative_angle(self) -> float:
        """
        Get the angle relative to initial orientation.
        
        Returns:
            Relative angle in degrees
        """
        if self._last_message is None or self._initial_angle is None:
            return 0.0
        return self._last_message.angle - self._initial_angle
    
    def get_angular_velocity(self) -> float:
        """
        Get the current angular velocity.
        
        Returns:
            Angular velocity in degrees per second
        """
        if self._last_message is None:
            return 0.0
        return self._last_message.angular_velocity
    
    def angle_to(self, target: float) -> float:
        """
        Calculate shortest angle to target.
        
        Args:
            target: Target angle in degrees
        
        Returns:
            Shortest angle to target (positive = clockwise)
        """
        if self._last_message is None:
            return 0.0
        return self._last_message.angle_to(target)
    
    def reset_initial(self) -> None:
        """Reset initial angle to current angle."""
        if self._last_message is not None:
            self._initial_angle = self._last_message.angle


def wait_for_message(topic: str, data_class: Type, timeout: float = 10.0) -> Optional[Any]:
    """
    Wait for a single message on a topic.
    
    Similar to rospy.wait_for_message().
    
    Args:
        topic: Topic to wait on
        data_class: Expected message class
        timeout: Maximum wait time in seconds
    
    Returns:
        Received message or None if timeout
    
    Example:
        >>> from agroweekpy import wait_for_message
        >>> from agroweekpy.msg import Odometry
        >>> msg = wait_for_message('/odometry', Odometry, timeout=5.0)
    """
    result = [None]
    event = threading.Event()
    
    def callback(msg):
        result[0] = msg
        event.set()
    
    sub = Subscriber(topic, data_class, callback)
    
    try:
        event.wait(timeout)
        return result[0]
    finally:
        sub.unregister()
