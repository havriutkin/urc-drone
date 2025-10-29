cmake_minimum_required(VERSION 3.8)
project(drone_gazebo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find ament_cmake to add install targets
find_package(ament_cmake REQUIRED)

# Install the launch and worlds directories
install(
  DIRECTORY launch worlds
  DESTINATION share/${PROJECT_NAME}
)

ament_package()