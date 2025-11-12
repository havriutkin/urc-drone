import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, TimerAction, SetEnvironmentVariable
from launch.launch_description_sources import AnyLaunchDescriptionSource

def generate_launch_description():

    # Set the ardupilot path - try environment variable first, then fall back to default
    ardupilot_dir = os.environ.get('ARDUPILOT_DIR', os.path.expanduser('~/ardupilot'))
    ardupilot_tools = os.path.join(ardupilot_dir, 'Tools', 'autotest')
    
    # Path to your custom world file
    world_path = os.path.join(
        get_package_share_directory('drone_gazebo'),
        'worlds', 'iris_runway.sdf')

    # Get the drone_description share directory for models
    drone_description_share = get_package_share_directory('drone_description')
    drone_models_path = os.path.join(drone_description_share, 'models')
    
    # Setup Gazebo resource paths
    # Combine existing GZ_SIM_RESOURCE_PATH with our workspace models
    existing_gz_resource_path = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    ardupilot_gazebo_models = os.path.expanduser('~/ardupilot_gazebo/models')
    
    # Build the complete resource path (workspace models : ardupilot models : existing)
    gz_resource_paths = [drone_models_path, ardupilot_gazebo_models]
    if existing_gz_resource_path:
        gz_resource_paths.append(existing_gz_resource_path)
    gz_sim_resource_path = ':'.join(gz_resource_paths)
    
    # Path to the MAVROS launch file - use system installation since it's not in conda
    # MAVROS is installed via apt at /opt/ros/jazzy
    mavros_launch_path = '/opt/ros/jazzy/share/mavros/launch/apm.launch'

    return LaunchDescription([
        # Set GZ_SIM_RESOURCE_PATH to include workspace models
        SetEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=gz_sim_resource_path
        ),
        
        # Add ArduPilot tools to PATH for sim_vehicle.py
        SetEnvironmentVariable(
            name='PATH',
            value=ardupilot_tools + ':' + os.environ.get('PATH', '')
        ),
        
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
        # Note: Using XML launch file format since MAVROS is installed system-wide
        TimerAction(
            period=10.0,
            actions=[
                IncludeLaunchDescription(
                    AnyLaunchDescriptionSource(mavros_launch_path),
                    launch_arguments={
                        'fcu_url': 'udp://127.0.0.1:14550@',
                        'time_timesync_rate': '0.0',  # Disable timesync for simulation
                        'time_timesync_avg_alpha': '0.6',
                        'conn_timeout': '30.0',  # Increase connection timeout for slow simulation
                        'param_use_mission_item_int': 'true'
                    }.items()
                )
            ]
        ),
    ])