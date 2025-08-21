import math
import time
# from tkinter import messagebox
import queue
import threading
import cv2
import numpy as np

from API.MessageBroker import MessageBroker
# from pl_gui.contour_editor.temp.testTransformPoints import startPosition

from GlueDispensingApplication.tools.GlueNozzleService import GlueNozzleService
from GlueDispensingApplication.robot.RobotWrapper import RobotWrapper
from GlueDispensingApplication.robot.RobotConfig import *
from GlueDispensingApplication.tools.enums import ToolID
from GlueDispensingApplication.tools.enums.ToolID import ToolID
from GlueDispensingApplication.tools.enums.Gripper import Gripper
from GlueDispensingApplication.tools.VacuumPump import VacuumPump
from GlueDispensingApplication.tools.nozzles.Tool1 import Tool1
from GlueDispensingApplication.tools.nozzles.Tool2 import Tool2
from GlueDispensingApplication.tools.nozzles.Tool3 import Tool3
from GlueDispensingApplication.tools.Laser import Laser
from GlueDispensingApplication.robot import RobotUtils
from GlueDispensingApplication.tools.ToolChanger import ToolChanger
import enum
from API.shared.Contour import Contour
from GlueDispensingApplication.SystemStatePublisherThread import SystemStatePublisherThread
import threading
import time
import math

class RobotServiceState(enum.Enum):
    INITIALIZING = "initializing"
    IDLE = "idle"
    STARTING = "starting"
    MOVING_TO_FIRST_POINT = "moving_to_first_point"
    EXECUTING_PATH = "executing_path_state"
    TRANSITION_BETWEEN_PATHS = "transition_between_paths"
    TRACING_CONTOURS = "tracing_contours"
    PERFORMING_NESTING = "performing_nesting"
    COMPLETED = "completed"
    ERROR = "error"

class RobotState(enum.Enum):
    STATIONARY = "stationary"
    ACCELERATING = "accelerating"
    DECELERATING = "decelerating"
    MOVING = "moving"
    ERROR = "error"


class RobotStateManager:
    def __init__(self, controller_cycle_time=0.01, proportional_gain=0.34, speed_threshold=1, accel_threshold=0.001):
        self.robot = RobotWrapper(ROBOT_IP)
        self.pos = None
        self.speed = 0.0
        self.accel = 0.0
        self.robotStateTopic = "robot/state"
        self.robotState = RobotState.STATIONARY  # Initial state

        self.prev_pos = None
        self.prev_time = None
        self.prev_speed = None
        self.trajectoryUpdate = False
        self._stop_event = threading.Event()

        self.following_error_gain = controller_cycle_time / proportional_gain
        self.broker = MessageBroker()

        # Thresholds for determining motion state
        self.speed_threshold = speed_threshold
        self.accel_threshold = accel_threshold

    def compute_speed(self, current_pos, previous_pos, dt):
        dx = current_pos[0] - previous_pos[0]
        dy = current_pos[1] - previous_pos[1]
        dz = current_pos[2] - previous_pos[2]
        distance = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        return distance / dt if dt > 0 else 0.0

    def update_state(self):
        """Update robot motion state based on speed and acceleration."""
        if abs(self.speed) < self.speed_threshold:
            self.robotState = RobotState.STATIONARY
        elif self.accel > self.accel_threshold:
            self.robotState = RobotState.ACCELERATING
        elif self.accel < -self.accel_threshold:
            self.robotState = RobotState.DECELERATING
        else:
            self.robotState = RobotState.MOVING

    def fetch_position(self):
        while not self._stop_event.is_set():
            current_time = time.time()
            try:
                current_pos = self.robot.getCurrentPosition()
            except:
                self.robotState = RobotState.ERROR
                continue

            if current_pos == None:
                self.robotState = RobotState.ERROR

            self.pos = current_pos


            if self.prev_pos is not None:
                dt = current_time - self.prev_time
                self.speed = self.compute_speed(current_pos, self.prev_pos, dt)

                if self.prev_speed is not None:
                    self.accel = (self.speed - self.prev_speed) / dt

                # Determine current robot state
                self.update_state()
                self.broker.publish(self.robotStateTopic, {"state": self.robotState, "speed": self.speed, "accel": self.accel})

                if self.robotState != RobotState.STATIONARY and self.trajectoryUpdate:

                    x = current_pos[0]
                    y = current_pos[1]

                    transformed_point = self.broker.request("vision/transformToCamera", {"x": x, "y": y})
                    t_x = transformed_point[0]
                    t_y = transformed_point[1]
                    # Scale down to 640x360
                    t_x_scaled = int(t_x * 0.5)
                    t_y_scaled = int(t_y * 0.5)

                    self.broker.publish("robot/trajectory/point", {"x": t_x_scaled, "y": t_y_scaled})
                    # print(f"Publishing point: ({t_x_scaled}, {t_y_scaled})")

            self.prev_pos = current_pos
            self.prev_time = current_time
            self.prev_speed = self.speed

            time.sleep(0.01)

    def start_thread(self):
        self._thread = threading.Thread(target=self.fetch_position)
        self._thread.start()

    def stop_thread(self):
        self._stop_event.set()
        self._thread.join()


