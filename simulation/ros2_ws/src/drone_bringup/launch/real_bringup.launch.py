# In my_robot_bringup/launch/real_bringup.launch.py

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    hw_launch_path = os.path.join(
        get_package_share_directory('drone_hardware'), 'launch', 'hardware.launch.py')

    control_launch_path = os.path.join(
        get_package_share_directory('drone_control'), 'launch', 'control.launch.py')

    return LaunchDescription([
        # Starts your gimbal driver and radio node
        IncludeLaunchDescription(PythonLaunchDescriptionSource(hw_launch_path)),

        # Starts your mission_manager and geolocation nodes
        IncludeLaunchDescription(PythonLaunchDescriptionSource(control_launch_path)),
        
        # You would also launch the real MAVROS node here, configured for your flight controller's serial port
    ])