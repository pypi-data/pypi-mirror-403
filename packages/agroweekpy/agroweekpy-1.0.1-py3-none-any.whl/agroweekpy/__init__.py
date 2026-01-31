"""
agroweekpy - ROS-like Python library for game robot control via WebSocket.

A rospy-style API for controlling robots in a game via WebSocket communication.
Provides publisher/subscriber pattern for motor control and full 2D odometry.

Basic Usage:
    >>> import agroweekpy
    >>> from agroweekpy.msg import MotorCommand, Odometry
    >>> 
    >>> # Initialize node
    >>> agroweekpy.init_node('my_rover', uri='ws://localhost:8765')
    >>> 
    >>> # Create publisher for motor commands
    >>> motor_pub = agroweekpy.Publisher('/motor_cmd', MotorCommand)
    >>> 
    >>> # Create subscriber for odometry (includes pose, velocities, heading)
    >>> def odom_callback(msg):
    ...     print(f"Pose: ({msg.x:.2f}, {msg.y:.2f}) θ={msg.theta_degrees:.1f}°")
    ...     print(f"Velocity: v={msg.linear_velocity:.2f} ω={msg.angular_velocity:.2f}")
    >>> odom_sub = agroweekpy.Subscriber('/odometry', Odometry, odom_callback)
    >>> 
    >>> # Main loop
    >>> rate = agroweekpy.Rate(10)  # 10 Hz
    >>> while not agroweekpy.is_shutdown():
    ...     cmd = MotorCommand(left_velocity=0.5, right_velocity=0.5)
    ...     motor_pub.publish(cmd)
    ...     rate.sleep()
"""

__version__ = "2.0.0"
__author__ = "Sergej Nekrasov"

# Core functions (like rospy)
from .core import (
    # Node management
    init_node,
    get_name,
    is_shutdown,
    signal_shutdown,
    on_shutdown,
    spin,
    sleep,
    
    # Time
    get_time,
    get_rostime,
    Time,
    Duration,
    Rate,
    
    # Logging
    logdebug,
    loginfo,
    logwarn,
    logerr,
    logfatal,
    
    # Connection
    wait_for_connection,
    get_connection_stats,
    
    # Exceptions
    AgroweekpyException,
    ROSInterruptException,
    ROSInitException,
)

# Publisher/Subscriber
from .publisher import (
    Publisher,
    MotorPublisher,
)

from .subscriber import (
    Subscriber,
    OdometrySubscriber,
    YawSubscriber,
    wait_for_message,
)

# Message types
from .msg import (
    MotorCommand,
    Odometry,
    Yaw,
)

# Client access (advanced usage)
from .client import (
    get_client,
    WebSocketClient,
    ClientConfig,
    ConnectionState,
)

__all__ = [
    # Version
    "__version__",
    
    # Core - Node management
    "init_node",
    "get_name",
    "is_shutdown",
    "signal_shutdown",
    "on_shutdown",
    "spin",
    "sleep",
    
    # Core - Time
    "get_time",
    "get_rostime",
    "Time",
    "Duration",
    "Rate",
    
    # Core - Logging
    "logdebug",
    "loginfo",
    "logwarn",
    "logerr",
    "logfatal",
    
    # Core - Connection
    "wait_for_connection",
    "get_connection_stats",
    
    # Core - Exceptions
    "AgroweekpyException",
    "ROSInterruptException",
    "ROSInitException",
    
    # Publisher/Subscriber
    "Publisher",
    "Subscriber",
    "MotorPublisher",
    "OdometrySubscriber",
    "YawSubscriber",
    "wait_for_message",
    
    # Messages
    "MotorCommand",
    "Odometry",
    "Yaw",
    
    # Client (advanced)
    "get_client",
    "WebSocketClient",
    "ClientConfig",
    "ConnectionState",
]