class RobotService:
    """
     RobotService is a service layer to control and manage robot movements,
     tool operations, grippers, and glue dispensing for industrial automation tasks.
     """
    MIN_Z_VALUE = 250
    RX_VALUE = 180
    RY_VALUE = 0
    RZ_VALUE = 0  # TODO: Change to 0

    TOOL_DEFAULT = 0  # Default tool ID
    USER_DEFAULT = 0  # Default user ID

    def __init__(self, robot, settingsService, glueNozzleService: GlueNozzleService = None):
        """
               Initializes the RobotService with robot control object and configuration services.

               Args:
                   robot: Robot controller object
                   settingsService: Settings service to fetch robot motion parameters
                   glueNozzleService (GlueNozzleService, optional): Glue nozzle control service
               """

        self.logTag = "RobotService"
        self.stateTopic = "robot-service/state"
        self.state= RobotServiceState.INITIALIZING
        self.broker = MessageBroker()
        self.statePublisherThread = SystemStatePublisherThread(self.publishState, 0.1)
        self.statePublisherThread.start()

        self.robot = robot
        self.robot.printSdkVersion()
        self.robotStateManager = RobotStateManager()
        self.robotStateManager.start_thread()
        self.robotState = None
        self.broker.subscribe(self.robotStateManager.robotStateTopic, self.onRobotStateUpdate)

        self.pump = VacuumPump()
        self.laser = Laser()


        # TODO: FINISH IMPLEMENTATION FOR ROBOT SETTINGS
        self.settingsService = settingsService
        self.robotSettings = self.settingsService.robot_settings
        self.glueNozzleService = glueNozzleService
        self.loginPosition = LOGIN_POS
        self.startPosition = HOME_POS
        self.calibrationPosition = CALIBRATION_POS
        self.debugPath = []
        self.currentGripper = None
        self.toolChanger = ToolChanger()
        self.commandQue = queue.Queue()
        self._stop_thread = threading.Event()

    def onRobotStateUpdate(self,state):
        self.robotState = state['state']

        if self.state == RobotServiceState.INITIALIZING and self.robotState == RobotState.STATIONARY:
            self.state = RobotServiceState.IDLE


    def publishState(self):
        # print("Publishing state:", self.state)
        self.broker.publish(self.stateTopic,self.state)

    def getMotionParams(self):
        """
             Retrieves motion parameters from robot settings.

             Returns:
                 tuple: (velocity, tool, user, acceleration, blend radius)
             """
        robotMotionParams = (self.robotSettings.get_robot_velocity(),
                             self.robotSettings.get_robot_tool(),
                             self.robotSettings.get_robot_user(),
                             self.robotSettings.get_robot_acceleration(),
                             1)
        return robotMotionParams

    def zigZag(self, contour, spacing):
        """
             Computes a zigzag path from the contour based on spacing and direction.

             Args:
                 contour (array): Input contour points
                 spacing (float): Spacing between zigzag lines
                 direction (str): Direction of zigzag (e.g., 'horizontal', 'vertical')

             Returns:
                 list: Zigzag path
             """
        path = RobotUtils.zigZag(contour, spacing)
        return path

    def moveToLoginPosition(self):
        currentPos = self.robot.getCurrentPosition()
        x, y, z, rx, ry, rz = currentPos

        if y > 350:
            ret = self.moveToCalibrationPosition()
            if ret != 0:
                return ret

            ret = self.moveToStartPosition()
            if ret != 0:
                return ret
        else:
            ret = self.moveToStartPosition()
            if ret != 0:
                return ret

        ret = self.robot.moveCart(self.loginPosition, self.TOOL_DEFAULT, self.USER_DEFAULT, vel=100, acc=30)
        return ret

    def moveToStartPosition(self):
        """
            Moves the robot to a predefined start position for safe initialization.
            """
        try:
            if not self.robot:
                # replace the tkinter messagebox with a print statement for debugging
                print("Warning: Robot not connected.")
                # messagebox.showwarning("Warning", "Robot not connected.")
                return

            ret = self.robot.moveCart(self.startPosition, self.TOOL_DEFAULT, self.USER_DEFAULT, vel=100, acc=30)
            # print("Moving to start: ", ret)
            return ret
        except Exception as e:
            print("Error moving to start position:", e)
            # messagebox.showerror("Error", f"Error moving to start position: {e}")
            return ret

    def moveToCalibrationPosition(self):
        """
               Moves the robot to the calibration position.
               """
        ret = None
        try:
            if not self.robot:
                print("Warning: Robot not connected.")
                # messagebox.showwarning("Warning", "Robot not connected.")
                return

            ret = self.robot.moveCart(self.calibrationPosition, self.TOOL_DEFAULT, self.USER_DEFAULT, vel=100, acc=30)
            # self._waitForRobotToReachPosition(self.calibrationPosition,1,0)
            # print("Moving to calibration pos: ", ret)
            print("In moveToCalibrationPosition")
            return ret
        except Exception as e:
            print("Error moving to calibration position:", e)
            # messagebox.showerror("Error", f"Error moving to calibration position: {e}")
            return ret

    # def traceContours(self, contours, height, orientation,toolID=None):
    #     """
    #         Traces the given contours with the robot, adjusting height and applying glue if needed.
    #
    #         Args:
    #             contours (list): List of contour point arrays
    #             height (float): Target Z height for tracing
    #             toolID (ToolID, optional): Tool identifier to determine glue type and behavior
    #         """
    #
    #     if self.glueNozzleService is None:
    #         raise Exception(f"[DEBUG] {self.logTag} GlueNozzleService is not initialized.")
    #     # print("ORIENTATION: ",orientation)
    #     self.RZ_VALUE = orientation
    #     # self.positionFether.start_thread()
    #     # self.velFetcher.start_thread()
    #     requiredSprayingHeight, toolTip = self.__getTool(toolID)
    #     threshold = 1
    #     height = self.pump.zOffset + height-10
    #     try:
    #         if not self.robot:
    #             print("Warning: Robot not connected.")
    #             # messagebox.showwarning("        Warning", "Robot not connected.")
    #             return
    #
    #         if toolTip == None:
    #             xOffset = 0
    #             yOffset = 0
    #         else:
    #             xOffset = toolTip.xOffset
    #             yOffset = toolTip.yOffset
    #
    #         # print("     xOffset: ", xOffset, "yOffset: ", yOffset)
    #         robotPaths = []
    #         for cnt in contours:
    #
    #             path = []
    #             for point in cnt:
    #                 point = point[0]
    #                 # print("Point[0] = ", point)
    #                 point[1] = point[1]+1
    #                 path.append((point[0] + xOffset, point[1] + yOffset,
    #                              height, self.RX_VALUE, self.RY_VALUE, self.RZ_VALUE))
    #                 self.debugPath.append((point[0] + xOffset, point[1] + yOffset,
    #                                        height, self.RX_VALUE, self.RY_VALUE, self.RZ_VALUE))
    #             robotPaths.append(path)
    #
    #         velocity, tool, workpiece, acceleration, blendR = self.getMotionParams()
    #
    #         # print("     Path = ", robotPaths)
    #
    #         for path in robotPaths:
    #             startPoint = path[0]
    #             # print("     Start point: ", startPoint)
    #             self.robot.moveCart(startPoint, tool, workpiece, vel=velocity, acc=acceleration)
    #             self._waitForRobotToReachPosition(startPoint, threshold=threshold,
    #                                               delay=0.1)  # TODO comment out when using test robot
    #
    #             if isinstance(toolTip, Tool1):
    #                 self.pump.turnOn(self.robot)
    #             elif isinstance(toolTip, Tool2):
    #
    #                 pass
    #                 # self.glueNozzleService.addCommandToQueue(self.glueNozzleService.startGlueDotsDispensing)
    #                 # self.laser.turnOn()
    #             elif isinstance(toolTip, Tool3):
    #                 self.pump.turnOn(self.robot)
    #             else:
    #
    #                 pass
    #                 # self.glueNozzleService.addCommandToQueue(self.glueNozzleService.startGlueDotsDispensing)
    #                 # self.laser.turnOn()
    #
    #
    #             self.executePathWithMoveL(acceleration, blendR, path, tool, velocity, workpiece)
    #             # self.executePathWithMoveL(1, blendR, path, tool, 1, workpieces)
    #
    #             endPoint = path[-1]
    #             # print("     End point: ", endPoint)
    #             self._waitForRobotToReachPosition(endPoint, threshold=threshold,
    #                                               delay=0)  # TODO comment out when using test robot
    #
    #             # self.positionFether.stop_thread()
    #             # self.velFetcher.stop_thread()
    #
    #             if isinstance(toolTip, Tool1):
    #                 self.pump.turnOff(self.robot)
    #             elif isinstance(toolTip, Tool2):
    #                 # self.glueNozzleService.stopGlueDispensing()
    #                 # self.laser.turnOff()
    #                 # self.glueNozzleService.addCommandToQueue(self.glueNozzleService.stopGlueDispensing)
    #                 pass
    #
    #             elif isinstance(toolTip, Tool3):
    #                 pass
    #                 # self.pump.turnOff(self.robot)
    #             else:
    #                 # self.glueNozzleService.stopGlueDispensing()
    #                 # self.laser.turnOff()
    #                 # self.glueNozzleService.addCommandToQueue(self.glueNozzleService.stopGlueDispensing)
    #                 pass
    #         # # write self.debugPath to txt file
    #         # with open('points.txt', 'w') as f:
    #         #     for point in self.debugPath:
    #         #         f.write(str(point) + "\n")
    #
    #     except Exception as e:
    #         raise Exception(e)

    def traceContours(self, paths):

        print("Tracing contours with paths:", paths)
        # return

        from GlueDispensingApplication.tools.GlueSprayService import GlueSprayService
        from API.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
        from API.shared.settings.conreateSettings.enums.RobotSettingKey import RobotSettingKey

        self.state = RobotServiceState.STARTING

        service = GlueSprayService(generatorTurnOffTimeout=10)
        glueType = service.glueB_addresses

        # Variables to persist across states
        current_path_index = 0
        speedReverse = 10000
        reverseDuration = 1
        delay = 1
        generator_to_glue_delay = 0

        while self.state != RobotServiceState.COMPLETED:
            print("Current State:", self.state)
            if self.state == RobotServiceState.STARTING:
                # Unpack settings for the current path
                path, settings = paths[current_path_index]
                velocity = settings.get(RobotSettingKey.VELOCITY.value)
                acceleration = settings.get(RobotSettingKey.ACCELERATION.value)
                time_before_motion = float(settings.get(GlueSettingKey.TIME_BEFORE_MOTION.value, 1.0))
                reach_start_threshold = float(settings.get(GlueSettingKey.REACH_START_THRESHOLD.value))
                reach_end_threshold = float(settings.get(GlueSettingKey.REACH_END_THRESHOLD.value))
                pumpSpeed = int(settings.get(GlueSettingKey.MOTOR_SPEED.value))
                glue_speed_coefficient = float(settings.get(GlueSettingKey.GLUE_SPEED_COEFFICIENT.value, 1.0))
                reverseDuration = float(settings.get(GlueSettingKey.REVERSE_DURATION.value))
                speedReverse = int(settings.get(GlueSettingKey.SPEED_REVERSE.value))
                generator_to_glue_delay = float(settings.get(GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value))
                fanSpeed = int(settings.get(GlueSettingKey.FAN_SPEED.value))

                # Move to the first point
                try:
                    ret = self.robot.moveCart(path[0], ROBOT_TOOL, ROBOT_USER, vel=30, acc=80)
                    if ret != 0:
                        self.state = RobotServiceState.ERROR
                    else:
                        self.state = RobotServiceState.MOVING_TO_FIRST_POINT
                except:
                    # service.generatorOff()
                    print("Robot could not reach start position, stopping glue dispensing")
                    return

                self._waitForRobotToReachPosition(path[0], reach_start_threshold, 0.1)

                # Turn on generator if off
                if not service.generatorCurrentState:
                    # service.generatorOn()
                    time.sleep(generator_to_glue_delay)

                # time.sleep(time_before_motion)

                self.state = RobotServiceState.EXECUTING_PATH

            elif self.state == RobotServiceState.EXECUTING_PATH:
                self.robotStateManager.trajectoryUpdate = True
                path, settings = paths[current_path_index]
                velocity = settings.get(RobotSettingKey.VELOCITY.value)
                acceleration = settings.get(RobotSettingKey.ACCELERATION.value)
                pumpSpeed = int(settings.get(GlueSettingKey.MOTOR_SPEED.value))
                glue_speed_coefficient = float(settings.get(GlueSettingKey.GLUE_SPEED_COEFFICIENT.value, 1.0))
                reach_end_threshold = float(settings.get(GlueSettingKey.REACH_END_THRESHOLD.value))

                for point in path:
                    ret = self.robot.moveL(point, ROBOT_TOOL, ROBOT_USER, vel=velocity, acc=acceleration, blendR=1)
                    if ret != 0:
                        print(f"MoveL to point {point} failed with error code {ret}")
                        self.state = RobotServiceState.ERROR
                    else:
                        # self.adjustPumpSpeedWhileRobotIsMoving(service, glue_speed_coefficient, glueType, pumpSpeed, point,
                        #                                        reach_end_threshold)
                        # self._waitForRobotToReachPosition(point, reach_end_threshold, 0.1)
                        pass

                # service.motorOff(glueType, speedReverse=speedReverse, delay=reverseDuration)
                # self.positionFetcher.trajectoryUpdate=False
                self.state = RobotServiceState.TRANSITION_BETWEEN_PATHS

            elif self.state == RobotServiceState.TRANSITION_BETWEEN_PATHS:
                current_path_index += 1
                if current_path_index >= len(paths):
                    self.state = RobotServiceState.COMPLETED
                else:
                    self.state = RobotServiceState.MOVING_TO_FIRST_POINT


            else:
                raise ValueError(f"Invalid state: {self.state}")


        # Final cleanup after all paths
        # time.sleep(delay)
        # service.motorOff(glueType, speedReverse=speedReverse, delay=reverseDuration)
        # service.generatorOff()

    def adjustPumpSpeedWhileRobotIsMoving(
            self,
            glueSprayService,
            glue_speed_coefficient,
            motorAddress,
            pumpSpeed,
            endPoint,
            threshold,
            use_second_order=True
    ):
        glueSprayService.motorOn(2,10000)
        time.sleep(1)
        while True:
            currentVel = self.robotStateManager.speed
            accel = self.robotStateManager.accel

            # Following error compensation (1st order)
            predicted_following_error = self.robotStateManager.following_error_gain * currentVel

            # Optional 2nd order: account for accel lag
            if use_second_order:
                predicted_following_error += (self.robotStateManager.following_error_gain * 0.5) * accel

            adjustedPumpSpeed = (currentVel + predicted_following_error) * glue_speed_coefficient
            glueSprayService.motorOn(motorAddress, adjustedPumpSpeed)

            currentPos = self.robotStateManager.pos
            distance = math.sqrt(
                (currentPos[0] - endPoint[0]) ** 2 +
                (currentPos[1] - endPoint[1]) ** 2 +
                (currentPos[2] - endPoint[2]) ** 2
            )

            if distance < threshold:
                break

    def __getTool(self, toolID):
        """
             Gets tool-specific height offset and tool instance based on ToolID.

             Args:
                 toolID (ToolID): Tool ID

             Returns:
                 tuple: (required height offset, tool instance)
             """
        if toolID == ToolID.Tool1:
            return 25, Tool1()
        elif toolID == ToolID.Tool2:
            return 25, Tool2()
        elif toolID == ToolID.Tool3:
            return 25, Tool3()
        elif toolID == ToolID.Tool0:
            return 25, None
        else:
            raise ValueError("Invalid tool ID")

    def _waitForRobotToReachPosition(self, endPoint, threshold, delay):
        """
           Waits until the robot reaches a given position within a threshold.

           Args:
               endPoint (list): Target Cartesian coordinates
               threshold (float): Allowed deviation
               delay (float): Delay between position checks
           """
        while True:
            state = self.robotStateManager.robotState
            if state == RobotState.STATIONARY:
                break
            # time.sleep(delay)
            # print(f"     Waiting for robot to reach end point: {threshold} ")
            # currentPos = self.robot.getCurrentPosition()
            # if currentPos is None:
            #     break
            # # Calculate Euclidean distance in XYZ
            # distance = math.sqrt(
            #     (currentPos[0] - endPoint[0]) ** 2 +
            #     (currentPos[1] - endPoint[1]) ** 2 +
            #     (currentPos[2] - endPoint[2]) ** 2
            # )
            # print(f"Distance to end point: {distance:.3f} mm")
            # if distance < threshold:
            #     break


    def getCurrentPosition(self):
        """
             Gets the current Cartesian position of the robot.

             Returns:
                 list: Current robot position
             """
        return self.robot.getCurrentPosition()

    def query_speed(self):
        """
               Continuously queries the robot's linear speed (for diagnostics or monitoring).
               """
        while True:
            ret = self.robot.getCurrentLinierSpeed()
            currentSpeed = ret[1][0]

    def executePathWithMoveL(self, acceleration, blendR, robotPath, tool, velocity, workpiece):
        """
           Executes a linear movement (MoveL) along a specified path.

           Args:
               acceleration (float): Acceleration value
               blendR (float): Blend radius
               robotPath (list): Sequence of positions
               tool (int): Tool frame ID
               velocity (float): Speed of movement
               workpiece (int): Workpiece frame ID
        """

        def distance_xy(p1, p2):
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            return math.sqrt(dx * dx + dy * dy)

        total_distance = 0
        for i in range(len(robotPath) - 1):
            total_distance += distance_xy(robotPath[i], robotPath[i + 1])

        # Execute moves
        for count, point in enumerate(robotPath):
            if count == 0:
                continue  # Skip first point or if you want to move to first point, remove this line

            # ret = self.robot.moveL(point, tool, workpiece, vel=velocity, acc=acceleration, blendR=blendR)
            ret = self.robot.moveL(point, tool, workpiece, vel=100, acc=100, blendR=blendR)
            print("ret", ret)
            if ret != 0:
                print(f"MoveL to point {count} failed with error code {ret}")
                break

        return total_distance

    # def executePathWithMoveL(self, acceleration, blendR, robotPath, tool, velocity, workpieces):
    #     """
    #        Executes a linear movement (MoveL) along a specified path.
    #
    #        Args:
    #            acceleration (float): Acceleration value
    #            blendR (float): Blend radius
    #            robotPath (list): Sequence of positions
    #            tool (int): Tool frame ID
    #            velocity (float): Speed of movement
    #            workpieces (int): Workpiece frame ID
    #        """
    #     count = 1
    #     # print("Robot Path:", robotPath)
    #     for point in robotPath:
    #         if count == 1:
    #             count = 0
    #             continue
    #
    #         ret = self.robot.moveL(point, tool, workpieces, vel=velocity, acc=acceleration, blendR=blendR)

    def _getNestingMoves(self, angle, centroid, dropOffPositionX, dropOffPositionY, height, gripperId):
        """
           Generates a pick-and-place trajectory for nesting.

           Args:
               angle (float): Rotation angle in degrees
               centroid (tuple): Centroid coordinates of the object
               dropOffPositionX (float): X position of drop target
               dropOffPositionY (float): Y position of drop target
               height (float): Height for Z-axis during move

           Returns:
               list: List of Cartesian positions for the move
           """
        # print("performPickAndPlaceMovement height: ", height)

        if gripperId == 4:  # DOUBLE GRIPPER
            angle = angle - 90
            self.RZ_VALUE = self.RZ_VALUE + 90
            # print("Angle Adjusted")
        else:
            self.RZ_VALUE = 0

        # xOffset = 50
        # yOffset = 50
        xOffset = 45
        yOffset = 45
        STATIC_Z_OFFSET = 30
        theta = math.radians(angle)
        # Apply 2D rotation matrix
        newXOffset = xOffset * math.cos(theta) - yOffset * math.sin(theta)
        newYOffset = xOffset * math.sin(theta) + yOffset * math.cos(theta)
        # print("NewX: ", newXOffset, "NewY: ", newYOffset)
        x = centroid[0] + newXOffset
        y = centroid[1] + newYOffset

        # Step 1: Pick up the workpieces
        path = []

        path.append([x, y, self.MIN_Z_VALUE + STATIC_Z_OFFSET,
                     self.RX_VALUE, self.RY_VALUE, self.RZ_VALUE])

        # Step 2: Move down to the workpieces with the correct orientation angle
        path.append([x, y, height,
                     self.RX_VALUE, self.RY_VALUE, angle])

        # Step 3 pick up the workpieces
        path.append([x, y, self.MIN_Z_VALUE + STATIC_Z_OFFSET,
                     self.RX_VALUE, self.RY_VALUE, self.RZ_VALUE])

        # waypoint -> -317.997 261.207
        waypoint = [-317.997, 261.207, self.MIN_Z_VALUE + STATIC_Z_OFFSET, self.RX_VALUE, self.RY_VALUE, self.RZ_VALUE]
        path.append(waypoint)

        # Step 4: Move to drop-off location
        path.append([dropOffPositionX + xOffset, dropOffPositionY + yOffset, height + STATIC_Z_OFFSET,
                     self.RX_VALUE, self.RY_VALUE, self.RZ_VALUE])

        return path

    def enableRobot(self):
        """
               Enables robot motion.
               """
        self.robot.enable()
        print("Robot enabled")

    def disableRobot(self):
        """
                Disables robot motion.
                """
        self.robot.disable()
        print("Robot disabled")

    def moveToPosition(self, position, tool, workpiece, velocity, acceleration, waitToReachPosition=False):
        """
        Moves the robot to a specified position with optional waiting.

        Args:
            position (list): Target Cartesian position
            tool (int): Tool frame ID
            workpiece (int): Workpiece frame ID
            velocity (float): Speed
            acceleration (float): Acceleration
            waitToReachPosition (bool): If True, waits for robot to reach position
        """
        ret = self.robot.moveCart(position, tool, workpiece, vel=velocity, acc=acceleration)

        if waitToReachPosition:  # TODO comment out when using test robot
            self._waitForRobotToReachPosition(position, 2, delay=0.1)

        # self.robot.moveL(position, tool, workpieces, vel=velocity, acc=acceleration,blendR=20)
        return ret

    def moveToHeightMeasurePosition(self, centroid, motionParams):
        """THIS FUNCTION WAS USET WITH THE LASER"""

        """
               Moves robot to a position used for height measurement.

               Args:
                   centroid (tuple): Target X, Y coordinates
                   motionParams (tuple): Motion parameters (velocity, tool, workpieces, acceleration)
               """
        position = [centroid[0], centroid[1] - 75, 300, self.RX_VALUE, self.RY_VALUE, self.RZ_VALUE]
        # print("Moving to height measurement position", position)
        self.moveToPosition(position, motionParams[1], motionParams[2], motionParams[0], motionParams[3])

    def _isValid(self, contour):
        """
              Validates if a contour is not None and has points.

              Args:
                  contour (array): Contour to validate

              Returns:
                  bool: True if valid
              """
        return contour is not None and len(contour) > 0

    def __executeNestingTrajectory(self, grippers, paths):
        """
               Executes pick-and-place paths for workpieces nesting using specified grippers.

               Args:
                   grippers (list): Gripper IDs
                   paths (list): Paths for each gripper

               Returns:
                   tuple: (bool, message) - True if successful
               """
        velocity, tool, workpiece, acceleration, blendR = self.getMotionParams()
        count = 0
        for gripperId, path in zip(grippers, paths):
            # print("PathCount: ", count)

            # print("len paths: ", len(paths))
            """CHECK IF GRIPPER CHANGE IS NECESSARY"""
            # print("Path: ", path)
            # print("Gripper: ", gripperId)
            # print("Current gripper: ", self.currentGripper)
            # print(f"Type of gripperId: {type(gripperId)}, Type of self.currentGripper: {type(self.currentGripper)}")

            if self.currentGripper != gripperId:
                if self.currentGripper is not None:
                    result, message = self.dropOffGripper(self.currentGripper)
                    if not result:
                        return False, message

                # result, message = self.pickupGripper(gripperId)
                # if not result:
                #     return False, message

            """MOVE ROBOT ALONG PATH TO PICK AND PLACE WORKPIECE"""
            self.pump.turnOn(self.robot)
            for point in path:
                # print("Exec path: ", count)
                self.robot.moveCart(point, ROBOT_TOOL, ROBOT_USER, vel=velocity, acc=acceleration)
            self.pump.turnOff(self.robot)
            self.moveToCalibrationPosition()
            count += 1
        return True, None

    def performWorkpieceNesting(self, workpieces, callback=None, plane=None):
        """
              Performs nesting of multiple workpieces by rotating, aligning, and placing them.

              Args:
                  plane: Plane object defining the nesting area
                  workpieces (list): List of workpieces objects with contour and height
                  callback (function, optional): Optional callback executed before nesting

              Returns:
                  tuple: (bool, message) - True if successful
              """
        # if callback is not None:
        #     validationPos = [-350, 650, 450, 180, 0, 90]
        #     self.moveToPosition(validationPos, 0, 0, 100, 30, waitToReachPosition=True)
        #     callback()
        grippers = []  # List of grippers
        paths = []  # List of pick and place paths
        count = 0  # Workpiece counter

        rowCount = plane.rowCount  # Row counter

        for slot in self.toolChanger.slots:
            # print("Slot: ", slot)
            pass

        # canvas = np.ones((720, 1280, 3), dtype=np.uint8) * 255  # Creates a 500x500 white canvas
        for item in workpieces:
            """ADD WORKPIECE GRIPPER TO GRIPPERS LIST"""
            # Extract and store the gripper ID needed for the current workpieces.
            grippers.append(int(item.gripperID.value))

            """GET NESTING POSITION FOR WORKPIECE"""
            # print("COUNT: ", count)
            cnt = item.contour
            cntObject = Contour(cnt)
            """ROTATE CONTOUR TO ALIGN WITH THE X-AXIS"""
            angle = cntObject.getOrientation()
            angle = angle
            # print("Nesting Angle: ", angle)
            centroid = cntObject.getCentroid()
            cntObject.rotate(-angle, centroid)

            """GET MINIMUM AREA RECTANGLE OF THE CONTOUR"""
            minRect = cntObject.getMinAreaRect()
            box = cv2.boxPoints(minRect)
            box = np.intp(box)

            """GET BOUNDING BOX CENTER AND DIMENSIONS"""
            bboxCenter = (minRect[0][0], minRect[0][1])

            # width = minRect[1][1]
            # height = minRect[1][0]

            width = minRect[1][0]
            height = minRect[1][1]
            if width < height:
                temp = width
                width = height
                height = temp
            # print(" bboxWidth: ", width)
            # print(" bboxHeight: ", height)

            """UPDATE HIGHEST CONTOUR HEIGHT ( IT IS USED FOR ROW SPACING)"""
            if height > plane.tallestContour:
                plane.tallestContour = height

            """GET TARGET POINT FOR PLACING THE WORKPIECE"""
            # Step 8: Compute the target placement point on the plane.
            targetPointX = plane.xOffset + plane.xMin + (width / 2)
            targetPointY = plane.yMax - plane.yOffset
            # print(f"    Target point: ({targetPointX}, {targetPointY}")

            """MOVE TO NEXT ROW IF THE CONTOUR EXCEEDS THE CANVAS WIDTH"""
            if targetPointX + (width / 2) > plane.xMax:
                # print(" The contour exceeds the canvas width. Moving to the next row.")

                rowCount += 1  # Increment row counter
                plane.xOffset = 0  # Reset xOffset for the new row
                plane.yOffset += plane.tallestContour + 50  # Use only the tallest contour + fixed spacing

                targetPointX = plane.xMin + (width / 2)  # Reset to the left
                targetPointY = plane.yMax - plane.yOffset  # Move down
                # print(" Target point after moving to the next row:", targetPointX, targetPointY)

                # Reset the row's tallest contour tracking
                plane.tallestContour = height

                """CHECK IF THE CONTOUR EXCEEDS THE CANVAS HEIGHT"""
                if targetPointY - (height / 2) < plane.yMin:
                    plane.isFull = True
                    # print(" The contour exceeds the canvas height.")
                    break

            # print(f"    bboxCenter: {bboxCenter}")
            count += 1

            """TRANSLATE THE CONTOUR TO THE TARGET POINT"""
            cntObject.translate(targetPointX - bboxCenter[0], targetPointY - bboxCenter[1])
            translated = cntObject.get_contour_points()

            """GET THE TRANSLATED CONTOUR CENTER"""
            newCentroid = cntObject.getCentroid()
            # print(f"    New centroid: {newCentroid}")

            """"UPDATE THE xOffset FOR THE NEXT CONTOUR"""
            plane.xOffset += width + plane.spacing  # Add horizontal spacing between contours

            """ADD PICK AND PLACE PATH TO PATHS LIST"""
            moveHeight = self.pump.zOffset + item.height

            gripperId = int(item.gripperID.value)
            path = self._getNestingMoves(angle, centroid, newCentroid[0], newCentroid[1], moveHeight, gripperId)
            paths.append(path)
            # print(f"    Path: ", path)

        """EXECUTE NESTING TRAJECTORY"""
        # self.pickupGripper(0)
        self.__executeNestingTrajectory(grippers, paths)

        return True, None

    def pickupGripper(self, gripperId, callBack=None):
        """
              Picks up a gripper from the tool changer.

              Args:
                  gripperId (int): ID of the gripper to pick
                  callBack (function, optional): Optional callback after pickup

              Returns:
                  tuple: (bool, message)
              """
        print("Gripper Id -> ", gripperId)
        slotId = self.toolChanger.getSlotIdByGrippedId(gripperId)
        print("Slot Id -> ", slotId)
        # print("Slot Id -> ", slotId)
        if not self.toolChanger.isSlotOccupied(slotId):
            message = f"Slot {slotId} is empty"
            print(message)
            return False, message

        slotPosition = self.toolChanger.getSlotPosition(slotId)
        # print("Slot Position: ", slotPosition)
        self.toolChanger.setSlotAvailable(slotId)

        # ret = self.robot.moveCart([-206.239, -180.406, 726.327, 180, 0, 101], 0, 0, 30, 30)
        # print("move before pickup: ",ret)
        if gripperId == Gripper.BELT.value:
            positions = self.toolChanger.getGripperPickupPositions_0()
        elif gripperId == Gripper.SINGLE.value:
            print("Picking up gripper 1")
            positions = self.toolChanger.getGripperPickupPositions_1()
        elif gripperId == Gripper.DOUBLE.value:
            positions = self.toolChanger.getGripperPickupPositions_2()
        else:
            raise ValueError("UNSUPPORTED GRIPPER ID: ", gripperId)
            self.moveToStartPosition()

        for pos in positions:
            print("Moving to position: ", pos)
            self.robot.moveL(pos, ROBOT_TOOL, ROBOT_USER, TOOL_CHANGING_VELOCITY, TOOL_CHANGING_ACCELERATION,
                             TOOL_CHANGING_BELNDING_RADIUS)

        self.moveToStartPosition()
        self.currentGripper = gripperId
        return True, None

    def dropOffGripper(self, gripperId, callBack=None):
        """
              Drops off the currently held gripper into a specified slot.

              Args:
                  slotId (int): Target slot ID
                  callBack (function, optional): Optional callback after drop off

              Returns:
                  tuple: (bool, message)
              """
        gripperId = int(gripperId)
        slotId = self.toolChanger.getSlotIdByGrippedId(gripperId)
        # print("Drop off gripper: ", gripperId)
        if self.toolChanger.isSlotOccupied(slotId):
            message = f"Slot {slotId} is taken"
            # print(message)
            return False, message

        slotPosition = self.toolChanger.getSlotPosition(slotId)
        self.toolChanger.setSlotNotAvailable(slotId)

        if gripperId == 0:
            positions = self.toolChanger.getGripperDropoffPositions_0()
        elif gripperId == 1:
            positions = self.toolChanger.getGripperDropoffPositions_1()
        elif gripperId == 2:
            """ADD LOGIC FOR DROPPING OFF TOOL 2 -> LASER"""
            positions = self.toolChanger.getGripperDropoffPositions_2()
        elif gripperId == 4:
            """ADD LOGIC FOR DROPPING OFF TOOL 4 -> DOUBLE GRIPPER"""
            positions = self.toolChanger.getGripperDropoffPositions_4()
        else:
            raise ValueError("UNSUPPORTED GRIPPER ID: ", gripperId)

        for pos in positions:
            self.robot.moveL(pos, ROBOT_TOOL, ROBOT_TOOL, TOOL_CHANGING_VELOCITY, TOOL_CHANGING_ACCELERATION,
                             TOOL_CHANGING_BELNDING_RADIUS)

        # self.moveToStartPosition()

        self.currentGripper = None
        return True, None

    def startJog(self, axis, direction, step):
        return self.robot.startJog(axis, direction, step, vel=JOG_VELOCITY, acc=JOG_ACCELERATION)

    def stopRobot(self):
        # FIXME THIS IMPLEMENTATION IS TEMPORARY !!!
        from GlueDispensingApplication.robot.RobotWrapper import RobotWrapper
        robot = RobotWrapper(ROBOT_IP)
        return robot.stopMotion()
        # return self.robot.stopMotion()

    def cleanNozzle(self):
        """
           Executes a nozzle cleaning routine.

           The robot performs a series of back-and-forth linear motions between two predefined
           Cartesian positions.

           Process Overview:
               1. Moves to an initial cleaning position (`pos1`) using Cartesian motion.
               2. Performs two full cleaning strokes (forward to `pos2` and back to `pos1`).
               3. Returns to the default start position after cleaning is complete.

           Motion Parameters:
               - Position Format: [X, Y, Z, Rx, Ry, Rz]
                   - X, Y, Z: Cartesian coordinates in millimeters
                   - Rx, Ry, Rz: Orientation in degrees

           Note:
               The function assumes the robot is already initialized and that the positions
               are safe and reachable. It also assumes the presence of a method `moveToStartPosition()`
               to bring the robot back to its idle or home configuration.
           """
        pos1 = CLEAN_NOZZLE_1
        pos2 = CLEAN_NOZZLE_2
        pos3 = CLEAN_NOZZLE_3

        iterations = 3

        self.robot.moveCart(pos1, 0, 0, 30, 30)
        self.robot.moveL(pos2, 0, 0, 30, 30, 1)

        while iterations > 0:
            self.robot.moveL(pos3, 0, 0, 30, 30, 1)
            self.robot.moveL(pos2, 0, 0, 30, 30, 1)
            iterations -= 1

        self.robot.moveL(pos1, 0, 0, 30, 30, 1)

        self.moveToStartPosition()

    def addCommandToQueue(self, command):
        """
        Adds a command to the queue for processing.

        Args:
            command (list): A list of integers representing the command to be added to the queue.
        """
        self.commandQue.put(command)
        # print("Command added to queue:", command)

    def _startCommandProcessor(self):
        def run():
            print("[CommandProcessor] Started.")
            while not self._stop_thread.is_set():
                try:
                    command = self.commandQue.get(timeout=0.1)
                    # print("[CommandProcessor] Executing:", command)
                    command()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"[CommandProcessor] Error: {e}")

        threading.Thread(target=run, daemon=True).start()

    def stop(self):
        """Gracefully stop the background thread."""
        self._stop_thread.set()
        print("[CommandProcessor] Stopping thread.")


