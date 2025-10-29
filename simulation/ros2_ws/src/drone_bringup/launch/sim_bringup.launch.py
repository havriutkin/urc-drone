# In my_robot_bringup/launch/sim_bringup.launch.py

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    sim_launch_path = os.path.join(
        get_package_share_directory('drone_gazebo'), 'launch', 'simulation.launch.py')

    control_launch_path = os.path.join(
        get_package_share_directory('drone_control'), 'launch', 'control.launch.py')

    return LaunchDescription([
        # Starts Gazebo, ArduPilot SITL, MAVROS, and spawns the drone
        IncludeLaunchDescription(PythonLaunchDescriptionSource(sim_launch_path)),

        # Starts your mission_manager and geolocation nodes
        IncludeLaunchDescription(PythonLaunchDescriptionSource(control_launch_path)),
    ])