#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

class GimbalBridgeReal(Node):
    """
    The GimbalBridgeSim node serves as a placeholder for the real
    bridge between MAVROS and custom gimbal.
    To be implemented by firmware team.
    """
    
    def __init__(self):
        raise NotImplemented()
    
    def mount_command_callback(self, msg):
        """
        Callback for mount control command messages from MAVROS.
        Converts degrees to radians and publishes to Gazebo topics.
        
        Args:
            msg: mavros_msgs/MountControl - Mount control command
        """
        raise NotImplemented()


def main(args=None):
    rclpy.init(args=args)
    node = GimbalBridgeReal()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
