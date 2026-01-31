"""
Publisher class for agroweekpy.

Provides ROS-like publishing interface over WebSocket.
"""

from typing import Any, Optional, Type, Dict
import time
import threading

from .client import get_client
from .core import logwarn, logdebug, _check_initialized


class Publisher:
    """
    Publisher for sending messages to topics.
    
    Similar to rospy.Publisher().
    
    Example:
        >>> from agroweekpy import Publisher
        >>> from agroweekpy.msg import MotorCommand
        >>> 
        >>> pub = Publisher('/motor_cmd', MotorCommand, queue_size=10)
        >>> cmd = MotorCommand(left_velocity=0.5, right_velocity=0.5)
        >>> pub.publish(cmd)
    """
    
    def __init__(
        self,
        topic: str,
        data_class: Optional[Type] = None,
        queue_size: int = 10,
        latch: bool = False,
        conflate: bool = False
    ):
        """
        Initialize publisher.
        
        Args:
            topic: Topic name to publish to
            data_class: Message class type (optional, for type hints)
            queue_size: Size of the message queue (not used, for ROS compatibility)
            latch: If True, store last message and send to new subscribers
            conflate: If True, only keep the latest message (drop old ones)
        """
        _check_initialized()
        
        self._topic = topic
        self._data_class = data_class
        self._queue_size = queue_size
        self._latch = latch
        self._conflate = conflate
        self._last_message: Optional[Any] = None
        self._lock = threading.Lock()
        self._client = get_client()
        
        # Statistics
        self._num_published = 0
        self._last_publish_time: Optional[float] = None
        
        logdebug(f"Publisher created for topic '{topic}'")
    
    @property
    def topic(self) -> str:
        """Get the topic name."""
        return self._topic
    
    @property
    def data_class(self) -> Optional[Type]:
        """Get the message data class."""
        return self._data_class
    
    @property
    def num_published(self) -> int:
        """Get number of messages published."""
        return self._num_published
    
    @property
    def last_message(self) -> Optional[Any]:
        """Get the last published message (if latched)."""
        return self._last_message if self._latch else None
    
    def publish(self, msg: Any) -> bool:
        """
        Publish a message to the topic.
        
        Args:
            msg: Message to publish. Can be a message object with to_dict(),
                 a dict, or any JSON-serializable object.
        
        Returns:
            True if message was sent successfully, False otherwise
        
        Example:
            >>> cmd = MotorCommand(left_velocity=1.0, right_velocity=1.0)
            >>> pub.publish(cmd)
            True
        """
        # Convert message to dict if it has to_dict method
        if hasattr(msg, 'to_dict'):
            data = msg.to_dict()
        elif isinstance(msg, dict):
            data = msg
        else:
            data = {"value": msg}
        
        with self._lock:
            success = self._client.send(self._topic, data, conflate=self._conflate)
            
            if success:
                self._num_published += 1
                self._last_publish_time = time.time()
                
                if self._latch:
                    self._last_message = msg
                
                logdebug(f"Published to '{self._topic}': {data}")
            else:
                logwarn(f"Failed to publish to '{self._topic}'")
            
            return success
    
    def get_num_connections(self) -> int:
        """
        Get the number of subscribers (ROS compatibility).
        
        Note: In WebSocket mode, this returns 1 if connected, 0 otherwise.
        """
        return 1 if self._client.is_connected else 0
    
    def unregister(self) -> None:
        """
        Unregister the publisher.
        
        Note: In WebSocket mode, this is a no-op as there's no registration.
        """
        logdebug(f"Publisher for '{self._topic}' unregistered")


class MotorPublisher(Publisher):
    """
    Specialized publisher for motor commands.
    
    Provides convenient methods for common motor operations.
    
    Example:
        >>> motor_pub = MotorPublisher('/motor_cmd')
        >>> motor_pub.forward(0.5)
        >>> motor_pub.stop()
    """
    
    def __init__(self, topic: str = "/motor_cmd", queue_size: int = 10):
        """Initialize motor publisher."""
        from .msg import MotorCommand
        super().__init__(topic, MotorCommand, queue_size, conflate=True)
    
    def set_velocity(self, left: float, right: float) -> bool:
        """
        Set motor velocities.
        
        Args:
            left: Left motor velocity (-1.0 to 1.0)
            right: Right motor velocity (-1.0 to 1.0)
        
        Returns:
            True if command was sent successfully
        """
        from .msg import MotorCommand
        cmd = MotorCommand(left_velocity=left, right_velocity=right)
        return self.publish(cmd)
    
    def forward(self, speed: float = 1.0) -> bool:
        """Move forward at the specified speed."""
        speed = max(0, min(1.0, abs(speed)))
        return self.set_velocity(speed, speed)
    
    def backward(self, speed: float = 1.0) -> bool:
        """Move backward at the specified speed."""
        speed = max(0, min(1.0, abs(speed)))
        return self.set_velocity(-speed, -speed)
    
    def turn_left(self, speed: float = 1.0) -> bool:
        """Turn left in place."""
        speed = max(0, min(1.0, abs(speed)))
        return self.set_velocity(-speed, speed)
    
    def turn_right(self, speed: float = 1.0) -> bool:
        """Turn right in place."""
        speed = max(0, min(1.0, abs(speed)))
        return self.set_velocity(speed, -speed)
    
    def stop(self) -> bool:
        """Stop both motors."""
        return self.set_velocity(0, 0)
    
    def arc_left(self, speed: float = 1.0, ratio: float = 0.5) -> bool:
        """
        Move in a left arc.
        
        Args:
            speed: Base speed
            ratio: Ratio of left to right motor (0-1)
        """
        speed = max(0, min(1.0, abs(speed)))
        ratio = max(0, min(1.0, ratio))
        return self.set_velocity(speed * ratio, speed)
    
    def arc_right(self, speed: float = 1.0, ratio: float = 0.5) -> bool:
        """
        Move in a right arc.
        
        Args:
            speed: Base speed
            ratio: Ratio of right to left motor (0-1)
        """
        speed = max(0, min(1.0, abs(speed)))
        ratio = max(0, min(1.0, ratio))
        return self.set_velocity(speed, speed * ratio)
