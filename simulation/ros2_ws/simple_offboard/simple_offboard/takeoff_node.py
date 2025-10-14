import rclpy
from rclpy.node import Node

from mavros_msgs.srv import CommandBool, CommandTOL, SetMode
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from sensor_msgs.msg import NavSatFix 
import time


class TakeoffNode(Node):
    """
    A ROS 2 node that uses MAVROS services to perform a takeoff
    and then reads GPS data.
    """

    def __init__(self):
        super().__init__('takeoff_and_gps_node')

        # Create QoS Profile that mathces the gps publisher
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # Create service clients
        self.arming_client = self.create_client(CommandBool, '/mavros/cmd/arming')
        self.takeoff_client = self.create_client(CommandTOL, '/mavros/cmd/takeoff')
        self.set_mode_client = self.create_client(SetMode, '/mavros/set_mode')

        # Create a subscriber for the GPS position
        self.gps_subscriber = self.create_subscription(
            NavSatFix,
            '/mavros/global_position/global',  # Standard topic for global GPS data in MAVROS
            self.gps_callback,
            qos_profile)
        self.gps_position = None  # stores latest gps positions

        # Give the node a second to fully initialize
        time.sleep(1)
        self.get_logger().info("Node initialized, starting sequence.")

        # Run the takeoff and GPS reading sequence
        self.run_sequence()

    def gps_callback(self, msg):
        """This function is called every time a new GPS message is received."""
        self.get_logger().info(f'RECEIVED GPS: Lat={msg.latitude:.6f}, Lon={msg.longitude:.6f}')
        # The first time we get a message, log it to confirm connection
        if self.gps_position is None:
            self.get_logger().info("GPS signal acquired.")
        self.gps_position = msg

    def run_sequence(self):
        """
        Executes the full takeoff and GPS reading sequence.
        """
        # 1. Set Mode to GUIDED
        self.get_logger().info("Requesting GUIDED mode...")
        mode_req = SetMode.Request()
        mode_req.custom_mode = "GUIDED"
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
        takeoff_req.altitude = 5.0
        if not self.takeoff_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error("Takeoff service not available")
            return
        future = self.takeoff_client.call_async(takeoff_req)
        rclpy.spin_until_future_complete(self, future)
        if not future.result().success:
            self.get_logger().error("Takeoff failed.")
            return
        self.get_logger().info("Takeoff initiated successfully.")

        # 4. Read gps
        self.get_logger().info("Waiting for GPS signal...")
        # Wait until the callback has received the first message
        while self.gps_position is None and rclpy.ok():
            time.sleep(0.5)

        if self.gps_position:
            self.get_logger().info("Reading GPS coordinates for 5 seconds...")
            for i in range(5):
                self.get_logger().info(
                    f"-> GPS Lat: {self.gps_position.latitude:.6f}, "
                    f"Lon: {self.gps_position.longitude:.6f}, "
                    f"Alt: {self.gps_position.altitude:.2f}m"
                )
                time.sleep(1)

        # Sequence complete, shutdown the node
        self.get_logger().info("Sequence complete. Shutting down.")
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    takeoff_and_gps_node = TakeoffNode()
    takeoff_and_gps_node.destroy_node()

if __name__ == '__main__':
    main()