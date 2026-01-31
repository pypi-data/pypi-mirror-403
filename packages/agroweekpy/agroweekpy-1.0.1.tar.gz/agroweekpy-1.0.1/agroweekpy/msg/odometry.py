"""
Odometry message type.

Full 2D pose odometry with dead reckoning.
Includes wheel distances, velocities, and pose (x, y, theta).
"""

from dataclasses import dataclass, field
from typing import Dict, Any
import time
import math


@dataclass
class Odometry:
    """
    Full 2D odometry message with pose estimation.
    
    Includes:
    - Wheel encoder distances (cumulative)
    - Measured velocities (calculated from deltas, not commands)
    - Pose estimate (x, y, theta) via dead reckoning
    - Linear and angular velocities in robot frame
    - Timing metadata for interpolation
    
    Attributes:
        left_distance: Cumulative left wheel distance (units)
        right_distance: Cumulative right wheel distance (units)
        left_velocity: Measured left wheel velocity (units/s)
        right_velocity: Measured right wheel velocity (units/s)
        x: Robot X position in world frame (units)
        y: Robot Y position in world frame (units)  
        theta: Robot heading in radians (world frame)
        linear_velocity: Forward velocity (units/s)
        angular_velocity: Rotation rate (rad/s)
        sequence: Message sequence number (detect missed messages)
        dt: Time since last update (seconds)
        timestamp: Unix timestamp (seconds)
    
    Example:
        >>> odom = Odometry(x=1.5, y=2.3, theta=0.785)
        >>> odom.theta_degrees
        45.0
        >>> odom.total_distance
        5.2
    """
    # Wheel encoder data
    left_distance: float = 0.0
    right_distance: float = 0.0
    left_velocity: float = 0.0
    right_velocity: float = 0.0
    
    # Pose estimate (dead reckoning)
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0  # radians
    
    # Velocities in robot frame
    linear_velocity: float = 0.0
    angular_velocity: float = 0.0
    
    # Metadata
    sequence: int = 0
    dt: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    @property
    def total_distance(self) -> float:
        """Average distance traveled by both wheels."""
        return (self.left_distance + self.right_distance) / 2.0
    
    @property
    def distance_difference(self) -> float:
        """Difference between left and right wheel distances."""
        return self.left_distance - self.right_distance
    
    @property
    def theta_degrees(self) -> float:
        """Heading in degrees."""
        return math.degrees(self.theta)
    
    @property
    def theta_normalized(self) -> float:
        """Heading normalized to [-pi, pi]."""
        theta = self.theta % (2 * math.pi)
        if theta > math.pi:
            theta -= 2 * math.pi
        return theta
    
    @property
    def theta_degrees_normalized(self) -> float:
        """Heading in degrees normalized to [-180, 180]."""
        return math.degrees(self.theta_normalized)
    
    @property
    def speed(self) -> float:
        """Absolute linear speed (magnitude of velocity)."""
        return abs(self.linear_velocity)
    
    @property
    def is_moving(self) -> bool:
        """Check if robot is moving (velocity above threshold)."""
        return abs(self.linear_velocity) > 0.01 or abs(self.angular_velocity) > 0.01
    
    @property
    def is_turning(self) -> bool:
        """Check if robot is turning in place."""
        return abs(self.angular_velocity) > 0.01 and abs(self.linear_velocity) < 0.01
    
    def distance_to(self, target_x: float, target_y: float) -> float:
        """Calculate Euclidean distance to target point."""
        dx = target_x - self.x
        dy = target_y - self.y
        return math.sqrt(dx * dx + dy * dy)
    
    def angle_to(self, target_x: float, target_y: float) -> float:
        """
        Calculate angle to target point (radians).
        Returns angle in world frame.
        """
        dx = target_x - self.x
        dy = target_y - self.y
        return math.atan2(dy, dx)
    
    def angle_to_degrees(self, target_x: float, target_y: float) -> float:
        """Calculate angle to target point (degrees)."""
        return math.degrees(self.angle_to(target_x, target_y))
    
    def heading_error_to(self, target_x: float, target_y: float) -> float:
        """
        Calculate heading error to face target point.
        Positive = need to turn left (counter-clockwise).
        Negative = need to turn right (clockwise).
        Returns angle in radians [-pi, pi].
        """
        target_angle = self.angle_to(target_x, target_y)
        error = target_angle - self.theta_normalized
        # Normalize to [-pi, pi]
        while error > math.pi:
            error -= 2 * math.pi
        while error < -math.pi:
            error += 2 * math.pi
        return error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            "left_distance": self.left_distance,
            "right_distance": self.right_distance,
            "left_velocity": self.left_velocity,
            "right_velocity": self.right_velocity,
            "x": self.x,
            "y": self.y,
            "theta": self.theta,
            "linear_velocity": self.linear_velocity,
            "angular_velocity": self.angular_velocity,
            "sequence": self.sequence,
            "dt": self.dt,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Odometry":
        """Create message from dictionary."""
        return cls(
            left_distance=data.get("left_distance", 0.0),
            right_distance=data.get("right_distance", 0.0),
            left_velocity=data.get("left_velocity", 0.0),
            right_velocity=data.get("right_velocity", 0.0),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            theta=data.get("theta", 0.0),
            linear_velocity=data.get("linear_velocity", 0.0),
            angular_velocity=data.get("angular_velocity", 0.0),
            sequence=data.get("sequence", 0),
            dt=data.get("dt", 0.0),
            timestamp=data.get("timestamp", time.time()),
        )
    
    def __str__(self) -> str:
        return (
            f"Odometry(pos=({self.x:.2f}, {self.y:.2f}), "
            f"θ={self.theta_degrees:.1f}°, "
            f"v={self.linear_velocity:.2f}, ω={math.degrees(self.angular_velocity):.1f}°/s)"
        )
    
    def __repr__(self) -> str:
        return (
            f"Odometry(x={self.x:.3f}, y={self.y:.3f}, theta={self.theta:.4f}, "
            f"left_dist={self.left_distance:.3f}, right_dist={self.right_distance:.3f}, "
            f"seq={self.sequence})"
        )
