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
        # 3. Auto Collector (The new logic we wrote)
        Node(
            package='drone_control',
            executable='auto_collector_node',
            name='auto_collector',
            output='screen' # Important to see logs
        ),
        # 4. Inference Node (GTSAM placeholder)
        Node(
            package='drone_control',
            executable='inference_node',
            name='inference_node',
            output='screen'
        ),
    ])