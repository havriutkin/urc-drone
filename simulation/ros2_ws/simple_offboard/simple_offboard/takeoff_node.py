import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor

from mavros_msgs.srv import CommandBool, CommandTOL, SetMode
import time


class TakeoffNode(Node):
    """
    A ROS 2 node that uses MAVROS services to perform a takeoff.
    This script is analogous to the provided C++ example.
    """

    def __init__(self):
        super().__init__('takeoff_node')

        # Create service clients
        self.arming_client = self.create_client(CommandBool, '/mavros/cmd/arming')
        self.takeoff_client = self.create_client(CommandTOL, '/mavros/cmd/takeoff')
        self.set_mode_client = self.create_client(SetMode, '/mavros/set_mode')

        # Give the node a second to fully initialize
        time.sleep(1)
        self.get_logger().info("Takeoff node initialized, starting sequence.")

        # Run the takeoff sequence
        self.run_takeoff_sequence()

    def run_takeoff_sequence(self):
        """
        Executes the full takeoff sequence by calling the MAVROS services.
        """
        # 1. Set Mode to GUIDED
        self.get_logger().info("Requesting GUIDED mode...")
        mode_req = SetMode.Request()
        mode_req.custom_mode = "GUIDED"

        # Wait for the service to be available
        if not self.set_mode_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error("Set mode service not available")
            return

        future = self.set_mode_client.call_async(mode_req)
        rclpy.spin_until_future_complete(self, future)

        if not future.result().mode_sent:
            self.get_logger().error("Failed to set GUIDED mode.")
            return
        self.get_logger().info("GUIDED mode set successfully.")

        # 2. Arm the vehicle
        self.get_logger().info("Arming vehicle...")
        arm_req = CommandBool.Request()
        arm_req.value = True

        if not self.arming_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error("Arming service not available")
            return

        future = self.arming_client.call_async(arm_req)
        rclpy.spin_until_future_complete(self, future)

        if not future.result().success:
            self.get_logger().error("Arming failed.")
            return
        self.get_logger().info("Vehicle armed.")

        # 3. Send Takeoff command
        self.get_logger().info("Sending takeoff command...")
        takeoff_req = CommandTOL.Request()
        takeoff_req.altitude = 5.0  # Desired takeoff altitude in meters

        if not self.takeoff_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error("Takeoff service not available")
            return

        future = self.takeoff_client.call_async(takeoff_req)
        rclpy.spin_until_future_complete(self, future)

        if not future.result().success:
            self.get_logger().error("Takeoff failed.")
            return
        self.get_logger().info("Takeoff initiated successfully.")

        # Sequence complete, shutdown the node
        self.get_logger().info("Takeoff sequence complete. Shutting down.")
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    takeoff_node = TakeoffNode()
    # The node handles its own spinning and shutdown
    # No need to call rclpy.spin() here as the sequence is short-lived.
    takeoff_node.destroy_node()


if __name__ == '__main__':
    main()