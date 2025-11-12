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
    Bridge node that converts MAVROS mount control messages to Gazebo gimbal commands.
    
    Subscribes to:
        /mavros/mount_control/command (mavros_msgs/MountControl) - Mount control commands
    
    Publishes to:
        /gimbal/cmd_pitch (std_msgs/Float64) - Gazebo gimbal pitch command
        /gimbal/cmd_roll (std_msgs/Float64) - Gazebo gimbal roll command  
        /gimbal/cmd_yaw (std_msgs/Float64) - Gazebo gimbal yaw command
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
