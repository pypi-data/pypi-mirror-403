"""
Yaw message type.

DEPRECATED: Yaw data is now included in the Odometry message.
Use Odometry.theta (radians) and Odometry.angular_velocity instead.

This class is kept for backwards compatibility only.
"""

import warnings
from dataclasses import dataclass, field
from typing import Dict, Any
import time
import math


def _deprecation_warning():
    warnings.warn(
        "Yaw message is deprecated. Use Odometry.theta and Odometry.angular_velocity instead. "
        "The server no longer broadcasts /yaw topic separately.",
        DeprecationWarning,
        stacklevel=3
    )


@dataclass
class Yaw:
    """
    Yaw message containing rotation around Y axis.
    
    Attributes:
        angle: Yaw angle in degrees (rotation around Y axis)
        angular_velocity: Rate of rotation in degrees per second
        timestamp: Message timestamp
    
    Example:
        >>> yaw = Yaw(angle=45.0)
        >>> yaw.radians
        0.7853981633974483
    """
    angle: float = 0.0  # degrees
    angular_velocity: float = 0.0  # degrees per second
    timestamp: float = field(default_factory=time.time)
    
    @property
    def radians(self) -> float:
        """Get yaw angle in radians."""
        return math.radians(self.angle)
    
    @property
    def normalized_angle(self) -> float:
        """Get angle normalized to -180 to 180 range."""
        angle = self.angle % 360
        if angle > 180:
            angle -= 360
        return angle
    
    @property
    def normalized_angle_0_360(self) -> float:
        """Get angle normalized to 0 to 360 range."""
        return self.angle % 360
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            "angle": self.angle,
            "angular_velocity": self.angular_velocity,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Yaw":
        """Create message from dictionary."""
        return cls(
            angle=data.get("angle", 0.0),
            angular_velocity=data.get("angular_velocity", 0.0),
            timestamp=data.get("timestamp", time.time()),
        )
    
    @classmethod
    def from_radians(cls, radians: float, angular_velocity: float = 0.0) -> "Yaw":
        """Create Yaw message from radians."""
        return cls(
            angle=math.degrees(radians),
            angular_velocity=angular_velocity,
        )
    
    def angle_to(self, target_angle: float) -> float:
        """
        Calculate shortest angle to target (in degrees).
        
        Returns positive for clockwise, negative for counter-clockwise.
        """
        diff = (target_angle - self.angle) % 360
        if diff > 180:
            diff -= 360
        return diff
    
    def __str__(self) -> str:
        return f"Yaw(angle={self.angle:.2f}°, velocity={self.angular_velocity:.2f}°/s)"
