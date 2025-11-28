import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
import json
import numpy as np
import math

from geographiclib.geodesic import Geodesic

# Import GTSAM
import gtsam
from gtsam.symbol_shorthand import X, L # X = Pose, L = Landmark

class InferenceNode(Node):
    """
    The InferenceNode performs factor graph based optimization using GTSAM for georeferencing.

    This node implements the inference algorithm that processes collected sensor data to 
    estimate the precise location of points of interest.
    It uses GTSAM (Georgia Tech Smoothing and Mapping) library to construct and optimize factor graphs
    representing the probabilistic relationships between drone poses, sensor measurements, and landmark positions.

    Key features:
    - Factor graph construction with pose and landmark variables
    - Bearing-range factors for sensor measurements
    - Prior factors for initial pose estimates
    - Levenberg-Marquardt optimization for maximum likelihood estimation
    - Automatic data loading from mission logs

    Services:
    - /run_gtsam_inference - Triggers optimization on collected data
    """
    def __init__(self):
        super().__init__('inference_node')
        self.srv = self.create_service(Trigger, '/run_gtsam_inference', self.callback)
        self.get_logger().info("GTSAM Inference Node Ready.")

    def callback(self, request, response):
        self.get_logger().info("Trigger received! Loading Mission Data...")
        
        try:
            # Load Data
            # Ensure this matches where AutoCollector saves it
            import os
            home_path = os.path.expanduser("./")
            filename = os.path.join(home_path, 'mission_data.json')
            
            with open(filename, 'r') as f:
                data = json.load(f)
            
            if not data:
                raise ValueError("Data file is empty!")

            self.get_logger().info(f"Loaded {len(data)} measurements. Building Factor Graph...")
            
            # Run Optimization
            result_point = self.run_gtsam_optimization(data)
            
            # Report
            res_str = f"Cube Located at: X={result_point[0]:.2f}, Y={result_point[1]:.2f}, Z={result_point[2]:.2f}"
            self.get_logger().info("SUCCESS! " + res_str)
            
            response.success = True
            response.message = res_str
            
        except Exception as e:
            self.get_logger().error(f"Optimization Failed: {e}")
            response.success = False
            response.message = str(e)
            
        return response

    def run_gtsam_optimization(self, data_points):
        # --- A. Setup Graph and Noise Models ---
        graph = gtsam.NonlinearFactorGraph()
        
        # Noise for Drone Position (Prior) - We trust MAVROS/Sim state quite a bit
        # [Roll, Pitch, Yaw, X, Y, Z] errors
        prior_noise = gtsam.noiseModel.Diagonal.Sigmas(
            np.array([0.01, 0.01, 0.01, 0.05, 0.05, 0.05])
        )
        
        # Noise for Measurements (Bearing + Range)
        # Bearing (radians), Range (meters)
        # We assume bearing is accurate to ~1 degree (0.02 rad) and range to 10cm (0.1m)
        measurement_noise = gtsam.noiseModel.Diagonal.Sigmas(
            np.array([0.02, 0.02, 0.1])
        )

        initial_estimates = gtsam.Values()
        
        # We need a key for the single landmark (Cube)
        LANDMARK_KEY = L(0)

        # --- B. Loop through Data ---
        for i, point in enumerate(data_points):
            POSE_KEY = X(i)
            
            # Extract Drone Pose
            pos = point['drone_pos'] # [x, y, z]
            quat = point['drone_quat'] # [w, x, y, z]
            
            # Construct GTSAM Pose3
            # Note: GTSAM Python Rot3.Quaternion takes (w, x, y, z)
            rot = gtsam.Rot3.Quaternion(quat[0], quat[1], quat[2], quat[3])
            pose = gtsam.Pose3(rot, gtsam.Point3(pos[0], pos[1], pos[2]))
            
            # Add Prior Factor (We trust where the drone says it is)
            graph.add(gtsam.PriorFactorPose3(POSE_KEY, pose, prior_noise))
            initial_estimates.insert(POSE_KEY, pose)
            
            # Extract Measurement
            pitch_deg = point['gimbal_pitch']
            yaw_deg = point['gimbal_yaw']
            r = point['range']
            
            # Convert Angles to Unit3 Vector (Bearing)
            # This must match the geometry that worked in your manual test
            # PITCH: Positive = Down => Z is negative
            p_rad = math.radians(pitch_deg)
            y_rad = math.radians(yaw_deg)
            
            z_b = -1.0 * math.sin(p_rad)
            xy_dist = math.cos(p_rad)
            x_b = xy_dist * math.cos(y_rad)
            y_b = xy_dist * math.sin(y_rad)
            
            bearing_vector = gtsam.Point3(x_b, y_b, z_b)
            bearing_unit = gtsam.Unit3(bearing_vector)
            
            # Add BearingRange Factor
            # Connects Drone Pose X(i) -> Landmark L(0)
            graph.add(gtsam.BearingRangeFactor3D(
                POSE_KEY, LANDMARK_KEY, bearing_unit, float(r), measurement_noise
            ))

        # --- C. Initialize Landmark Guess ---
        # Optimization needs a starting point. We use the first measurement to triangulate a guess.
        first_p = data_points[0]
        guess_pose = initial_estimates.atPose3(X(0))

        # Get reference GPS from the first data point
        ref_gps = data_points[0]['gps_ref']
        ref_pos = data_points[0]['drone_pos'] # The local (x,y) corresponding to that GPS
        
        # Calculate vector in Body frame
        p_rad = math.radians(first_p['gimbal_pitch'])
        y_rad = math.radians(first_p['gimbal_yaw'])
        r = first_p['range']
        
        # Same math as above
        local_vec = np.array([
            r * math.cos(p_rad) * math.cos(y_rad),
            r * math.cos(p_rad) * math.sin(y_rad),
            -r * math.sin(p_rad)
        ])
        
        # Rotate to World Frame
        # Get rotation matrix from the first pose estimate
        R_matrix = guess_pose.rotation().matrix()
        world_vec = R_matrix @ local_vec
        
        # Add to Drone Position
        t_vector = guess_pose.translation() # gtsam.Point3
        guess_x = t_vector[0] + world_vec[0]
        guess_y = t_vector[1] + world_vec[1]
        guess_z = t_vector[2] + world_vec[2]
        
        self.get_logger().info(f"Initial Guess for Cube: [{guess_x:.2f}, {guess_y:.2f}, {guess_z:.2f}]")
        initial_estimates.insert(LANDMARK_KEY, gtsam.Point3(guess_x, guess_y, guess_z))

        # --- D. Optimize ---
        params = gtsam.LevenbergMarquardtParams()
        optimizer = gtsam.LevenbergMarquardtOptimizer(graph, initial_estimates, params)
        result = optimizer.optimize()
        
        # --- E. Extract Result ---
        final_point = result.atPoint3(LANDMARK_KEY)

        
        # Calculate offset of Cube relative to that specific drone position
        # Cube_Global = Drone_Global + (Cube_Local - Drone_Local)
        dx = final_point[0] - ref_pos[0]
        dy = final_point[1] - ref_pos[1]
        
        cube_lat, cube_lon = self.enu_to_gps(ref_gps['lat'], ref_gps['lon'], dx, dy)
        self.get_logger().info(f"Cube GPS: Lat {cube_lat:.7f}, Lon {cube_lon:.7f}")

        return [final_point[0], final_point[1], final_point[2]]

    def enu_to_gps(self, ref_lat, ref_lon, x, y):
        """
        Convert local ENU (x, y) to GPS (lat, lon) relative to a reference point.
        X = East (meters)
        Y = North (meters)
        """
        # Calculate distance and azimuth (bearing) from the reference
        # Distance is simply hypotenuse
        dist = math.sqrt(x*x + y*y)
        
        # Azimuth: 0 is North, 90 is East. 
        # atan2(x, y) gives angle from North (Y-axis) in radians
        azimuth_rad = math.atan2(x, y) 
        azimuth_deg = math.degrees(azimuth_rad)
        
        # Use Geodesic library to compute the new coordinate
        geod = Geodesic.WGS84
        # Direct computation: given lat1, lon1, azi1, s12 (distance), return lat2, lon2
        g = geod.Direct(ref_lat, ref_lon, azimuth_deg, dist)
        
        return g['lat2'], g['lon2']

def main(args=None):
    rclpy.init(args=args)
    node = InferenceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()