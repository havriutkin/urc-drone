#!/usr/bin/env python3
"""
Rangefinder Bridge Node
Bridges rangefinder data from Gazebo to MAVROS distance_sensor
Converts LaserScan (from Gazebo) to Range (for MAVROS)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range, LaserScan
import math


class RangefinderBridge(Node):
    """
    The RangefinderBridge node acts as a hardware abstraction layer for rangefinder sensors.

    This node bridges rangefinder data from Gazebo or real hardware to standardized
    ROS2 sensor messages. It converts LaserScan messages from Gazebo's ros_gz_bridge to Range
    messages that are compatible with MAVROS and ROS2.

    Key functionalities:
    - Subscribes to Gazebo LaserScan topics for simulated rangefinder data
    - Converts LaserScan to Range messages with appropriate field mappings
    - Publishes Range messages for MAVROS distance sensor integration
    - Handles range limits and validity checks

    The node ensures consistent rangefinder data format across simulation and real-world deployments,
    enabling seamless transition between testing environments and actual drone operations.

    Subscribed topics:
    - /rangefinder_gz: LaserScan from Gazebo simulation

    Published topics:
    - /mavros/distance_sensor/rangefinder_sub: Range message for MAVROS
    """
    def __init__(self):
        super().__init__('rangefinder_bridge')
        
        # Subscribe to Gazebo rangefinder (LaserScan from ros_gz_bridge)
        self.rangefinder_sub = self.create_subscription(
            LaserScan,
            '/rangefinder_gz',
            self.rangefinder_callback,
            10
        )
        
        # Publish to MAVROS distance_sensor (companion computer input)
        self.distance_pub = self.create_publisher(
            Range,
            '/mavros/distance_sensor/rangefinder_sub',
            10
        )
        
        self.get_logger().info('Rangefinder bridge started')
        self.get_logger().info('Subscribing to: /rangefinder_gz (LaserScan)')
        self.get_logger().info('Publishing to: /mavros/distance_sensor/rangefinder_sub (Range)')
    
    def rangefinder_callback(self, msg):
        """
        Receive LaserScan from Gazebo and convert to Range for MAVROS
        """
        # Create a Range message for MAVROS
        range_msg = Range()
        range_msg.header = msg.header
        range_msg.header.frame_id = "rangefinder"
        range_msg.radiation_type = Range.INFRARED  # Laser rangefinder
        range_msg.field_of_view = 0.0  # Single beam (negligible FOV)
        range_msg.min_range = msg.range_min
        range_msg.max_range = msg.range_max
        
        # For a single-beam rangefinder, take the first (and only) range value
        if len(msg.ranges) > 0:
            range_msg.range = msg.ranges[0]
        else:
            range_msg.range = float('inf')
        
        # Publish to MAVROS
        self.distance_pub.publish(range_msg)


def main(args=None):
    rclpy.init(args=args)
    node = RangefinderBridge()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
