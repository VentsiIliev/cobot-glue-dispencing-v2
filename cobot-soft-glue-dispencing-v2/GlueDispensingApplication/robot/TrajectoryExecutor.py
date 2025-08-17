# =============================================================================
# NOTE: THIS CLASS IS CURRENTLY NOT IN USE
#
# PURPOSE:
# This class is intended to support asynchronous robot operations by
# separating motion execution and position monitoring into background threads.
# It will allow queuing of movement commands and continuous tracking of
# robot position, enabling more flexible and responsive control.
# =============================================================================


import logging
from queue import Queue, Empty
import threading
import time
from enum import Enum
from GlueDispensingApplication.robot.RobotWrapper import RobotWrapper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')



class ThreadType(Enum):
    MOTION = "motion"
    POSITION = "position"



# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class ThreadType(Enum):
    MOTION = "motion"
    POSITION = "position"


robotIp = '192.168.58.2'

class TrajectoryExecutor():
    def __init__(self, robot):
        self.motionRobot = robot
        self.posRobot = RobotWrapper(robotIp)
        self.motion_queue = Queue()
        self.position_queue = Queue(maxsize=5)

        self.targetPosition = None
        self.tragetPositonThreshold = 0
        self.targetPositionReachedCallback = None
        #[path,startCallback,endCallback]

        self.motionThreadStopSignal = False
        self.motionThreadPauseSignal = False
        self.positionThreadStopSignal = False
        self.positionThreadPauseSignal = False

        self.threads = [
            threading.Thread(target=self.motion_thread),
            threading.Thread(target=self.position_thread)
        ]


    def startThreads(self):

        for t in self.threads:
            t.start()

    def execute(self, acceleration, blendR, robotPath, tool, velocity, workpiece):
        count = 1

        for point in robotPath:
            if count == 0:
                count = 0
                continue
            self.motion_queue.put([point, [tool, workpiece, velocity, acceleration, blendR]])

    def motion_thread(self):
        while not self.motionThreadStopSignal:
            if self.motionThreadPauseSignal:
                time.sleep(0.1)  # Pause the thread for a while
                continue  # Skip further processing and check again

            try:
                move = self.motion_queue.get()
                position = move[0]
                logging.info(f"Moving to: {position} Motion Params: {move[1]}")
                motionParams = move[1]
                self.motionRobot.moveL(position, tool=motionParams[0], user=motionParams[1], vel=motionParams[2],
                                 acc=motionParams[3], blendR=motionParams[4])

            except Empty:
                continue
            except Exception as e:
                logging.error(f"Error in motion_thread: {e}", exc_info=True)

    def position_thread(self):
        while not self.positionThreadStopSignal:
            if self.positionThreadPauseSignal:
                time.sleep(0.1)  # Pause the thread for a while
                continue  # Skip further processing and check again

            try:
                if self.position_queue.full():  # Check if the queue is full
                    # Remove the oldest item to make space for the new one
                    self.position_queue.get()  # Get removes the oldest item
                    # logging.info("Queue full, removed the oldest position.")

                position = self.posRobot.getCurrentPosition()

                if self.targetPosition is not None and self.targetPositionReachedCallback is not None:

                    if abs(position[0] - self.targetPosition[0]) < threshold and abs(
                            position[1] - self.targetPosition[1]) < threshold and abs(position[2] - self.targetPosition[2]) < threshold:
                        self.targetPositionReachedCallback()
                        self.targetPosition = None
                        self.targetPositionReachedCallback = None

                self.position_queue.put(position)  # Add new position
                # logging.info(f"Position added to queue: {position}")

            except Exception as e:
                logging.error("Error getting current position", exc_info=True)
                continue

    # Stop signals for both threads
    def setStopSignal(self):
        self.motionThreadStopSignal = True
        self.positionThreadStopSignal = True
        for t in self.threads:
            t.join()  # Wait for threads to finish gracefully

    # Pause signals for both threads using the ThreadType enum
    def setPauseSignal(self, thread_type: ThreadType):
        if thread_type == ThreadType.MOTION:
            self.motionThreadPauseSignal = True
            logging.info("Motion thread paused.")
        elif thread_type == ThreadType.POSITION:
            self.positionThreadPauseSignal = True
            logging.info("Position thread paused.")

    def resume_thread(self, thread_type: ThreadType):
        if thread_type == ThreadType.MOTION:
            self.motionThreadPauseSignal = False
            logging.info("Motion thread resumed.")
        elif thread_type == ThreadType.POSITION:
            self.positionThreadPauseSignal = False
            logging.info("Position thread resumed.")

