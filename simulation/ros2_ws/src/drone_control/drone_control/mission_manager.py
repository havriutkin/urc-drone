#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from mavros_msgs.srv import CommandBool, CommandTOL, SetMode, CommandLong, ParamGet
from mavros_msgs.msg import State, MountControl
from sensor_msgs.msg import NavSatFix
from geometry_msgs.msg import PoseStamped
from std_srvs.srv import Trigger
from drone_interfaces.srv import SetGimbalAttitude
import random
import math
import time

class MissionManagerNode(Node):
    """
    The MissionManagerNode is the central control node for autonomous drone operations in the ROS2-based drone system.

    This node acts as an interface between high-level mission commands and the MAVROS/MAVLink stack, providing
    essential drone control services such as arming, takeoff, landing, mode changes, and gimbal control.

    Key responsibilities:
    - Arming and disarming the drone motors
    - Executing takeoff and landing sequences
    - Changing flight modes (GUIDED, LOITER, etc.)
    - Controlling gimbal orientation for camera pointing
    - Monitoring drone state, GPS, and local position
    - Providing service interfaces for mission coordination

    The node integrates with:
    - MAVROS for MAVLink communication with the flight controller
    - ArduPilot for low-level flight control

    Subscribed topics:
    - /mavros/state: Current flight state (armed, mode, etc.)
    - /mavros/global_position/global: GPS coordinates
    - /mavros/local_position/pose: Local position and orientation

    Published topics:
    - /mavros/mount_control/command: Gimbal control commands

    Services provided:
    - mission_manager/start_mission: Trigger autonomous mission execution
    - mission_manager/arm: Arm the drone
    - mission_manager/takeoff: Initiate takeoff
    - mission_manager/land: Execute landing
    - mission_manager/set_mode: Change flight mode
    - mission_manager/set_gimbal_attitude: Control gimbal angles

    This node also provides few debugging services, such as 
    test_gimbal and random_gimbal.
    """
    
    def __init__(self):
        super().__init__('mission_manager_node')
        
        # QoS profile for MAVROS topics
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # MAVROS service clients (ROS2 services use /mavros namespace)
        self.arming_client = self.create_client(CommandBool, '/mavros/cmd/arming')
        self.takeoff_client = self.create_client(CommandTOL, '/mavros/cmd/takeoff')
        self.landing_client = self.create_client(CommandTOL, '/mavros/cmd/land')
        self.set_mode_client = self.create_client(SetMode, '/mavros/set_mode')
        self.command_long_client = self.create_client(CommandLong, '/mavros/cmd/command')
        
        # Gimbal control publisher
        self.gimbal_cmd_pub = self.create_publisher(
            MountControl,
            '/mavros/mount_control/command',
            10
        )
        
        # Subscribe to vehicle state
        self.state_sub = self.create_subscription(
            State,
            '/mavros/state',
            self.state_callback,
            qos_profile
        )
        
        # Subscribe to GPS position
        self.gps_sub = self.create_subscription(
            NavSatFix,
            '/mavros/global_position/global',
            self.gps_callback,
            qos_profile
        )
        
        # Subscribe to local position
        self.local_pos_sub = self.create_subscription(
            PoseStamped,
            '/mavros/local_position/pose',
            self.local_pos_callback,
            qos_profile
        )
        
        # State variables
        self.current_state = None
        self.gps_position = None
        self.local_position = None
        self.mission_executed = False
        
        # Create service to trigger autonomous mission
        self.start_mission_srv = self.create_service(
            Trigger,
            'mission_manager/start_mission',
            self.start_mission_callback
        )
        
        # Create service to set gimbal to random position
        self.random_gimbal_srv = self.create_service(
            Trigger,
            'mission_manager/random_gimbal',
            self.random_gimbal_callback
        )
        
        # Create service to set gimbal attitude
        self.set_gimbal_srv = self.create_service(
            SetGimbalAttitude,
            'mission_manager/set_gimbal_attitude',
            self.set_gimbal_attitude_callback
        )
        
        # Create service to test gimbal with smooth rotation
        self.test_gimbal_srv = self.create_service(
            Trigger,
            'mission_manager/test_gimbal',
            self.test_gimbal_callback
        )
        
        # Timer for gimbal test (will be created when test starts)
        self.gimbal_test_timer = None
        self.gimbal_test_start_time = None
        
        self.get_logger().info('Mission manager node started')
        self.get_logger().info('Services:')
        self.get_logger().info('  - /mission_manager/start_mission (start autonomous mission)')
        self.get_logger().info('  - /mission_manager/random_gimbal (set gimbal to random position)')
        self.get_logger().info('  - /mission_manager/set_gimbal_attitude (set gimbal to specific angles)')
        self.get_logger().info('  - /mission_manager/test_gimbal (smooth gimbal rotation test)')
        self.get_logger().info('Waiting for MAVROS connection...')
        
    def start_mission_callback(self, request, response):
        """Service callback to start autonomous mission"""
        if self.current_state is None:
            response.success = False
            response.message = 'MAVROS not connected yet'
            self.get_logger().error('Cannot start mission: MAVROS not connected')
            return response
        
        if not self.current_state.connected:
            response.success = False
            response.message = 'Flight controller not connected'
            self.get_logger().error('Cannot start mission: FCU not connected')
            return response
            
        if self.mission_executed:
            response.success = False
            response.message = 'Mission already executed. Restart node to run again.'
            self.get_logger().warn('Mission already executed')
            return response
        
        self.get_logger().info('Mission start requested via service')
        self.mission_executed = True
        
        # Start mission in a separate thread to not block service response
        import threading
        mission_thread = threading.Thread(target=self.execute_autonomous_mission)
        mission_thread.start()
        
        response.success = True
        response.message = 'Autonomous mission started'
        return response
    
    def random_gimbal_callback(self, request, response):
        """Service callback to set gimbal to random position"""
        if self.current_state is None or not self.current_state.connected:
            response.success = False
            response.message = 'MAVROS not connected'
            self.get_logger().error('Cannot control gimbal: MAVROS not connected')
            return response
        
        # Generate random gimbal angles (in degrees)
        # Pitch: -135 to +45 degrees
        # Roll: -30 to +30 degrees  
        # Yaw: -160 to +160 degrees
        pitch = random.uniform(-135.0, 45.0)
        roll = random.uniform(-30.0, 30.0)
        yaw = random.uniform(-160.0, 160.0)
        
        self.get_logger().info(f'Setting gimbal to random position: pitch={pitch:.1f}°, roll={roll:.1f}°, yaw={yaw:.1f}°')
        
        success = self.set_gimbal_attitude(pitch, roll, yaw)
        
        if success:
            response.success = True
            response.message = f'Gimbal set to pitch={pitch:.1f}°, roll={roll:.1f}°, yaw={yaw:.1f}°'
        else:
            response.success = False
            response.message = 'Failed to set gimbal position'
        
        return response
    
    def set_gimbal_attitude_callback(self, request, response):
        """Service callback to set gimbal to specific angles"""
        if self.current_state is None or not self.current_state.connected:
            response.success = False
            response.message = 'MAVROS not connected'
            self.get_logger().error('Cannot control gimbal: MAVROS not connected')
            return response
        
        self.get_logger().info(f'Setting gimbal attitude: pitch={request.pitch:.1f}°, roll={request.roll:.1f}°, yaw={request.yaw:.1f}°')
        
        success = self.set_gimbal_attitude(request.pitch, request.roll, request.yaw)
        
        if success:
            response.success = True
            response.message = f'Gimbal set to pitch={request.pitch:.1f}°, roll={request.roll:.1f}°, yaw={request.yaw:.1f}°'
        else:
            response.success = False
            response.message = 'Failed to set gimbal attitude'
        
        return response
    
    def test_gimbal_callback(self, request, response):
        """Service callback to start smooth gimbal rotation test"""
        if self.current_state is None or not self.current_state.connected:
            response.success = False
            response.message = 'MAVROS not connected'
            self.get_logger().error('Cannot test gimbal: MAVROS not connected')
            return response
        
        # Stop existing test if running
        if self.gimbal_test_timer is not None:
            self.gimbal_test_timer.cancel()
            self.gimbal_test_timer = None
        
        # Start new test
        self.get_logger().info('=== STARTING GIMBAL SMOOTH ROTATION TEST ===')
        self.get_logger().info('Test duration: 30 seconds')
        self.get_logger().info('Pattern: Circular pitch/yaw movement with sinusoidal roll')
        
        self.gimbal_test_start_time = time.time()
        
        # Create timer that updates gimbal at 10Hz (smooth motion)
        self.gimbal_test_timer = self.create_timer(0.1, self.gimbal_test_update)
        
        response.success = True
        response.message = 'Gimbal test started - smooth rotation for 30 seconds'
        return response
    
    def gimbal_test_update(self):
        """Timer callback for smooth gimbal rotation test"""
        if self.gimbal_test_start_time is None:
            return
        
        elapsed = time.time() - self.gimbal_test_start_time
        
        # Stop test after 30 seconds
        if elapsed > 30.0:
            self.get_logger().info('=== GIMBAL TEST COMPLETE ===')
            if self.gimbal_test_timer is not None:
                self.gimbal_test_timer.cancel()
                self.gimbal_test_timer = None
            self.gimbal_test_start_time = None
            # Return to neutral position
            self.set_gimbal_attitude(0.0, 0.0, 0.0)
            return
        
        # Create smooth circular motion
        # Frequency: complete circle every 10 seconds
        angle = (elapsed / 10.0) * 2.0 * math.pi
        
        # Pitch: oscillate between -30° and +20° (sinusoidal)
        pitch = -5.0 + 25.0 * math.sin(angle)
        
        # Roll: small oscillation ±15° (faster frequency)
        roll = 15.0 * math.sin(angle * 2.0)
        
        # Yaw: full circular rotation -90° to +90°
        yaw = 90.0 * math.cos(angle)
        
        # Update gimbal
        self.set_gimbal_attitude(pitch, roll, yaw)
    
    def set_gimbal_attitude(self, pitch: float, roll: float, yaw: float) -> bool:
        """
        Set gimbal attitude by publishing to /mavros/mount_control/command.
        
        Args:
            pitch: Pitch angle in degrees (-135 to +45)
            roll: Roll angle in degrees (-30 to +30)
            yaw: Yaw angle in degrees (-160 to +160)
            
        Returns:
            True if command was published successfully
        """
        self.get_logger().info('=== GIMBAL CONTROL ===')
        self.get_logger().info(f'Setting gimbal: pitch={pitch:.1f}°, roll={roll:.1f}°, yaw={yaw:.1f}°')
        
        # Create MountControl message
        msg = MountControl()
        msg.mode = 2  # MAV_MOUNT_MODE_MAVLINK_TARGETING
        msg.pitch = float(pitch)  # degrees
        msg.roll = float(roll)    # degrees
        msg.yaw = float(yaw)      # degrees
        msg.altitude = 0.0
        msg.latitude = 0.0
        msg.longitude = 0.0
        
        # Publish to mount_control/command topic
        self.gimbal_cmd_pub.publish(msg)
        self.get_logger().info(f'✓ Published gimbal command: mode={msg.mode}, pitch={msg.pitch}°, roll={msg.roll}°, yaw={msg.yaw}°')
        
        return True
    
    def execute_autonomous_mission(self):
        """Example autonomous mission: GUIDED mode -> Arm -> Takeoff"""
        self.get_logger().info('=== Starting Autonomous Mission ===')
        
        # Step 1: Set GUIDED mode
        if self.set_mode('GUIDED'):
            import time
            time.sleep(2)  # Wait for mode change
            
            # Step 2: Arm
            if self.arm():
                time.sleep(2)  # Wait for arming
                
                # Step 3: Takeoff to 5m
                if self.takeoff(5.0):
                    self.get_logger().info('Mission sequence completed! Drone should be taking off.')
                    # You can add more waypoints, landing, etc. here
        
    def state_callback(self, msg):
        """Update vehicle state"""
        if self.current_state is None:
            self.get_logger().info('MAVROS connected!')
        
        # Log mode changes
        if self.current_state is not None and self.current_state.mode != msg.mode:
            self.get_logger().info(f'Mode changed: {self.current_state.mode} -> {msg.mode}')
        
        # Log armed state changes
        if self.current_state is not None and self.current_state.armed != msg.armed:
            armed_str = 'ARMED' if msg.armed else 'DISARMED'
            self.get_logger().info(f'Vehicle {armed_str}')
            
        self.current_state = msg
        
    def gps_callback(self, msg):
        """Update GPS position"""
        self.gps_position = msg
        
    def local_pos_callback(self, msg):
        """Update local position"""
        self.local_position = msg
        
    def wait_for_service(self, client, timeout_sec=5.0):
        """Wait for a service to be available"""
        if not client.wait_for_service(timeout_sec=timeout_sec):
            self.get_logger().error(f'Service {client.srv_name} not available')
            return False
        return True
        
    def set_mode(self, mode: str):
        """Set flight mode (GUIDED, STABILIZE, LOITER, etc.)"""
        if not self.wait_for_service(self.set_mode_client):
            return False
            
        req = SetMode.Request()
        req.custom_mode = mode
        
        self.get_logger().info(f'Setting mode to {mode}...')
        future = self.set_mode_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        
        if future.result() is not None:
            # Wait a bit for mode to actually change and verify
            import time
            time.sleep(0.5)
            if self.current_state and self.current_state.mode == mode:
                self.get_logger().info(f'Mode set to {mode}')
                return True
            elif future.result().mode_sent:
                # Command was sent successfully, mode will change soon
                self.get_logger().info(f'Mode command sent to {mode}')
                return True
        
        self.get_logger().error(f'Failed to set mode to {mode}')
        return False
            
    def arm(self):
        """Arm the vehicle"""
        if not self.wait_for_service(self.arming_client):
            return False
            
        req = CommandBool.Request()
        req.value = True
        
        self.get_logger().info('Arming vehicle...')
        future = self.arming_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        
        if future.result() is not None and future.result().success:
            self.get_logger().info('Vehicle armed!')
            return True
        else:
            self.get_logger().error('Arming failed!')
            return False
            
    def disarm(self):
        """Disarm the vehicle"""
        if not self.wait_for_service(self.arming_client):
            return False
            
        req = CommandBool.Request()
        req.value = False
        
        self.get_logger().info('Disarming vehicle...')
        future = self.arming_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        
        if future.result() is not None and future.result().success:
            self.get_logger().info('Vehicle disarmed!')
            return True
        else:
            self.get_logger().error('Disarm failed!')
            return False
            
    def takeoff(self, altitude: float):
        """Command takeoff to specified altitude"""
        if not self.wait_for_service(self.takeoff_client):
            return False
            
        req = CommandTOL.Request()
        req.altitude = altitude
        
        self.get_logger().info(f'Taking off to {altitude}m...')
        future = self.takeoff_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        
        if future.result() is not None and future.result().success:
            self.get_logger().info('Takeoff command sent!')
            return True
        else:
            self.get_logger().error('Takeoff failed!')
            return False
            
    def land(self):
        """Command landing"""
        if not self.wait_for_service(self.landing_client):
            return False
            
        req = CommandTOL.Request()
        
        self.get_logger().info('Landing...')
        future = self.landing_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        
        if future.result() is not None and future.result().success:
            self.get_logger().info('Landing command sent!')
            return True
        else:
            self.get_logger().error('Landing failed!')
            return False

def main(args=None):
    rclpy.init(args=args)
    node = MissionManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
