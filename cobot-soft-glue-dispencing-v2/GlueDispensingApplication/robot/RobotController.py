from API import Constants
from API.Response import Response
from GlueDispensingApplication.robot.RobotWrapper import Direction, Axis


class RobotController():
    """
     RobotController handles high-level robot API actions based on external requests.

     It interprets actions like jogging, calibration, saving points, and homing, and delegates execution
     to the robot service and calibration service.

     Attributes:
         robotService (RobotService): Service responsible for controlling the physical robot.
         robotCalibrationService (RobotCalibrationService): Handles calibration between camera and robot space.
     """

    def __init__(self, robotService, robotCalibrationService):
        """
              Initialize the RobotController with services for robot control and calibration.

              Args:
                  robotService (RobotService): Robot control abstraction layer.
                  robotCalibrationService (RobotCalibrationService): Calibration manager.
              """
        self.robotService = robotService
        self.robotCalibrationService = robotCalibrationService

    def handle(self, request, parts):
        command = parts[1]
        if "jog" in command:
            axis = parts[2]
            direction = parts[3]
            step = parts[4]
            return self._newHandleJog(axis, direction, step)

        elif "move" in command:
            pos = parts[2]
            if pos == "home":
                return self._handleHome()
            elif pos == "login":
                return  self._handleLoginPos()
            elif pos == "calibPos":
                return self._handleMoveToCalibPose()
            else:
                print("Invalid position in RobotController.handle")

        elif "stop" in command:
            return self._handleStop()
        elif "savePoint" in command:
            return self._handleSavePoint()

    def _newHandleJog(self, axis, direction, step):
        ret = self.robotService.startJog(Axis.get_by_string(axis), Direction.get_by_string(direction), step)
        return self._moveSuccess(ret, "Failed JOG","Success JOG")

    def _moveSuccess(self, ret, messageFail,messageSuccess):

        if ret != 0:
            return Response(status=Constants.RESPONSE_STATUS_ERROR,
                            message=messageFail,
                            data={}).to_dict()
        return Response(status=Constants.RESPONSE_STATUS_SUCCESS,
                        message=messageSuccess,
                        data={}).to_dict()

    def _handleMoveToCalibPose(self):
        ret = self.robotService.moveToCalibrationPosition()
        response = self._moveSuccess(ret, "Failed moveing to calibration pose", "Success moveing to calibration pose")
        return response


    def _handleSavePoint(self):
        currentPos = self.robotService.getCurrentPosition()
        x, y, z = currentPos[0], currentPos[1], currentPos[2]
        self.robotCalibrationService.saveRobotPoint([x, y, z])
        pointsCount = self.robotCalibrationService.robotPointIndex

        if pointsCount == 9:
            result, message = self.robotCalibrationService.calibrate()
            if result:
                self.robotService.cameraToRobotMatrix = self.robotCalibrationService.cameraToRobotMatrix

            self.robotService.moveToCalibrationPosition()
            self.robotService.moveToStartPosition()
            self.robotService._waitForRobotToReachPosition(self.robotService.startPosition, 1, 0.1)
            # from GlueDispensingApplication.vision import workAreaCalibration
            # workAreaCalibration.calibratePickupArea(visionService)

            response = Response(status=Constants.RESPONSE_STATUS_SUCCESS,
                                message=message,
                                data={"pointsCount": pointsCount})
            return response.to_dict()

        else:
            self.robotService.moveToPosition([currentPos[0], currentPos[1], currentPos[2] + 50, 180, 0, 0], 0, 0, 100,
                                             30)
            x, y, z = self.robotCalibrationService.getNextRobotPoint()
            nextPosition = [x, y, 150, 180, 0, 0]
            self.robotService.moveToPosition(nextPosition, 0, 0, 100, 30)
            nextPosition = [x, y, z, 180, 0, 0]
            self.robotService.moveToPosition(nextPosition, 0, 0, 100, 30)

        response = Response(status=Constants.RESPONSE_STATUS_SUCCESS,
                            message="Point saved",
                            data={"pointsCount": pointsCount})

        return response.to_dict()

    def _handleLoginPos(self):
        ret = self.robotService.moveToLoginPosition()
        print("_handleLoginPos", ret)
        return self._moveSuccess(ret, "Failed moving to login pos", "Success moving to login pos")

    def _handleHome(self):
        ret = self.robotService.moveToStartPosition()
        return self._moveSuccess(ret, "Failed moving to home","Success moving to home")

    def _handleStop(self):
        ret = self.robotService.stopRobot()
        response = self._moveSuccess(ret, "Failed STOP", "Success STOP")
        return response
