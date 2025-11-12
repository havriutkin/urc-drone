#!/bin/bash
# Build script for URC Drone ROS2 workspace
# Handles proper installation of Python package executables

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== URC Drone ROS2 Workspace Build Script ===${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "src/drone_bringup/package.xml" ]; then
    echo -e "${RED}Error: Must be run from ros2_ws directory${NC}"
    echo "Usage: cd ~/Programming/urc-drone/simulation/ros2_ws && ./build.sh"
    exit 1
fi

# Source ROS2
echo -e "${YELLOW}Sourcing ROS2 Jazzy...${NC}"
source /opt/ros/jazzy/setup.bash

# Clean build option
if [ "$1" == "clean" ]; then
    echo -e "${YELLOW}Cleaning build, install, and log directories...${NC}"
    rm -rf build install log
    echo -e "${GREEN}Clean complete!${NC}"
    echo ""
fi

# Build all packages
echo -e "${YELLOW}Building all packages...${NC}"
colcon build --symlink-install

if [ $? -ne 0 ]; then
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}Build successful!${NC}"
echo ""

# Function to create symlinks for executables in bin/ to lib/package_name/
create_symlinks_for_package() {
    local pkg=$1
    local install_dir="install/$pkg"
    
    # Check if package has bin directory with executables
    if [ -d "$install_dir/bin" ]; then
        local bin_files=$(ls "$install_dir/bin/" 2>/dev/null | wc -l)
        
        if [ $bin_files -gt 0 ]; then
            # Check if lib/package_name exists
            if [ ! -d "$install_dir/lib/$pkg" ]; then
                echo -e "${YELLOW}  Creating lib/$pkg directory...${NC}"
                mkdir -p "$install_dir/lib/$pkg"
            fi
            
            # Create symlinks for each executable in bin/
            for exe in "$install_dir/bin"/*; do
                local exe_name=$(basename "$exe")
                local target="$install_dir/lib/$pkg/$exe_name"
                
                # Check if symlink already exists and points correctly
                if [ -L "$target" ]; then
                    if [ "$(readlink "$target")" == "../../bin/$exe_name" ]; then
                        # Symlink already correct
                        continue
                    else
                        # Remove incorrect symlink
                        rm "$target"
                    fi
                elif [ -e "$target" ]; then
                    # File exists but is not a symlink, skip
                    continue
                fi
                
                # Create symlink
                echo -e "${GREEN}  ✓ Linking $exe_name${NC}"
                ln -sf "../../bin/$exe_name" "$target"
            done
        fi
    fi
}

# Fix executable locations for Python packages
echo -e "${YELLOW}Checking executable locations...${NC}"

# List of Python packages that might need symlinks
PYTHON_PACKAGES=(
    "drone_control"
    "drone_hardware"
    "simple_offboard"
)

for pkg in "${PYTHON_PACKAGES[@]}"; do
    if [ -d "install/$pkg" ]; then
        echo -e "${YELLOW}Checking $pkg...${NC}"
        create_symlinks_for_package "$pkg"
    fi
done

echo ""
echo -e "${GREEN}=== Build Complete ===${NC}"
echo ""
echo "To use the workspace, run:"
echo -e "${YELLOW}  source install/setup.bash${NC}"
echo ""
echo "To verify executables:"
echo -e "${YELLOW}  ros2 pkg executables drone_hardware${NC}"
echo -e "${YELLOW}  ros2 pkg executables drone_control${NC}"
echo ""
