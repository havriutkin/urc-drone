# Gimbal Bridge Architecture

## Overview

The gimbal bridge provides a hardware abstraction layer between ArduPilot/MAVROS gimbal commands and the actual gimbal hardware (or simulation). This allows the same high-level gimbal control code to work in both simulation and on the real drone.

## Architecture

```
┌─────────────────┐
│ Mission Manager │  (High-level control)
│ or Pilot Input  │
└────────┬────────┘
         │ /mavros/gimbal_control/manager/pitchyaw
         ▼
┌─────────────────┐
│    MAVROS       │  (MAVLink ↔ ROS2 bridge)
└────────┬────────┘
         │ MAVLink gimbal commands
         ▼
┌─────────────────┐
│   ArduPilot     │  (Flight controller)
│   Mount/Gimbal  │
│   Subsystem     │
└────────┬────────┘
         │ /mavros/mount_control/orientation (Quaternion)
         ▼
┌─────────────────────────────────────┐
│      Gimbal Bridge                  │  ◄── ABSTRACTION LAYER
│  ┌────────────┬──────────────────┐  │
│  │ Simulation │  Real Hardware   │  │
│  │  Version   │     Version      │  │
│  └────────────┴──────────────────┘  │
└─────────┬───────────────────┬───────┘
          │                   │
          ▼                   ▼
  ┌──────────────┐    ┌──────────────┐
  │   Gazebo     │    │ Real Servos  │
  │   Topics     │    │ (PCA9685/    │
  │              │    │  Maestro)    │
  └──────────────┘    └──────────────┘
```

## Component Details

### 1. ArduPilot Gimbal Configuration

ArduPilot is configured with a **Type 1 (Servo) gimbal**:
- `MNT1_TYPE = 1` - Servo-controlled gimbal
- `MNT1_DEFLT_MODE = 3` - MAVLink targeting mode
- `SERVO8_FUNCTION = 6` - Roll control
- `SERVO9_FUNCTION = 7` - Pitch control
- `SERVO10_FUNCTION = 8` - Yaw control

**Why Type 1?** While ArduPilot accepts gimbal commands and processes them through the mount subsystem, it doesn't directly output PWM to servos in our setup. The gimbal bridge intercepts the processed orientation and handles the actual hardware interface.

### 2. Gimbal Bridge (Simulation)

**File:** `drone_hardware/gimbal_bridge_sim.py`

**Purpose:** Connects ArduPilot gimbal output to Gazebo simulation.

**Data Flow:**
1. Subscribes to `/mavros/mount_control/orientation` (Quaternion)
2. Converts quaternion to Euler angles (roll, pitch, yaw)
3. Publishes to Gazebo topics:
   - `/gimbal/cmd_pitch` (Float64)
   - `/gimbal/cmd_roll` (Float64)
   - `/gimbal/cmd_yaw` (Float64)

**Launch:** Automatically started by `sim_bringup.launch.py`

```python
# Key functionality
def mount_orientation_callback(self, msg):
    # Convert quaternion to Euler
    roll, pitch, yaw = self.quaternion_to_euler(msg)
    
    # Publish to Gazebo
    self.pitch_pub.publish(Float64(data=pitch))
    self.roll_pub.publish(Float64(data=roll))
    self.yaw_pub.publish(Float64(data=yaw))
```

### 3. Gimbal Bridge (Real Hardware)

**File:** `drone_hardware/gimbal_bridge_real.py`

**Purpose:** Connects ArduPilot gimbal output to real servo hardware.

**Status:** **PLACEHOLDER IMPLEMENTATION** - To be implemented when hardware is available.

**Planned Data Flow:**
1. Subscribe to `/mavros/mount_control/orientation` (Quaternion)
2. Convert quaternion to Euler angles
3. Convert angles to servo pulse widths (1000-2000 µs)
4. Send PWM commands to servo controller (e.g., PCA9685, Pololu Maestro)

**Launch:** Automatically started by `real_bringup.launch.py`

**TODO for real hardware:**
```python
# Example pseudo-code for future implementation
def mount_orientation_callback(self, msg):
    roll, pitch, yaw = self.quaternion_to_euler(msg)
    
    # Convert to servo pulses
    pitch_pulse = self.euler_to_servo_pulse(pitch, 
        min_angle=-135°, max_angle=45°)
    roll_pulse = self.euler_to_servo_pulse(roll,
        min_angle=-30°, max_angle=30°)
    yaw_pulse = self.euler_to_servo_pulse(yaw,
        min_angle=-160°, max_angle=160°)
    
    # Send to servo controller
    self.servo_controller.set_pulse(PITCH_CH, pitch_pulse)
    self.servo_controller.set_pulse(ROLL_CH, roll_pulse)
    self.servo_controller.set_pulse(YAW_CH, yaw_pulse)
```

## Why Use a Bridge?

### Problem

ArduPilot's Type 1 (servo) gimbal accepts MAVLink gimbal manager commands but doesn't output servo PWM signals in our simulation setup. Type 4 (SToRM32 MAVLink) requires an actual MAVLink gimbal device to be present.

### Solution

The bridge acts as a "hardware abstraction layer":

