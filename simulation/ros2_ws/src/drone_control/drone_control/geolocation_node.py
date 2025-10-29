#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

class GeolocationNode(Node):
    def __init__(self):
        super().__init__('geolocation_node')
        self.get_logger().info('Geolocation node started')

def main(args=None):
    rclpy.init(args=args)
    node = GeolocationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()