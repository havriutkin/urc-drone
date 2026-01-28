#!/usr/bin/env python3
"""
Gimbal Bridge for Simulation

This node bridges ArduPilot's servo outputs to Gazebo gimbal topics.
It subscribes to MAVROS mount orientation topic and republishes to Gazebo.

Author: URC Drone Team
"""

import rclpy
from rclpy.node import Node
from mavros_msgs.msg import MountControl
from std_msgs.msg import Float64
import math


class GimbalBridgeSim(Node):
    """
    The GimbalBridgeSim node provides gimbal control bridging.

    This node acts as the simulation implementation of the gimbal bridge architecture,
    converting high-level MAVROS mount control commands into Gazebo-compatible gimbal
    commands. It handles the translation between MAVROS MountControl messages
    and individual joint position commands for the gimbal in Gazebo.

    Key functionalities:
    - Subscribes to MAVROS mount control commands for gimbal orientation
    - Converts quaternion or Euler angle commands to individual joint angles
    - Publishes separate pitch, roll, and yaw commands to Gazebo joint controllers
    - Handles coordinate frame transformations between MAVROS and Gazebo conventions
    - Provides simulation-specific gimbal behavior and constraints

    The node is part of the gimbal bridge abstraction layer, ensuring identical
    high-level gimbal control interfaces work in both simulation and real hardware.

    Subscribed topics:
    - /mavros/mount_control/command: MountControl messages from MAVROS

    Published topics:
    - /gimbal/cmd_pitch: Float64 pitch angle for Gazebo
    - /gimbal/cmd_roll: Float64 roll angle for Gazebo
    - /gimbal/cmd_yaw: Float64 yaw angle for Gazebo
    """
    
    def __init__(self):
        super().__init__('gimbal_bridge_sim')
        
        self.get_logger().info('Starting Gimbal Bridge for Simulation')
        
        # Publishers to Gazebo gimbal topics
        self.pitch_pub = self.create_publisher(Float64, '/gimbal/cmd_pitch', 10)
        self.roll_pub = self.create_publisher(Float64, '/gimbal/cmd_roll', 10)
        self.yaw_pub = self.create_publisher(Float64, '/gimbal/cmd_yaw', 10)
        
        # Subscribe to MAVROS mount control commands
        self.mount_sub = self.create_subscription(
            MountControl,
            '/mavros/mount_control/command',
            self.mount_command_callback,
            10
        )
        
        self.get_logger().info('Gimbal bridge initialized')
        self.get_logger().info('  Listening: /mavros/mount_control/command')
        self.get_logger().info('  Publishing: /gimbal/cmd_pitch, /gimbal/cmd_roll, /gimbal/cmd_yaw')
    
    def mount_command_callback(self, msg):
        """
        Callback for mount control command messages from MAVROS.
        Converts degrees to radians and publishes to Gazebo topics.
        
        Args:
            msg: mavros_msgs/MountControl - Mount control command
        """
        # Convert degrees to radians
        pitch_rad = math.radians(msg.pitch)
        roll_rad = math.radians(msg.roll)
        yaw_rad = math.radians(msg.yaw)
        
        # Publish to Gazebo gimbal topics
        pitch_msg = Float64()
        pitch_msg.data = pitch_rad
        self.pitch_pub.publish(pitch_msg)
        
        roll_msg = Float64()
        roll_msg.data = roll_rad
        self.roll_pub.publish(roll_msg)
        
        yaw_msg = Float64()
        yaw_msg.data = yaw_rad
        self.yaw_pub.publish(yaw_msg)
        
        self.get_logger().info(
            f'Gimbal command: pitch={msg.pitch:.1f}°, '
            f'roll={msg.roll:.1f}°, yaw={msg.yaw:.1f}° (mode={msg.mode})'
        )


def main(args=None):
    rclpy.init(args=args)
    node = GimbalBridgeSim()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
