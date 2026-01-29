import tests.test_header

from dimos.robot.unitree.unitree_go2 import UnitreeGo2
from dimos.robot.unitree.unitree_skills import MyUnitreeSkills
from dimos.robot.unitree.unitree_ros_control import UnitreeROSControl
from dimos.agents.agent import OpenAIAgent
from dimos.web.robot_web_interface import RobotWebInterface
import os

# Initialize robot
robot = UnitreeGo2(
    ip=os.getenv("ROBOT_IP"),
    ros_control=None,
    skills=MyUnitreeSkills(),
    use_ros=False,
    use_webrtc=True,
)

webrtc_video_stream = robot.video_stream.capture_video_as_observable(fps=30)

web_interface = RobotWebInterface(port=5555, video_stream=webrtc_video_stream)

web_interface.run()

try:
    input("Press ESC to exit...")
except KeyboardInterrupt:
    print("\nExiting...")