# if __name__ == "__main__":
#     import time
#     from GlueDispensingApplication.settings.SettingsService import SettingsService
#     from GlueDispensingApplication.tools.GlueNozzleService import GlueNozzleService
#     from GlueDispensingApplication.robot.RobotWrapper import RobotWrapper
#     from GlueDispensingApplication.robot import RobotConfig
#
#     robot = RobotWrapper(ROBOT_IP)
#     settingsService = SettingsService()
#     glueNozzleService = GlueNozzleService()
#     glueNozzleService._startCommandProcessor()
#     robotService = RobotService(robot,settingsService,glueNozzleService)
#
#     robotService._startCommandProcessor()
#     robotService.addCommandToQueue(robotService.moveToStartPosition())
#     robotService.addCommandToQueue(lambda: robotService.robot.moveL([-232.343, -193.902, 721.685, 180, 0, 90],ROBOT_TOOL,ROBOT_USER,50,30,1))
#
#     robotService.glueNozzleService.addCommandToQueue(robotService.glueNozzleService.startGlueDotsDispensing())
#     time.sleep(1)
#     robotService.glueNozzleService.addCommandToQueue(robotService.glueNozzleService.stopGlueDispensing())
#     robotService.addCommandToQueue(robotService.moveToLoginPosition())
#     # robotService.addCommandToQueue(robotService.moveToCalibrationPosition())


