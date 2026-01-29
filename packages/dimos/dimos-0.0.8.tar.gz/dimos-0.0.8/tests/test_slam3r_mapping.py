# Copyright 2025 Dimensional Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import tests.test_header
import os
import time
from dimos.stream.frame_processor import FrameProcessor
from dimos.stream.video_operators import VideoOperators as vops
from dimos.robot.unitree.unitree_go2 import UnitreeGo2
from dimos.robot.unitree.unitree_ros_control import UnitreeROSControl
from dimos.web.robot_web_interface import RobotWebInterface

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Initialize the robot
robot = UnitreeGo2(
    ip=os.getenv("ROBOT_IP"),
    ros_control=UnitreeROSControl(),
)

# Create a frame processor with a specific output directory
frame_processor = FrameProcessor(
    output_dir=os.path.join(os.getcwd(), "assets/output/slam3r_slower"), delete_on_init=True
)

# Get the ROS video stream
video_stream = robot.get_ros_video_stream(fps=30)

# Process the stream to save frames as JPGs
processed_stream = video_stream.pipe(
    vops.with_fps_sampling(fps=5),
    vops.with_jpeg_export(
        frame_processor=frame_processor,
        save_limit=0,  # Optional: limit number of frames to save (0 for unlimited)
        suffix="frame",  # Optional: adds this suffix to filenames
    ),
).subscribe()

# Create a web interface
web_interface = RobotWebInterface(video=video_stream)
web_interface.run()

# Keep the program running
try:
    while True:
        time.sleep(1)
finally:
    # Clean up
    processed_stream.dispose()
    robot.cleanup()
