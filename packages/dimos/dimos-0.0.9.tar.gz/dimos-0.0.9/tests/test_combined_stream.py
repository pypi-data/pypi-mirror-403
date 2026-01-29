#!/usr/bin/env python3
import os
import sys
import time
import cv2
import numpy as np
import rclpy
from reactivex import operators as ops

# Add the parent directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dimos.robot.unitree.unitree_go2 import UnitreeGo2
from dimos.robot.unitree.unitree_ros_control import UnitreeROSControl
from dimos.perception.spatial_perception import SpatialPerception


def extract_position(transform):
    """Extract position coordinates from a transform message"""
    if transform is None:
        return (0, 0, 0)

    pos = transform.transform.translation
    return (pos.x, pos.y, pos.z)


def main():
    print("Hi from: test_combined_stream.py")
    print("Current working directory:", os.getcwd())

    # Initialize ROS
    rclpy.init()

    # Create robot control
    ros_control = UnitreeROSControl(
        node_name="test_combined_stream",
        mock_connection=False,  # Set to False when testing on a real robot
    )

    # Create robot
    robot = UnitreeGo2(ip=os.getenv("ROBOT_IP"), ros_control=ros_control)

    # Get video stream at 8 FPS
    print("Starting ROS video stream at 8 FPS...")
    video_stream = robot.get_ros_video_stream()

    # Get transform stream in pull-based mode (no rate_hz specified)
    print("Setting up pull-based transform stream...")
    transform_stream = ros_control.get_transform_stream(
        child_frame="map",
        parent_frame="base_link",
        rate_hz=None,  # Pull-based mode
    )

    # Counter for received frames
    frame_count = 0

    # Define the subscriber function
    def on_combined_data(data):
        nonlocal frame_count
        frame_count += 1

        # Extract frame and position
        frame = data["frame"]
        position = data["position"]

        # Print information about the received data
        print(
            f"Frame #{frame_count} at position: ({position[0]:.3f}, {position[1]:.3f}, {position[2]:.3f})"
        )

        # Display the frame (optional)
        # cv2.imshow("Combined Stream", frame)
        # cv2.waitKey(1)

    # Combine video frames with their corresponding transforms
    print("Creating combined stream...")
    combined_stream = video_stream.pipe(
        ops.with_latest_from(transform_stream),
        ops.map(lambda pair: {"frame": pair[0], "position": extract_position(pair[1])}),
    )

    # Subscribe to the combined stream
    print("Subscribing to combined stream...")
    subscription = combined_stream.subscribe(
        on_next=on_combined_data,
        on_error=lambda e: print(f"Error in stream: {e}"),
        on_completed=lambda: print("Stream completed"),
    )

    print("Running stream test for 30 seconds or until interrupted...")
    try:
        start_time = time.time()
        while time.time() - start_time < 30:
            rclpy.spin_once(ros_control._node, timeout_sec=0.1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        print("Cleaning up resources...")
        # Dispose of the subscription
        subscription.dispose()

        # Clean up robot resources
        try:
            robot.cleanup()
        except Exception as e:
            print(f"Error during cleanup: {e}")

        # Shut down ROS
        rclpy.shutdown()
        print("Test complete.")


if __name__ == "__main__":
    main()
