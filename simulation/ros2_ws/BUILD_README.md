# ROS2 Workspace Build Script

## Overview

The `build.sh` script automates the build process for the URC Drone ROS2 workspace and handles proper installation of Python package executables.

## Why This Script?

Python packages in ROS2 sometimes install executables in `install/package_name/bin/` instead of the expected `install/package_name/lib/package_name/` location. ROS2's launch system and `ros2 pkg executables` command expect executables to be in `lib/package_name/`. 

This script:
1. Builds all packages with `--symlink-install`
2. Checks for executables in `bin/` directories
3. Creates symlinks in `lib/package_name/` pointing to `bin/` executables
4. Ensures all executables are discoverable by ROS2

## Usage

### Normal Build

```bash
cd ~/Programming/urc-drone/simulation/ros2_ws
./build.sh
```

### Clean Build

```bash
cd ~/Programming/urc-drone/simulation/ros2_ws
./build.sh clean
```

This will:
1. Delete `build/`, `install/`, and `log/` directories
2. Rebuild all packages from scratch
3. Fix executable locations

## After Building

Source the workspace:

```bash
source install/setup.bash
```

Verify executables are available:

```bash
ros2 pkg executables drone_hardware
ros2 pkg executables drone_control
ros2 pkg executables simple_offboard
```

## Affected Packages

The script currently handles:
- `drone_control` - mission_manager, geolocation nodes
- `drone_hardware` - gimbal bridge nodes
- `simple_offboard` - takeoff node

## Technical Details

### The Problem

When using setuptools with `console_scripts` entry points, executables can be installed in:
- **Expected:** `install/package_name/lib/package_name/executable`
- **Actual (sometimes):** `install/package_name/bin/executable`

This happens due to setuptools installation behavior with certain Python configurations.

### The Solution

Create symlinks from `lib/package_name/executable` → `../../bin/executable` so ROS2 can find them in both locations.

## Troubleshooting

### Executables not found after build

```bash
# Rebuild with clean
./build.sh clean

# Verify executables exist
ls -la install/drone_hardware/lib/drone_hardware/
ls -la install/drone_hardware/bin/
```

### Permission denied

```bash
chmod +x build.sh
```

### ROS2 not found

Ensure ROS2 Jazzy is installed and sourced:
```bash
source /opt/ros/jazzy/setup.bash
```
