# In my_robot_bringup/launch/sim_bringup.launch.py

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch_ros.actions import Node
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
        
        # Gimbal bridge for simulation (MAVROS -> ROS2 gimbal topics)
        Node(
            package='drone_hardware',
            executable='gimbal_bridge_sim',
            name='gimbal_bridge_sim',
            output='screen',
            parameters=[],
        ),
        
        # ROS-Gazebo bridge for gimbal control (ROS2 -> Gazebo transport)
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/gimbal/cmd_pitch@std_msgs/msg/Float64]gz.msgs.Double',
                '/gimbal/cmd_roll@std_msgs/msg/Float64]gz.msgs.Double',
                '/gimbal/cmd_yaw@std_msgs/msg/Float64]gz.msgs.Double',
            ],
            output='screen',
        ),
        
        # ROS-Gazebo bridge for rangefinder sensor (Gazebo -> ROS2)
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/rangefinder@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            ],
            remappings=[
                ('/rangefinder', '/rangefinder_gz'),
            ],
            output='screen',
        ),
        
        # Rangefinder bridge (converts LaserScan to Range and publishes to MAVROS)
        Node(
            package='drone_hardware',
            executable='rangefinder_bridge',
            name='rangefinder_bridge',
            output='screen',
        ),
    ])