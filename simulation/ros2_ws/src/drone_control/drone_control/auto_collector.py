import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import Range
from sensor_msgs.msg import NavSatFix
from std_srvs.srv import Trigger
from mavros_msgs.srv import SetMode
from mavros_msgs.msg import State, MountControl
from drone_interfaces.srv import SetGimbalAttitude
import numpy as np
import json
import math

def quaternion_to_rotation_matrix(q):
    w, x, y, z = q.w, q.x, q.y, q.z
    return np.array([
        [1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w,     2*x*z + 2*y*w],
        [2*x*y + 2*z*w,     1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w],
        [2*x*z - 2*y*w,     2*y*z + 2*x*w,     1 - 2*x*x - 2*y*y]
    ])

class AutoCollector(Node):
    """
    The AutoCollector node implements an autonomous data collection algorithm.

    This node implements the "stop-and-stare" data collection strategy, where the drone moves to predefined waypoints,
    hovers at each location, aims the gimbal towards an estimated target position (e.g., a cube or landmark),
    and records sensor data including pose, gimbal angles, range measurements, and GPS coordinates.

    The collected data is used for subsequent GTSAM-based factor graph optimization.

    Key features:
    - Autonomous waypoint navigation in GUIDED mode
    - Integration with MAVROS for drone control
    - Service-based mission start trigger
    - Automatic inference triggering upon mission completion

    The node subscribes to:
    - /mavros/local_position/pose: Drone pose
    - /mavros/distance_sensor/rangefinder_sub: Range measurements
    - /mavros/mount_control/command: Gimbal commands (for initial aiming)
    - /mavros/global_position/global: GPS data

    Publishes to:
    - /mavros/setpoint_position/local: Position setpoints

    Services:
    - /start_collection: Trigger to start mission
    - /mavros/set_mode: Mode changes
    - /run_gtsam_inference: Inference trigger
    - mission_manager/set_gimbal_attitude: Gimbal control
    """
    def __init__(self):
        super().__init__('auto_collector')

        qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, durability=DurabilityPolicy.VOLATILE, history=HistoryPolicy.KEEP_LAST, depth=10)

        # --- Settings ---
        self.lateral_movement = 5.0 
        self.hover_duration = 5.0 # Seconds to stare before recording
        self.loop_rate = 10.0 # Hz

        # --- State ---
        self.state = "IDLE" 
        self.current_pose = None
        self.current_range = -1.0
        self.last_manual_pitch = 0.0
        self.last_manual_yaw = 0.0

        # --- Snapshot State (For Relative Updates) ---
        self.initial_pose = None
        self.initial_range = 0.0
        self.initial_pitch = 0.0
        self.initial_yaw = 0.0
        
        # --- Targets ---
        self.estimated_target_pos = None 
        self.waypoints = []
        self.current_wp_index = 0
        self.data_log = []
        self.hover_timer_count = 0

        # --- Interfaces ---
        self.create_subscription(PoseStamped, '/mavros/local_position/pose', self.pose_cb, qos)
        self.create_subscription(Range, '/mavros/distance_sensor/rangefinder_sub', self.range_cb, qos)
        self.create_subscription(MountControl, '/mavros/mount_control/command', self.gimbal_listen_cb, 10)
        self.create_subscription(NavSatFix, '/mavros/global_position/global', self.gps_cb, qos)


        self.pos_pub = self.create_publisher(PoseStamped, '/mavros/setpoint_position/local', 10)
        self.set_mode_client = self.create_client(SetMode, '/mavros/set_mode')
        self.inference_client = self.create_client(Trigger, '/run_gtsam_inference')
        self.gimbal_client = self.create_client(SetGimbalAttitude, 'mission_manager/set_gimbal_attitude')
        self.gimbal_future = None
        self.current_gps = None

        self.create_service(Trigger, '/start_collection', self.start_mission_callback)
        self.timer = self.create_timer(1.0/self.loop_rate, self.control_loop)
        
        self.get_logger().info("AutoCollector (Stop & Stare) Ready.")

    def pose_cb(self, msg): self.current_pose = msg
    def range_cb(self, msg): self.current_range = msg.range
    def gimbal_listen_cb(self, msg):
        if self.state == "IDLE":
            self.last_manual_pitch = msg.pitch
            self.last_manual_yaw = msg.yaw
    def gps_cb(self, msg): self.current_gps = msg

    def get_body_vector(self, pitch_deg, yaw_deg, r):
        p_rad = math.radians(pitch_deg)
        y_rad = math.radians(yaw_deg)
        z = r * math.sin(p_rad)
        xy_dist = r * math.cos(p_rad)
        x = xy_dist * math.cos(y_rad)
        y = xy_dist * math.sin(y_rad)
        return np.array([x, y, z])

    def get_corrected_gimbal_angles(self, current_pose, initial_pose, initial_range, initial_pitch, initial_yaw):
        """
        Calculates new gimbal angles based on drone displacement relative to the initial look-vector.
        """
        # 1. Calculate the initial vector relative to the drone body (spherical to cartesian)
        # Note: We use the stored initial pitch/yaw/range
        body_vec_initial = self.get_body_vector(initial_pitch, initial_yaw, initial_range)

        # 2. Rotate this vector into the World Frame (using initial drone orientation)
        R_initial = quaternion_to_rotation_matrix(initial_pose.pose.orientation)
        world_vec_initial = R_initial.dot(body_vec_initial)

        # 3. Calculate Drone Displacement (How much we moved)
        curr_p = np.array([current_pose.pose.position.x, current_pose.pose.position.y, current_pose.pose.position.z])
        init_p = np.array([initial_pose.pose.position.x, initial_pose.pose.position.y, initial_pose.pose.position.z])
        displacement = curr_p - init_p

        # 4. The new vector to target is the Old Vector minus Displacement
        # geometric logic: Target = Start + Vec => Vec_new = Target - New_Pos 
        # => Vec_new = (Start + Vec) - (Start + Displacement) = Vec - Displacement
        world_vec_new = world_vec_initial - displacement

        # 5. Rotate this new vector back into the Current Body Frame
        # We need the inverse (transpose) of the current orientation
        R_current_inv = quaternion_to_rotation_matrix(current_pose.pose.orientation).T
        body_vec_new = R_current_inv.dot(world_vec_new)

        # 6. Convert back to Pitch/Yaw for the gimbal
        x, y, z = body_vec_new
        dist_xy = math.sqrt(x*x + y*y)
        new_pitch = math.degrees(math.atan2(z, dist_xy))
        new_yaw = math.degrees(math.atan2(y, x))

        return new_pitch, new_yaw
    
    def start_mission_callback(self, request, response):
        if self.current_pose is None:
            response.success = False; response.message = "No Pose Data"; return response

        self.get_logger().info("--- CALCULATING TARGET ---")
        p = self.current_pose.pose.position
        drone_pos = np.array([p.x, p.y, p.z])
        
        # Estimate Cube
        # If range is invalid, we assume 25m as a fallback for testing geometry
        r_val = self.current_range if self.current_range < 50 else 25.0

        self.initial_pose = self.current_pose       # Save the pose object
        self.initial_range = r_val                  # Save the valid range
        self.initial_pitch = self.last_manual_pitch # Save the manual pitch
        self.initial_yaw = self.last_manual_yaw     # Save the manual yaw
        
        body_vec = self.get_body_vector(self.last_manual_pitch, self.last_manual_yaw, r_val)
        R = quaternion_to_rotation_matrix(self.current_pose.pose.orientation)
        self.estimated_target_pos = drone_pos + R.dot(body_vec)
        
        self.get_logger().info(f"Ray Casting Approximation of the target: {self.estimated_target_pos}")

        # Define Waypoints: Current -> Left -> Right -> Center
        wp_center = drone_pos
        wp_left = drone_pos + np.array([0.0, self.lateral_movement, 0.0])
        wp_right = drone_pos + np.array([0.0, -self.lateral_movement, 0.0])
        
        self.waypoints = [wp_left, wp_right, wp_center]
        self.current_wp_index = 0
        
        self.set_mode_client.call_async(SetMode.Request(custom_mode='GUIDED'))
        self.state = "MOVING"
        self.data_log = []
        
        response.success = True
        response.message = "Mission Started"
        return response

    def control_loop(self):
        if self.state == "IDLE" or self.current_pose is None: return

        # State: MOVING
        if self.state == "MOVING":
            target = self.waypoints[self.current_wp_index]
            
            # Send Position
            ps = PoseStamped()
            ps.header.frame_id = "map"
            ps.header.stamp = self.get_clock().now().to_msg()
            ps.pose.position.x = target[0]
            ps.pose.position.y = target[1]
            ps.pose.position.z = target[2]
            ps.pose.orientation = self.current_pose.pose.orientation
            self.pos_pub.publish(ps)
            
            # Check Arrival
            curr_pos = np.array([self.current_pose.pose.position.x, self.current_pose.pose.position.y, self.current_pose.pose.position.z])
            dist = np.linalg.norm(target - curr_pos)
            
            if dist < 0.2:
                self.get_logger().info(f"Arrived at WP {self.current_wp_index}. Hovering...")
                self.state = "HOVERING"
                self.hover_timer_count = 0

        # State: HOVERING (Aiming)
        elif self.state == "HOVERING":
            # Keep sending position command to hold place
            target = self.waypoints[self.current_wp_index]
            ps = PoseStamped()
            ps.header.frame_id = "map"
            ps.header.stamp = self.get_clock().now().to_msg()
            ps.pose.position.x = target[0]; ps.pose.position.y = target[1]; ps.pose.position.z = target[2]
            ps.pose.orientation = self.current_pose.pose.orientation
            self.pos_pub.publish(ps)

            # Calculate Gimbal
            """
            curr_pos = np.array([self.current_pose.pose.position.x, self.current_pose.pose.position.y, self.current_pose.pose.position.z])
            vec_to_target_world = self.estimated_target_pos - curr_pos
            R_inv = quaternion_to_rotation_matrix(self.current_pose.pose.orientation).T
            vec_body = R_inv.dot(vec_to_target_world)
            
            x, y, z = vec_body
            dist_xy = math.sqrt(x*x + y*y)
            pitch_deg = math.degrees(math.atan2(z, dist_xy))
            yaw_deg = math.degrees(math.atan2(y, x))
            """

            pitch_deg, yaw_deg = self.get_corrected_gimbal_angles(
                self.current_pose, 
                self.initial_pose, 
                self.initial_range, 
                self.initial_pitch, 
                self.initial_yaw
            )
            
            # Send Gimbal
            self.send_gimbal(pitch_deg, 0.0, yaw_deg)
            
            # Wait for X seconds
            self.hover_timer_count += 1
            if self.hover_timer_count > (self.hover_duration * self.loop_rate):
                self.record_data(pitch_deg, yaw_deg)
                self.get_logger().info(f"Snapshot taken at WP {self.current_wp_index}")
                
                # Next Waypoint
                self.current_wp_index += 1
                if self.current_wp_index >= len(self.waypoints):
                    self.finish_mission()
                else:
                    self.state = "MOVING"

    def send_gimbal(self, p, r, y):
        if self.gimbal_future is not None and not self.gimbal_future.done(): return
        req = SetGimbalAttitude.Request()
        req.pitch = float(p); req.roll = float(r); req.yaw = float(y)
        self.gimbal_future = self.gimbal_client.call_async(req)

    def record_data(self, pitch, yaw):
        entry = {
            "timestamp": self.get_clock().now().nanoseconds,
            "drone_pos": [
                self.current_pose.pose.position.x, 
                self.current_pose.pose.position.y,
                self.current_pose.pose.position.z
            ],
            "drone_quat": [
                self.current_pose.pose.orientation.w,
                self.current_pose.pose.orientation.x,
                self.current_pose.pose.orientation.y,
                self.current_pose.pose.orientation.z
            ],
            "gimbal_pitch": pitch,
            "gimbal_yaw": yaw,
            "range": self.current_range,
            "gps_ref": {
                "lat": self.current_gps.latitude,
                "lon": self.current_gps.longitude,
                "alt": self.current_gps.altitude
            }
        }
        self.data_log.append(entry)

    def finish_mission(self):
        self.state = "FINISHED"
        #self.set_mode_client.call_async(SetMode.Request(custom_mode='LOITER'))
        with open('mission_data.json', 'w') as f:
            json.dump(self.data_log, f, indent=4)
        self.get_logger().info("Mission Complete. Triggering Inference.")
        if self.inference_client.wait_for_service(timeout_sec=1.0):
            self.inference_client.call_async(Trigger.Request())

def main(args=None):
    rclpy.init(args=args)
    node = AutoCollector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()