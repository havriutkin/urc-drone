# Drone Simulation Setup and Operation Guide

This guide provides comprehensive instructions for setting up and running the drone simulation environment using ROS2 Jazzy, Gazebo Harmonic, and ArduPilot SITL.

## System Requirements

- Ubuntu 24.04 LTS (Noble Numbat)
- At least 8GB RAM (16GB recommended)
- Minimum 20GB free disk space

## Environment Setup

### 1. Prepare Ubuntu System

Ensure Ubuntu 24.04 is installed and updated:
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install ROS2 Jazzy

```bash
# Install required packages
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev

# Add ROS2 repository
sudo apt update && sudo apt install curl -y
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb

# Install ROS2 Jazzy
sudo apt update && sudo apt install ros-dev-tools 
sudo apt install ros-jazzy-desktop 

# Set up environment
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 3. Install Gazebo Harmonic

```bash
# Add the GPG key
sudo wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg

# Add the repository source
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null

# Install Gazebo Harmonic
sudo apt update
sudo apt install gz-harmonic ros-jazzy-ros-gz

# Verify installation
gz sim -v4 shapes.sdf
```

### 4. Clone and Setup ArduPilot

```bash
# Navigate to home directory or desired location
cd ~

# Clone ArduPilot repository
git clone https://github.com/ArduPilot/ardupilot.git
cd ardupilot
git submodule update --init --recursive

# Install dependencies
pip install MAVProxy pymavlink
sudo apt install build-essential

# Install prerequisites
./Tools/environment_install/install-prereqs-ubuntu.sh -y

# Reload shell environment
source ~/.bashrc
```

### 5. Install MAVROS

```bash
sudo apt update
sudo apt install ros-jazzy-mavros ros-jazzy-mavros-extras ros-jazzy-mavros-msgs
```

### 6. Install Geographic Tools

```bash
sudo apt update
sudo apt install geographiclib-tools
sudo geographiclib-get-geoids egm96-5
```

### 7. Install ArduPilot Gazebo Plugin

```bash
# Install dependencies
sudo apt install rapidjson-dev libgz-sim8-dev libopencv-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-bad gstreamer1.0-libav gstreamer1.0-gl

# Clone and build ardupilot_gazebo
cd ~
git clone https://github.com/ArduPilot/ardupilot_gazebo.git
cd ardupilot_gazebo
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo
make -j4
sudo make install

# Set environment variables
echo 'export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/ardupilot_gazebo/build:$GZ_SIM_SYSTEM_PLUGIN_PATH' >> ~/.bashrc
echo 'export GZ_SIM_RESOURCE_PATH=$HOME/ardupilot_gazebo/models:$HOME/ardupilot_gazebo/worlds:$GZ_SIM_RESOURCE_PATH' >> ~/.bashrc
source ~/.bashrc
```

## ROS2 Workspace Setup

### 8. Build the ROS2 Workspace

Navigate to the ROS2 workspace and build all packages using the provided build script:

```bash
# Navigate to the ROS2 workspace
cd ~/urc-drone/simulation/ros2_ws

# Install dependencies using rosdep (first time only)
sudo rosdep init  # Only run this once
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# Build all packages using the automated build script
./scripts/build.sh

# For a clean rebuild (removes build/, install/, log/ directories)
./scripts/build.sh clean

# Source the workspace
source install/setup.bash

# Add workspace sourcing to bashrc for convenience
echo "source ~/urc-drone/simulation/ros2_ws/install/setup.bash" >> ~/.bashrc
```

**Note:** The `build.sh` script automatically handles Python package executable installation issues. See [Build System Documentation](ros2_ws/BUILD_README.md) for details.

## ROS2 Package Overview

The workspace contains the following packages:

- **`drone_description`**: Contains URDF/Xacro files and 3D models for the drone
- **`drone_gazebo`**: Gazebo simulation worlds and launch files
- **`drone_control`**: High-level control nodes (mission manager, geolocation)
- **`drone_interfaces`**: Custom ROS2 messages and services
- **`drone_bringup`**: Launch files for bringing up the complete system
- **`drone_hardware`**: Hardware abstraction layer (currently empty)
- **`simple_offboard`**: Simple offboard control example (takeoff node)

## Running the Simulation

You have multiple options to run the simulation:

### Option 1: Regular launch (Recommended)
Use the usual ROS2 launch command.

```bash
cd ~/urc-drone/simulation
source /opt/ros/jazzy/setup.bash
ros2 launch drone_bringup sim_bringup.launch.py
```

### Option 2: Launch Script
If option 1 fails, you can try custom script:

```bash
cd ~/urc-drone/simulation/ros2_ws
./scripts/launch_simulation_clean.sh
```


**What this script does:**
1. **Environment Cleanup**: Unsets problematic Snap-related environment variables (GTK, GDK, etc.) that can cause GUI issues
2. **Library Path Management**: Filters out Snap paths from `LD_LIBRARY_PATH` and prioritizes system libraries
3. **Complete System Launch**: Starts all components (Gazebo, ArduPilot SITL, MAVROS, control nodes)

**When to use this script:**
- **Recommended**: Running VS Code as a Snap package (most Ubuntu installations)
- First time launching after a fresh clone
- Encountering GTK/GUI-related errors
- Workspace not yet built

**When NOT to use this script:**
- VS Code installed via apt/deb package (system-wide installation)
- Already sourced the workspace and no environment conflicts
- Need more control over individual component startup

### Option 3: Manual Step-by-Step Launch

If you prefer manual control or need to troubleshoot, use separate terminals:

#### Terminal 1: Gazebo Simulation
```bash
cd ~/urc-drone/simulation/ros2_ws
source install/setup.bash
ros2 launch drone_gazebo simulation.launch.py
```

#### Terminal 2: Drone Control System (after Gazebo is running)
```bash
cd ~/urc-drone/simulation/ros2_ws
source install/setup.bash
ros2 launch drone_control control.launch.py
```

### Option 4: Individual Component Testing

For development and testing individual components:

#### Test Simple Takeoff Node
```bash
# Ensure Gazebo, ArduPilot, and MAVROS are running first
cd ~/urc-drone/simulation/ros2_ws
source install/setup.bash
ros2 run simple_offboard takeoff_node
```

#### Manual Component Startup
```bash
# Terminal 1: Gazebo only
gz sim -v4 -r ~/urc-drone/simulation/ros2_ws/src/drone_gazebo/worlds/iris_runway.sdf

