# Simulation

## Setup Environment

1.  **Ensure Ubuntu 24 is used**

2.  **Install ROS2 Jazzy**
    ```bash
    sudo apt update
    sudo apt install software-properties-common
    sudo add-apt-repository universe
    sudo apt install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev
     
    sudo apt update && sudo apt install curl -y
    export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
    curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
    sudo dpkg -i /tmp/ros2-apt-source.deb
    sudo apt update && sudo apt install ros-dev-tools 
    sudo apt install ros-jazzy-desktop
    ```

3.  **Install Gazebo**
    ```bash
    # Add the GPG key
    sudo wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
    
    # Add the repository source
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
    
    # Install Gazebo Harmonic
    sudo apt update
    sudo apt install gz-harmonic
    
    # Check installation
    gz sim -v4 shapes.sdf
    ```

4.  **Clone and build Ardupilot**
    ```bash
    git clone https://github.com/ArduPilot/ardupilot.git
    cd ardupilot
    git submodule update --init --recursive
    
    # Install dependencies
    pip install MAVProxy pymavlink
    sudo apt install build-essential
    ./Tools/environment_install/install-prereqs-ubuntu.sh -y
    
    # Reload the shell to apply changes
    . ~/.bashrc
    ```

5.  **Install Mavros**
    ```bash
    sudo apt update
    sudo apt install ros-jazzy-mavros ros-jazzy-mavros-extras
    ```

6.  **Install geographic tools for GPS module**
    ```bash
    sudo apt update
    sudo apt install geographiclib-tools
    sudo geographiclib-get-geoids egm96-5
    ```

## Running the simulation

You need to create 4 separate terminals:

### 1. Gazebo Terminal
Start Gazebo with the specified world file.
```bash
gz sim -v4 -r iris_runway.sdf
```

### 2. Ardupilot Terminal
In the `ardupilot` directory, start the Ardupilot SITL.
```bash
./Tools/autotest/sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON --map --console
```

### 3. Mavros Terminal
This terminal runs the MAVROS connection.
```bash
# Source ROS2 environment
source /opt/ros/jazzy/setup.bash

# Launch MAVROS
ros2 launch mavros apm.launch fcu_url:=udp://127.0.0.1:14550@
```

### 4. Custom Node Terminal
In this terminal, you will build and run the custom offboard control node.
```bash
# Source ROS2 environment
source /opt/ros/jazzy/setup.bash

# Navigate to the ROS2 workspace
cd ros2_ws

# Build the package
colcon build --packages-select simple_offboard

# Run the takeoff node (ensure other terminals are running)
ros2 run simple_offboard takeoff_node
```
This will call the takeoff sequence, which you can observe in the Gazebo simulation.

## Supporting Evidence

[Videos of the running simulation](https://gtvault-my.sharepoint.com/:f:/g/personal/vhavriutkin3_gatech_edu/EhilfnMA3hFOohFR_kGznW0BpV0GipMPK1ZKRfFsYTg-5g?e=MBskEh) can be found at the provided link.
