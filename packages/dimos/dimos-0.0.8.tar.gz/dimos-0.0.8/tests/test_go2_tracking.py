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

"""Test script for Unitree Go2 with ObjectDBTrackingModule."""

import os
import time
import logging

from dimos.protocol.pubsub import lcm
from dimos.robot.unitree_webrtc.unitree_go2 import UnitreeGo2
from dimos.utils.logging_config import setup_logger

logger = setup_logger(__name__, level=logging.INFO)


def test_go2_with_tracking():
    """Test Unitree Go2 with integrated ObjectDBTrackingModule."""

    # Get robot IP from environment
    ip = os.getenv("ROBOT_IP")
    connection_type = os.getenv("CONNECTION_TYPE", "webrtc")

    # Initialize LCM
    lcm.autoconf()

    logger.info("=" * 60)
    logger.info("Starting Unitree Go2 with ObjectDBTrackingModule")
    logger.info("=" * 60)

    # Create robot instance
    with UnitreeGo2(ip=ip, connection_type=connection_type) as robot:
        logger.info("Robot initialized successfully")

        logger.info("")
        logger.info("Available tracking commands:")
        logger.info("  robot.track_object('person')   # Track nearest person")
        logger.info("  robot.track_object('obj_0')    # Track specific object")
        logger.info("  robot.stop_tracking()           # Stop tracking")
        logger.info("")
        logger.info("ObjectDB skills available via robot.object_db:")
        logger.info("  - track(target)")
        logger.info("  - stop_tracking()")
        logger.info("  - list_objects()")
        logger.info("  - navigate_to_object_by_id(id)")
        logger.info("")
        logger.info("Architecture:")
        logger.info("  ObjectDBTrackingModule")
        logger.info("       ↓")
        logger.info("  tracked_object stream")
        logger.info("       ↓")
        logger.info("  BBoxNavigationModule")
        logger.info("       ↓")
        logger.info("  Navigation goal")
        logger.info("=" * 60)

        # Example: Start tracking after 5 seconds
        time.sleep(5)
        logger.info("Starting to track 'person'...")
        result = robot.track_object("person")
        logger.info(f"Track result: {result}")

        try:
            # Keep running
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("\nStopping tracking...")
            robot.stop_tracking()
            logger.info("Shutting down...")


def main():
    test_go2_with_tracking()


if __name__ == "__main__":
    main()