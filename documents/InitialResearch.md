# Project Research Summary: Platforms and Protocols

This document summarizes the initial research phase, covering the existing codebase, platform selection, and the communication protocol for the custom gimbal.

---

## 1. Existing Codebase Review

An investigation into the previous team's codebase revealed that it is largely outdated or incomplete. Most of the code is not suitable for direct reuse in the current project.

* **Key Finding:** The only significant asset identified is the `urc_gazebo` package. It contains a template **URDF (Unified Robot Description Format) file** for a drone model equipped with simulated GPS and lidar sensors. This file will serve as a valuable starting point for building our Gazebo simulation environment.

---

## 2. Platform and Software Selection

The following platforms have been chosen for the drone's primary control and computation systems.

* ### Flight Computer: Raspberry Pi with ROS2
    * **Rationale:** We will use **ROS2 (Robot Operating System 2)** on a Raspberry Pi. This choice is based on ROS2's strong reputation in the robotics community, extensive documentation, and robust ecosystem of tools, which will accelerate development. 🤖

* ### Flight Controller: Pixhawk with ArduPilot
    * **Rationale:** The **Pixhawk flight controller running ArduPilot** will be used. This system was already installed on the previous version of the drone and demonstrated reliable performance. Additionally, it integrates seamlessly with the **Mission Planner** ground control station software, which is a powerful tool for flight planning and monitoring.

---

## 3. Gimbal Control and Communication Protocol

A key challenge is integrating our custom 2-axis gimbal, which communicates via an I2C connection.

* ### The Architectural Challenge
    The initial idea was to connect the gimbal's I2C interface directly to the Raspberry Pi. However, this approach was rejected because it would violate the principle of **abstraction**. The high-level flight computer (Raspberry Pi) should not be responsible for low-level hardware signaling.

* ### Chosen Solution: MAVLink Abstraction Layer
    We have decided on a more robust and modular architecture in collaboration with the firmware team. The control signal flow will be as follows:

    1.  **ROS2 Control Node:** A node on the Raspberry Pi sends high-level gimbal control commands (e.g., target angle) using the **MAVLink protocol** (via MAVROS).
    2.  **Ethernet Communication:** These MAVLink messages are sent from the Raspberry Pi to the Pixhawk over an Ethernet connection.
    3.  **MAVLink-to-PWM Conversion:** The Pixhawk will be configured to interpret these specific MAVLink messages and translate them into low-level **PWM (Pulse Width Modulation) signals**.
    4.  **Gimbal Firmware:** The gimbal's onboard firmware team is responsible for interpreting these PWM signals to drive the gimbal motors.

    This approach ensures a clean separation of concerns, allowing the software team to focus on high-level logic in ROS2 while the firmware team handles the low-level hardware control. 👍

---

## 4. ArduPilot Configuration for MAVLink Gimbal

To configure the Pixhawk to convert MAVLink commands into PWM signals for the gimbal, you will need to set several parameters in ArduPilot using Mission Planner or a similar GCS.

The general process involves three main steps:

1.  **Set the Mount Type:** You must tell ArduPilot that a MAVLink-controlled gimbal is attached.
    * Set the parameter `MNT1_TYPE` to **4** ("MAVLink Targeting"). This configures the mount to accept target angles from a companion computer via MAVLink messages like `MAV_CMD_DO_MOUNT_CONTROL`.

2.  **Assign Gimbal Functions to PWM Outputs:** You need to map the gimbal's pan and tilt functions to the physical PWM output pins on the Pixhawk.
    * For the Tilt motor, find an unused output (e.g., SERVO9) and set its function: `SERVO9_FUNCTION` to **7** ("Mount1 Tilt").
    * For the Pan motor, find another unused output (e.g., SERVO10) and set its function: `SERVO10_FUNCTION` to **8** ("Mount1 Pan").

3.  **Configure Angle and PWM Limits:** Define the operational range for the gimbal.
    * Set the min/max angle limits (in degrees), for example: `MNT1_PITCH_MIN` to **-90** and `MNT1_PITCH_MAX` to **0**.
    * Set the corresponding min/max PWM values for the assigned servo outputs, for example: `SERVO9_MIN` to **1000** and `SERVO9_MAX` to **2000**.

### **Official Documentation Links:**

* **[ArduPilot Servo Gimbal Configuration](https://ardupilot.org/copter/docs/common-camera-gimbal.html):** This is the primary guide. It explains all the parameters mentioned above (`MNT1_TYPE`, angle limits, etc.) for setting up a PWM-based gimbal.