# In drone_control/launch/control.launch.py

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='drone_control',
            executable='mission_manager_node',
            name='mission_manager'
        ),
        Node(
            package='drone_control',
            executable='geolocation_node',
            name='geolocation'
        ),
        # add the object_detector_node here later
    ])