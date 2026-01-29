#!/usr/bin/env python3
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

"""Test script demonstrating BBoxNavigationModule integration with ObjectDBTrackingModule."""

import logging
import time

from dimos_lcm.sensor_msgs import CameraInfo
from lcm_msgs.foxglove_msgs import SceneUpdate

from dimos.agents2.spec import Model, Provider
from dimos.core import LCMTransport, start
from dimos.msgs.foxglove_msgs import ImageAnnotations
from dimos.msgs.geometry_msgs import PoseStamped
from dimos.msgs.sensor_msgs import Image, PointCloud2
from dimos.msgs.vision_msgs import Detection2DArray
from dimos.navigation.bbox_navigation import BBoxNavigationModule
from dimos.perception.detection2d.moduleDB import ObjectDBTrackingModule
from dimos.protocol.pubsub import lcm
from dimos.robot.unitree_webrtc.modular import deploy_connection
from dimos.robot.unitree_webrtc.modular.connection_module import ConnectionModule
from dimos.utils.logging_config import setup_logger

logger = setup_logger(__name__, level=logging.INFO)


def test_bbox_integration():
    """Test BBoxNavigationModule integration with ObjectDBTrackingModule."""

    # Start DimOS
    dimos = start(6)

    # Deploy connection module
    connection = deploy_connection(dimos)

    # Define navigation callback
    def goto(pose: PoseStamped):
        logger.info(f"NAVIGATION REQUESTED to: {pose.position}")
        return True

    # Deploy ObjectDBTrackingModule with tracking capability
    object_db = dimos.deploy(
        ObjectDBTrackingModule,
        goto=goto,
        camera_info=ConnectionModule._camera_info(),
    )

    # Connect ObjectDB inputs
    object_db.image.connect(connection.video)
    object_db.pointcloud.connect(connection.lidar)

    # Set up ObjectDB outputs (including new tracked_object output)
    object_db.annotations.transport = LCMTransport("/annotations", ImageAnnotations)
    object_db.detections.transport = LCMTransport("/detections", Detection2DArray)
    object_db.scene_update.transport = LCMTransport("/scene_update", SceneUpdate)
    object_db.tracked_object.transport = LCMTransport("/tracked_object", Detection2DArray)

    # Deploy BBoxNavigationModule
    bbox_nav = dimos.deploy(BBoxNavigationModule, goal_distance=2.0)

    # Connect BBoxNav inputs
    # KEY: Connect to tracked_object output, not general detections
    bbox_nav.detection2d.connect(object_db.tracked_object)
    bbox_nav.camera_info.transport = LCMTransport("/go2/camera_info", CameraInfo)

    # BBoxNav output goes to navigation system
    bbox_nav.goal_request.transport = LCMTransport("/bbox_goal", PoseStamped)

    # Start modules
    object_db.start()
    connection.start()
    bbox_nav.start()

    # Set up agent for testing
    from dimos.agents2 import Agent
    from dimos.agents2.cli.human import HumanInput

    agent = Agent(
        system_prompt="""Robot control assistant with visual tracking.

        Skills:
        - track(target) - Track object by ID (obj_0) or class (person)
        - stop_tracking() - Stop tracking
        - list_objects() - List detected objects
        """,
        model=Model.GPT_4O,
        provider=Provider.OPENAI,
    )

    human_input = dimos.deploy(HumanInput)
    agent.register_skills(human_input)
    agent.register_skills(object_db)  # Register ObjectDB skills

    agent.run_implicit_skill("human")
    agent.start()

    logger.info("=" * 60)
    logger.info("BBox Navigation with ObjectDBTrackingModule")
    logger.info("=" * 60)
    logger.info("Architecture:")
    logger.info("  ObjectDBTrackingModule (extends ObjectDBModule)")
    logger.info("       ↓                        ↓")
    logger.info("  detections (all)      tracked_object (single)")
    logger.info("                                ↓")
    logger.info("                    BBoxNavigationModule")
    logger.info("                                ↓")
    logger.info("                         Navigation Goal")
    logger.info("")
    logger.info("Clean separation:")
    logger.info("  - ObjectDBModule: Base functionality")
    logger.info("  - ObjectDBTrackingModule: Adds tracking + tracked_object output")
    logger.info("  - BBoxNav connects ONLY to tracked_object")
    logger.info("  - Object3D IS Detection2D (no conversion)")
    logger.info("")
    logger.info("Commands:")
    logger.info('  - "Track person" - Track most prominent person')
    logger.info('  - "Track obj_0" - Track specific object by ID')
    logger.info('  - "Stop tracking" - Stop tracking')
    logger.info("=" * 60)

    try:
        agent.loop_thread()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        connection.stop()
        logger.info("Shutting down...")


def main():
    lcm.autoconf()
    test_bbox_integration()


if __name__ == "__main__":
    main()