# Terminal 2: ArduPilot SITL
cd ~/ardupilot
./Tools/autotest/sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON --map --console

# Terminal 3: MAVROS
source /opt/ros/jazzy/setup.bash
ros2 launch mavros apm.launch fcu_url:=udp://127.0.0.1:14550@

# Terminal 4: Individual nodes
cd ~/urc-drone/simulation/ros2_ws
source install/setup.bash
ros2 run drone_control mission_manager_node
# or
ros2 run drone_control geolocation_node
# or
ros2 run simple_offboard takeoff_node
```

## Verification and Testing

### 1. Check ROS2 Nodes
```bash
# List all running nodes
ros2 node list

# Check node info
ros2 node info /mission_manager
ros2 node info /geolocation
```

### 2. Monitor Topics
```bash
# List all topics
ros2 topic list

# Monitor MAVROS topics
ros2 topic echo /mavros/state
ros2 topic echo /mavros/local_position/pose

# Monitor custom topics (if any)
ros2 topic list | grep drone
```

### 3. Check Services
```bash
# List available services
ros2 service list

# Test MAVROS services
ros2 service call /mavros/cmd/arming mavros_msgs/srv/CommandBool "{value: true}"
ros2 service call /mavros/set_mode mavros_msgs/srv/SetMode "{custom_mode: 'GUIDED'}"
```

## Gimbal Control

### Setting Gimbal Parameters

If gimbal control is not working properly, you can set the ArduPilot gimbal parameters while the simulation is running:

```bash
cd ~/urc-drone/simulation
./set_gimbal_params_live.sh
```

This script configures:
- `MNT1_TYPE = 1` (servo gimbal)
- `MNT1_DEFLT_MODE = 3` (MAVLink targeting)
- Servo channel assignments (SERVO8-10 for roll/pitch/yaw)
- Gimbal angle limits

**Note:** These parameters are usually pre-configured in `~/ardupilot/mav.parm` and persist across simulation runs. The live script is only needed if parameters get reset or for troubleshooting.

### Testing Gimbal Control

Test the gimbal using mission_manager services:

```bash
# Set gimbal to specific angles (pitch, roll, yaw in degrees)
ros2 service call /mission_manager/set_gimbal_attitude \
  drone_interfaces/srv/SetGimbalAttitude \
  "{pitch: -45.0, roll: 0.0, yaw: 30.0}"

# Set gimbal to random position
ros2 service call /mission_manager/random_gimbal std_srvs/srv/Trigger

# Run smooth rotation test (30 seconds)
ros2 service call /mission_manager/test_gimbal std_srvs/srv/Trigger
```

For more details on gimbal architecture and troubleshooting, see [Gimbal Bridge Documentation](GIMBAL_BRIDGE.md).

## Troubleshooting

### Common Issues

1. **GTK/GUI errors or Gazebo crashes on startup**:
   - **Cause**: VS Code Snap package sets conflicting environment variables
   - **Solution**: Use `./launch_simulation_clean.sh` instead of direct ros2 launch
   - The script automatically cleans up Snap-related paths and environment variables
   - Alternatively, install VS Code via apt/deb package instead of Snap

2. **ArduPilot path not found**: 
   - Ensure ArduPilot is cloned to `~/ardupilot`
   - Update the path in `simulation.launch.py` if installed elsewhere

3. **MAVROS connection fails**:
   - Verify ArduPilot SITL is running and listening on port 14550
   - Check firewall settings: `sudo ufw allow 14550`

4. **Gazebo world not found**:
   - Ensure all packages are built successfully
   - Check world file exists in `drone_gazebo/worlds/`

5. **Build errors**:
   ```bash
   # Clean and rebuild
   cd ~/urc-drone/simulation/ros2_ws
   rm -rf build install log
   colcon build
   ```

6. **Missing dependencies**:
   ```bash
   # Reinstall dependencies
   rosdep install --from-paths src --ignore-src -r -y
   ```

7. **Workspace not building with launch_simulation_clean.sh**:
   - The script only builds if `install/` doesn't exist
   - For clean rebuild, delete the directory first:
     ```bash
     cd ~/urc-drone/simulation/ros2_ws
     rm -rf build/ install/ log/
     ```
   - Or use the build script directly: `./build.sh clean`

### Log Files

Check log files for detailed error information:
```bash
# ROS2 logs
ls ~/.ros/log/

# Colcon build logs
cd ~/urc-drone/simulation/ros2_ws
ls log/latest_build/
```

## Supporting Evidence

[Videos of the running simulation](https://gtvault-my.sharepoint.com/:f:/g/personal/vhavriutkin3_gatech_edu/EhilfnMA3hFOohFR_kGznW0BpV0GipMPK1ZKRfFsYTg-5g?e=MBskEh) can be found at the provided link.