1. **Simulation:** ArduPilot processes gimbal commands → Bridge converts to Gazebo topics
2. **Real Hardware:** ArduPilot processes gimbal commands → Bridge converts to servo PWM

This approach:
- **Keeps ArduPilot gimbal logic intact** (targeting, stabilization, limits)
- **Works with standard MAVLink gimbal commands**
- **Allows same code to work in sim and real hardware**
- **Provides clean separation of concerns**

## Usage

### In Simulation

The bridge runs automatically when you launch the simulation:

```bash
ros2 launch drone_bringup sim_bringup.launch.py
```

Control the gimbal:
```bash
# Using mission_manager service
ros2 service call /mission_manager/set_gimbal_attitude \
  drone_interfaces/srv/SetGimbalAttitude \
  "{pitch: -45.0, roll: 0.0, yaw: 30.0}"

# Or using MAVROS directly
ros2 service call /mavros/gimbal_control/manager/pitchyaw \
  mavros_msgs/srv/GimbalManagerPitchyaw \
  "{pitch: -45.0, yaw: 30.0, pitch_rate: 0.0, yaw_rate: 0.0, flags: 0, gimbal_device_id: 0}"
```

### On Real Hardware

When hardware is available:

1. Implement servo controller interface in `gimbal_bridge_real.py`
2. Configure servo controller I2C/serial connection
3. Launch with real hardware:
   ```bash
   ros2 launch drone_bringup real_bringup.launch.py
   ```

## Debugging

### Check bridge is running:
```bash
ros2 node list | grep gimbal_bridge
```

### Monitor MAVROS mount orientation:
```bash
ros2 topic echo /mavros/mount_control/orientation
```

### Monitor Gazebo gimbal commands (simulation only):
```bash
gz topic -e -t /gimbal/cmd_pitch
gz topic -e -t /gimbal/cmd_roll
gz topic -e -t /gimbal/cmd_yaw
```

### Test direct Gazebo control (bypassing bridge):
```bash
gz topic -t /gimbal/cmd_pitch -m gz.msgs.Double -p 'data: -0.785'  # -45°
```

## Troubleshooting

### Gimbal not moving in simulation

1. **Check bridge is running:**
   ```bash
   ros2 node list | grep gimbal_bridge_sim
   ```

2. **Check MAVROS orientation is being published:**
   ```bash
   ros2 topic hz /mavros/mount_control/orientation
   ```
   Should show ~10-50 Hz when gimbal commands are sent

3. **Check ArduPilot gimbal parameters:**
   ```bash
   grep "MNT1_TYPE\|MNT1_DEFLT_MODE" ~/ardupilot/mav.parm
   ```
   Should show: `MNT1_TYPE 1` and `MNT1_DEFLT_MODE 3`

4. **Check bridge logs:**
   ```bash
   ros2 node info /gimbal_bridge_sim
   ```

### Bridge not starting

1. **Rebuild package:**
   ```bash
   cd ~/Programming/urc-drone/simulation/ros2_ws
   colcon build --packages-select drone_hardware
   source install/setup.bash
   ```

2. **Check dependencies:**
   ```bash
   ros2 pkg executables drone_hardware
   ```
   Should list: `gimbal_bridge_sim` and `gimbal_bridge_real`

## Implementation Notes

### Coordinate Systems

- **ArduPilot:** Uses NED (North-East-Down) frame
- **Gazebo:** Uses ENU (East-North-Up) frame for world, but gimbal joints use local frames
- **Bridge:** Handles quaternion → Euler conversion, maintains angle semantics

### Angle Ranges

Configured in `~/ardupilot/mav.parm`:
- **Pitch:** -135° to +45° (looking down to slightly up)
- **Roll:** -30° to +30° (small stabilization)
- **Yaw:** -160° to +160° (nearly full rotation)

### Performance

- Bridge runs at same rate as MAVROS mount updates (~10-50 Hz)
- Negligible latency (<1ms) for quaternion conversion
- No filtering - relies on ArduPilot's internal gimbal stabilization

## Future Enhancements

### For Real Hardware:

1. **Servo Controller Integration:**
   - Add PCA9685 I2C driver support
   - Add Pololu Maestro serial support
   - Calibration routine for servo limits

2. **Safety Features:**
   - Servo rate limiting
   - Overcurrent protection monitoring
   - Failsafe positions

3. **Calibration:**
   - Auto-calibration for servo centers
   - Physical limit detection
   - Servo trim adjustment

### For Simulation:

1. **Latency Simulation:**
   - Add configurable delay to match real hardware
   
2. **Noise Injection:**
   - Simulate servo jitter/backlash

## Related Documentation

- **Build System:** `ros2_ws/BUILD_README.md` - Workspace build script documentation
- **Manual Commands:** `MANUAL_COMMANDS.md` - Testing and debugging commands
- **Mission Manager:** `drone_control/mission_manager.py` - High-level gimbal control interface
- **Main README:** `README.md` - Complete setup and usage guide

## References

- ArduPilot Mount Documentation: https://ardupilot.org/copter/docs/common-cameras-and-gimbals.html
- MAVLink Gimbal Protocol: https://mavlink.io/en/services/gimbal_v2.html
- MAVROS Gimbal Plugin: http://wiki.ros.org/mavros/Plugins#mount__gimbal_control
