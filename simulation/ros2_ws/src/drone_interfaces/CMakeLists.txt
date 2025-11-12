cmake_minimum_required(VERSION 3.8)
project(drone_interfaces)

# Find necessary packages
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# Generate messages, services, etc.
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/ScanPattern.msg"
  "srv/SetGimbalAttitude.srv"
  # Add other .msg, .srv, .action files here
)

# Install and export the package
ament_package()