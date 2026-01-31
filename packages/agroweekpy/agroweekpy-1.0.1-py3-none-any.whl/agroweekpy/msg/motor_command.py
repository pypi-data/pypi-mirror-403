"""
MotorCommand message type.

Used to send velocity commands to left and right motors.
"""

from dataclasses import dataclass, field
from typing import Dict, Any
import time


@dataclass
class MotorCommand:
    """
    Motor command message for differential drive control.
    
    Attributes:
        left_velocity: Velocity for the left motor (-1.0 to 1.0)
        right_velocity: Velocity for the right motor (-1.0 to 1.0)
        timestamp: Message timestamp (auto-generated if not provided)
    
    Example:
        >>> cmd = MotorCommand(left_velocity=0.5, right_velocity=0.5)
        >>> cmd.left_velocity
        0.5
    """
    left_velocity: float = 0.0
    right_velocity: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Clamp velocities to valid range."""
        self.left_velocity = max(-1.0, min(1.0, self.left_velocity))
        self.right_velocity = max(-1.0, min(1.0, self.right_velocity))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            "left_velocity": self.left_velocity,
            "right_velocity": self.right_velocity,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MotorCommand":
        """Create message from dictionary."""
        return cls(
            left_velocity=data.get("left_velocity", 0.0),
            right_velocity=data.get("right_velocity", 0.0),
            timestamp=data.get("timestamp", time.time()),
        )
    
    def stop(self) -> None:
        """Set both motors to stop."""
        self.left_velocity = 0.0
        self.right_velocity = 0.0
        self.timestamp = time.time()
    
    def forward(self, speed: float = 1.0) -> None:
        """Set both motors to move forward."""
        speed = max(-1.0, min(1.0, abs(speed)))
        self.left_velocity = speed
        self.right_velocity = speed
        self.timestamp = time.time()
    
    def backward(self, speed: float = 1.0) -> None:
        """Set both motors to move backward."""
        speed = max(-1.0, min(1.0, abs(speed)))
        self.left_velocity = -speed
        self.right_velocity = -speed
        self.timestamp = time.time()
    
    def turn_left(self, speed: float = 1.0) -> None:
        """Turn left in place."""
        speed = max(-1.0, min(1.0, abs(speed)))
        self.left_velocity = -speed
        self.right_velocity = speed
        self.timestamp = time.time()
    
    def turn_right(self, speed: float = 1.0) -> None:
        """Turn right in place."""
        speed = max(-1.0, min(1.0, abs(speed)))
        self.left_velocity = speed
        self.right_velocity = -speed
        self.timestamp = time.time()
