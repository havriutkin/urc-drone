#!/bin/bash
source /opt/ros/jazzy/setup.bash

echo "=== Setting ArduPilot Gimbal Parameters via MAVROS ==="
echo "Make sure simulation is running!"
echo ""

# Set MNT1_TYPE to 1 (servo gimbal)
echo "1. Setting MNT1_TYPE = 1 (servo gimbal)..."
ros2 service call /mavros/param/set mavros_msgs/srv/ParamSetV2 "{
  force_set: true,
  param_id: 'MNT1_TYPE',
  value: {type: 2, integer_value: 1}
}"

sleep 1

# Set MNT1_DEFLT_MODE to 3 (MAVLink targeting)
echo ""
echo "2. Setting MNT1_DEFLT_MODE = 3 (MAVLink targeting)..."
ros2 service call /mavros/param/set mavros_msgs/srv/ParamSetV2 "{
  force_set: true,
  param_id: 'MNT1_DEFLT_MODE',
  value: {type: 2, integer_value: 3}
}"

sleep 1

# Set servo channels
echo ""
echo "3. Setting servo channels..."
ros2 service call /mavros/param/set mavros_msgs/srv/ParamSetV2 "{
  force_set: true,
  param_id: 'SERVO8_FUNCTION',
  value: {type: 2, integer_value: 6}
}"

ros2 service call /mavros/param/set mavros_msgs/srv/ParamSetV2 "{
  force_set: true,
  param_id: 'SERVO9_FUNCTION',
  value: {type: 2, integer_value: 7}
}"

ros2 service call /mavros/param/set mavros_msgs/srv/ParamSetV2 "{
  force_set: true,
  param_id: 'SERVO10_FUNCTION',
  value: {type: 2, integer_value: 8}
}"

sleep 1

# Set angle limits
echo ""
echo "4. Setting angle limits..."
ros2 service call /mavros/param/set mavros_msgs/srv/ParamSetV2 "{
  force_set: true,
  param_id: 'MNT1_PITCH_MIN',
  value: {type: 3, double_value: -13500.0}
}"

ros2 service call /mavros/param/set mavros_msgs/srv/ParamSetV2 "{
  force_set: true,
  param_id: 'MNT1_PITCH_MAX',
  value: {type: 3, double_value: 4500.0}
}"

ros2 service call /mavros/param/set mavros_msgs/srv/ParamSetV2 "{
  force_set: true,
  param_id: 'MNT1_ROLL_MIN',
  value: {type: 3, double_value: -3000.0}
}"

ros2 service call /mavros/param/set mavros_msgs/srv/ParamSetV2 "{
  force_set: true,
  param_id: 'MNT1_ROLL_MAX',
  value: {type: 3, double_value: 3000.0}
}"

ros2 service call /mavros/param/set mavros_msgs/srv/ParamSetV2 "{
  force_set: true,
  param_id: 'MNT1_YAW_MIN',
  value: {type: 3, double_value: -16000.0}
}"

ros2 service call /mavros/param/set mavros_msgs/srv/ParamSetV2 "{
  force_set: true,
  param_id: 'MNT1_YAW_MAX',
  value: {type: 3, double_value: 16000.0}
}"

echo ""
echo "=== Parameters Set! ==="
echo ""
echo "Testing gimbal control..."
sleep 2

# Test gimbal
echo "Sending gimbal command via mission_manager..."
ros2 service call /mission_manager/random_gimbal std_srvs/srv/Trigger

echo ""
echo "Watch the gimbal in Gazebo!"
echo ""
echo "If it still doesn't work, ArduPilot may need to be restarted to initialize gimbal subsystem."
