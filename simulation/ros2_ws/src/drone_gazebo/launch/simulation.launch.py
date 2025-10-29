import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():

    # Set the ardupilot path - make it more flexible
    # First try environment variable, then fall back to relative path
    ardupilot_dir = '/home/havri/ardupilot'
    """
    ardupilot_dir = os.environ.get('ARDUPILOT_DIR')
    if not ardupilot_dir:
        # Assume ardupilot is in the parent directory of ros2_ws
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ardupilot_dir = os.path.join(current_dir, '../../../../ardupilot')
        ardupilot_dir = os.path.abspath(ardupilot_dir)
    """

    # Path to your custom world file
    world_path = os.path.join(
        get_package_share_directory('drone_gazebo'),
        'worlds', 'iris_runway.sdf')

    # Path to the MAVROS launch file
    mavros_launch_path = os.path.join(
        get_package_share_directory('mavros'), 'launch', 'apm.launch')

    return LaunchDescription([
        # 1. Start Gazebo simulation first
        ExecuteProcess(
            cmd=['gz', 'sim', '-v4', '-r', world_path],
            output='screen'
        ),

        # 2. Start ArduPilot SITL after a short delay
        TimerAction(
            period=3.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'sim_vehicle.py', '-v', 'ArduCopter',
                        '-f', 'gazebo-iris', '--model', 'JSON',
                        '--map', '--console'
                    ],
                    cwd=ardupilot_dir,
                    output='screen'
                )
            ]
        ),

        # 3. Start MAVROS after ArduPilot is ready
        TimerAction(
            period=10.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(mavros_launch_path),
                    launch_arguments={'fcu_url': 'udp://127.0.0.1:14550'}.items()
                )
            ]
        ),
    ])