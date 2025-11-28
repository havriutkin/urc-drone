# Manual Drone Control Commands

This guide shows how to manually control the drone using ROS2 CLI commands.

## Prerequisites

1. Launch the simulation:
```bash
cd /home/havri/Programming/urc-drone/simulation
./launch_simulation_clean.sh
```

2. Wait for MAVROS to connect (check logs for "MAVROS connected!")

## Basic Commands

### Check Vehicle State
```bash
# Monitor state (mode, armed status, connected)
ros2 topic echo /mavros/state

# Monitor GPS position
ros2 topic echo /mavros/global_position/global

# Monitor local position
ros2 topic echo /mavros/local_position/pose
```

### Set Flight Mode
```bash
# Set to GUIDED mode (required for autonomous control)
ros2 service call /mavros/set_mode mavros_msgs/srv/SetMode "{custom_mode: 'GUIDED'}"

# Other modes: STABILIZE, LOITER, RTL, LAND, etc.
ros2 service call /mavros/set_mode mavros_msgs/srv/SetMode "{custom_mode: 'STABILIZE'}"
```

### Arm/Disarm
```bash
# Arm the vehicle
ros2 service call /mavros/cmd/arming mavros_msgs/srv/CommandBool "{value: true}"

# Disarm the vehicle
ros2 service call /mavros/cmd/arming mavros_msgs/srv/CommandBool "{value: false}"
```

### Takeoff
```bash
# Takeoff to 5 meters
ros2 service call /mavros/cmd/takeoff mavros_msgs/srv/CommandTOL "{altitude: 5.0}"

# Takeoff to 10 meters
ros2 service call /mavros/cmd/takeoff mavros_msgs/srv/CommandTOL "{altitude: 10.0}"
```

### Land
```bash
# Land at current position
ros2 service call /mavros/cmd/land mavros_msgs/srv/CommandTOL "{}"
```

## Complete Takeoff Sequence

Execute these commands in order:

```bash
# 1. Set GUIDED mode
ros2 service call /mavros/set_mode mavros_msgs/srv/SetMode "{custom_mode: 'GUIDED'}"

# 2. Arm the vehicle
ros2 service call /mavros/cmd/arming mavros_msgs/srv/CommandBool "{value: true}"

# 3. Takeoff to 5m
ros2 service call /mavros/cmd/takeoff mavros_msgs/srv/CommandTOL "{altitude: 5.0}"

# 4. Monitor altitude
ros2 topic echo /mavros/local_position/pose --field pose.position.z
```

## List Available Services

```bash
# List all MAVROS services
ros2 service list | grep /mavros

# Get service info
ros2 service type /mavros/cmd/arming
ros2 interface show mavros_msgs/srv/CommandBool
```

## List Available Topics

```bash
# List all MAVROS topics
ros2 topic list | grep /mavros

# Get topic info
ros2 topic info /mavros/state
ros2 interface show mavros_msgs/msg/State
```

## Common Flight Modes

- `GUIDED`: Autonomous control via commands
- `STABILIZE`: Manual control (requires RC)
- `LOITER`: Hold position
- `RTL`: Return to launch
- `LAND`: Auto-land
- `ALT_HOLD`: Hold altitude

## Notes

- All commands use `/mavros` namespace (default MAVROS configuration)
- Vehicle must be armed before takeoff
- GUIDED mode is required for autonomous commands
- Check state/position topics to verify commands executed correctly
- To see all available topics: `ros2 topic list`
- To see all available services: `ros2 service list`
