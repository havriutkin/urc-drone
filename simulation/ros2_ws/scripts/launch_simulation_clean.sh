#!/bin/bash
# Conda base environment launcher for drone simulation
# This script launches the simulation using conda base environment with system ROS2
# Try this script if regular command fails

# Unset problematic snap-related GTK/GDK environment variables
unset GTK_PATH GTK_EXE_PREFIX GIO_MODULE_DIR GTK_IM_MODULE_FILE LOCPATH GSETTINGS_SCHEMA_DIR
for var in $(env | grep VSCODE_SNAP_ORIG | cut -d= -f1); do unset $var; done

# Prepend system library path and filter snap from LD_LIBRARY_PATH
if [ -n "$LD_LIBRARY_PATH" ]; then
    export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:$(echo "$LD_LIBRARY_PATH" | tr ':' '\n' | grep -v '/snap/' | tr '\n' ':' | sed 's/:$//')"
else
    export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu"
fi

# Source ROS2 Jazzy (this will add ROS2 libraries to LD_LIBRARY_PATH)
source /opt/ros/jazzy/setup.bash

# Source workspace
source install/setup.bash

# Launch simulation
echo "Launching drone simulation..."
ros2 launch drone_bringup sim_bringup.launch.py
