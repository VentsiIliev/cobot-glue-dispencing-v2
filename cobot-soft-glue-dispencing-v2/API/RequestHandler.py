from API.Request import Request
from API.Response import Response
from API import Constants
from pl_gui.Endpoints import *
from API.shared.workpiece.Workpiece import WorkpieceField
from GlueDispensingApplication.utils import utils
import traceback

from GlueDispensingApplication.utils.utils import applyTransformation


class RequestHandler:
    """
      Handles the incoming requests and routes them to appropriate handlers
      based on the type of request (GET, POST, EXECUTE).

      Attributes:
          controller: The main controller for handling operations.
          settingsController: Controller for managing settings.
          cameraSystemController: Controller for camera system operations.
          glueNozzleController: Controller for glue nozzle operations.
          workpieceController: Controller for managing workpieces.
          robotController: Controller for managing robot operations.
      """
    def __init__(self, controller, settingsController, cameraSystemController, glueNozzleController, workpieceController, robotController):
        """
              Initializes the RequestHandler with the necessary controllers.

              Args:
                  controller (object): The main controller for handling operations.
                  settingsController (object): The settings controller.
                  cameraSystemController (object): The camera system controller.
                  glueNozzleController (object): The glue nozzle controller.
                  workpieceController (object): The workpiece controller.
                  robotController (object): The robot controller.
              """
        self.controller = controller
        self.settingsController = settingsController
        self.cameraSystemController = cameraSystemController
        self.glueNozzleController = glueNozzleController
        self.workpieceController = workpieceController
        self.robotController = robotController

    def _parseRequest(self,action):
        parts = action.split("/")
        resource = parts[0]
        print(resource)  # Output: ['robot', 'jog', 'X', 'Minus']
        return parts

    def newHandleRequest(self,request):
        request = Request.from_dict(request)
        parts = self._parseRequest(request.action)

        resource  = parts[0]
        if resource == Constants.REQUEST_RESOURCE_ROBOT.lower():
            self.robotController.handle(request,parts)
        elif resource == Constants.REQUEST_RESOURCE_CAMERA.lower():
            pass
        else:
            pass

    def handleRequest(self, request: dict):
        """
              Main request dispatcher. Routes requests based on their type and action.

              Args:
                  request (dict): The incoming request data as a dictionary.

              Returns:
                  dict: The response data based on the type of request.

              Raises:
                  ValueError: If the request type is invalid.
              """

        request = Request.from_dict(request)

        if request.action != Constants.CAMERA_ACTION_GET_LATEST_FRAME:
            print(f"Handling request1: {request}")

        handlers = {
            Constants.REQUEST_TYPE_GET: self.handleGetRequests,
            Constants.REQUEST_TYPE_POST: self.handlePostRequest,
            Constants.REQUEST_TYPE_EXECUTE: self.handleExecuteRequest,
        }

        if request.req_type in handlers:
            return handlers[request.req_type](request)
        else:
            raise ValueError(f"Invalid request type: {request.req_type}")

    def handleGetRequests(self, request):
        """
        Handles all GET requests, routing them to the correct resource handler.

        Args:
            request (Request): The request object to be processed.

        Returns:
            dict: The response data.
        """
        if request.action == Constants.SETTINGS_GET:

            return self.settingsController.handleGetRequest(request)

        if request.resource == Constants.REQUEST_RESOURCE_CAMERA:
            return self.cameraSystemController.handleGetRequest(request)

    def handlePostRequest(self, request):
        """
               Handles all POST requests, routing them to the correct action handler.

               Args:
                   request (Request): The request object to be processed.

               Returns:
                   dict: The response data.
               """

        if request.action == Constants.SETTINGS_SET:
            return self.settingsController.handlePostRequest(request)

        if request.action == Constants.ACTION_SAVE_WORKPIECE:
            return self._handleSaveWorkpiece(request)

        if request.action == Constants.ACTION_SAVE_WORKPIECE_DXF:
            return self._handleSaveWorkpieceDXF(request)

    def _handleSaveWorkpieceDXF(self,request):
        """
               Handles the saving of a workpiece in DXF format.

               Args:
                   request (Request): The request object to be processed.

               Returns:
                   dict: The response indicating success or failure of the operation.
               """
        print("Saving DFX")
        result = self.workpieceController.handlePostRequest(request)


        if result:
            return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Workpiece saved successfully").to_dict()
        else:
            return Response(Constants.RESPONSE_STATUS_ERROR, message="Error saving workpiece").to_dict()

    def _handleSaveWorkpiece(self, request):
        """
        Prepares and transforms the spray pattern before saving a workpiece.
        """
        print("Processing workpiece save request", request)



        print("Data before transform: ",request.data)

        sprayPattern = request.data.get(WorkpieceField.SPRAY_PATTERN.value, [])
        contours = sprayPattern.get("Contour")
        fill = sprayPattern.get("Fill")

        externalContour = request.data.get(WorkpieceField.CONTOUR.value, [])
        externalContour = applyTransformation(self.cameraSystemController.cameraService.getCameraToRobotMatrix(),externalContour)
        request.data[WorkpieceField.CONTOUR.value] = externalContour[0]

        # transpormedCnt= []
        # for cnt in contours:
        #     transformed = utils.applyTransformation(self.cameraSystemController.cameraService.getCameraToRobotMatrix(), cnt)
        #
        #     transpormedCnt.append(transformed)

        contours = utils.applyTransformation(self.cameraSystemController.cameraService.getCameraToRobotMatrix(), contours)
        fill = utils.applyTransformation(self.cameraSystemController.cameraService.getCameraToRobotMatrix(), fill)

        # transpormedFill = []
        # for cnt in fill:
        #     transformed = utils.applyTransformation(self.cameraSystemController.cameraService.getCameraToRobotMatrix(),
        #                                             cnt)
        #     transpormedFill.append(transformed)

        sprayPattern['Contour'] = contours
        sprayPattern['Fill'] = fill

        # if sprayPattern:
        #     sprayPattern = np.array(sprayPattern, dtype=np.float32).reshape(-1, 2)
        #     sprayPattern = [[[point[0], point[1]]] for point in sprayPattern]
        #     sprayPattern = utils.applyTransformation(
        #         self.cameraSystemController.cameraService.getCameraToRobotMatrix(), sprayPattern
        #     )

        request.data[WorkpieceField.SPRAY_PATTERN.value] = sprayPattern
        print("Data after transform: ", request.data)
        result =  self.workpieceController.handlePostRequest(request)

        if result:
            return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Workpiece saved successfully").to_dict()
        else:
            return Response(Constants.RESPONSE_STATUS_ERROR, message="Error saving workpiece").to_dict()


    def handleExecuteRequest(self, request):
        """
               Handles all EXECUTE requests, routing them to the appropriate resource handler.

               Args:
                   request (Request): The request object to be processed.

               Returns:
                   dict: The response data.
               """



        if request.resource == Constants.REQUEST_RESOURCE_GLUE_NOZZLE:
            return self.glueNozzleController.handleExecuteRequest(request)

        if request.resource == Constants.REQUEST_RESOURCE_ROBOT:
            return self._handleRobotRequests(request)

        if request.resource == Constants.REQUEST_RESOURCE_CAMERA:

            if request.action == Constants.ACTION_CALIBRATE:
                print("Handling camera calib")
                return self._handleCameraCalibration()

            return self.cameraSystemController.handleExecuteRequest(request)

        return self._handleGeneralExecutionRequests(request)

    def _handleRobotRequests(self, request):
        """
               Handles robot-related execution requests, such as calibration and point saving.

               Args:
                   request (Request): The request object to be processed.

               Returns:
                   dict: The response data.
               """


        if request.action == Constants.ACTION_CALIBRATE:
            return self._handleRobotCalibration()

        if request.action == Constants.ACTION_CALIBRATE_PICKUP_AREA:
            from GlueDispensingApplication.vision.workAreaCalibration import calibratePickupArea
            calibratePickupArea(self.controller.visionService)
            self.controller.visionService.pickupCamToRobotMatrix = self.controller.visionService._loadPickupCamToRobotMatrix()
            return
        # if request.action == Constants.ROBOT_MOVE_TO_CALIB_POS:
        #     self.ro
        #     self.robotController.robotService.moveToCalibrationPosition()

        if request.action == Constants.ROBOT_SAVE_POINT:
            return self.robotController.handleExecuteRequest(request,self.cameraSystemController.cameraService)

        return self.robotController.handleExecuteRequest(request)

    def _handleRobotCalibration(self):
        """
        Handles robot calibration requests by invoking the calibration method on the controller.

        Returns:
            dict: The response indicating success or failure of the operation.
        """

        try:
            result,message, image = self.controller.calibrateRobot()
            if result:
                return Response(Constants.RESPONSE_STATUS_SUCCESS, message=message, data={"image": image}).to_dict()
            else:
                return Response(Constants.RESPONSE_STATUS_ERROR, message=message).to_dict()
        except Exception as e:
            print(f"Error calibrating robot: {e}")
            return Response(Constants.RESPONSE_STATUS_ERROR, message=f"Error calibrating robot: {e}").to_dict()

    def _handleGeneralExecutionRequests(self, request):
        """
        Handles general execution requests like start, calibrate, and create workpiece.

        Args:
            request (Request): The request object to be processed.

        Returns:
            dict: The response data.
        """
        action_handlers = {
            START: self._handleStart,
            # Constants.ACTION_CALIBRATE: self._handleCameraCalibration,
            "Login": self._handleLogin,  # Add handler for Login action
            Constants.ACTION_CREATE_WORKPIECE: self._handleCreateWorkpiece
        }

        handler = action_handlers.get(request.action)
        return handler() if handler else Response(Constants.RESPONSE_STATUS_ERROR, message="Invalid action").to_dict()

    def _handleStart(self):
        """
                Handles the Start action, initiating the controller's start method.

                Returns:
                    dict: The response indicating success or failure of the operation.
                """
        try:

            result, message = self.controller.start()
            print("Result: ", result)
            if not result:
                return Response(Constants.RESPONSE_STATUS_ERROR, message=message).to_dict()
            else:
                return Response(Constants.RESPONSE_STATUS_SUCCESS, message=message).to_dict()
        except Exception as e:
            traceback.print_exc()
            return Response(Constants.RESPONSE_STATUS_ERROR, message=f"Error starting: {e}").to_dict()

    # def _handleStart(self):
    #     """
    #     Handles the Start action, initiating the controller's start method in a new thread.
    #
    #     Returns:
    #         dict: The response indicating success or failure of the operation.
    #     """
    #     import threading
    #
    #     def start_in_thread():
    #         try:
    #             result, message = self.controller.start()
    #             print("Result: ", result)
    #             if not result:
    #                 return Response(Constants.RESPONSE_STATUS_ERROR, message=message).to_dict()
    #             else:
    #                 responseDict = {"status": Constants.RESPONSE_STATUS_SUCCESS, "message": message}
    #                 return Response.from_dict(responseDict).to_dict()
    #         except Exception as e:
    #             traceback.print_exc()
    #             return Response(Constants.RESPONSE_STATUS_ERROR, message=f"Error starting: {e}").to_dict()
    #
    #     thread = threading.Thread(target=start_in_thread)
    #     thread.start()

        # responseDict = {"status": Constants.RESPONSE_STATUS_SUCCESS, "message": ""}
        # return Response.from_dict(responseDict).to_dict()

    def _handleCameraCalibration(self):
        """
        Handles the Camera Calibration action, invoking the calibration method.

        Returns:
            dict: The response indicating success or failure of the operation.
        """
        try:
            result, message = self.controller.calibrateCamera()
            print(f"Result: {result} Message: {message}")
            status = Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
            print("Status: ",status)
            return Response(status, message=message).to_dict()
        except Exception as e:
            return Response(Constants.RESPONSE_STATUS_ERROR, message=e).to_dict()

    def _handleCreateWorkpiece(self):
        """
        Handles the Create Workpiece action, invoking the controller's method to create a workpiece.

        Returns:
            dict: The response containing workpiece data.
        """
        try:
            result,height, contourArea, contour, scaleFactor, image,message,originalContours = self.controller.createWorkpiece()
            if not result:
                return Response(Constants.RESPONSE_STATUS_ERROR, message=message).to_dict()

            # Temporary workaround: force height to 4
            print("before comparison Height:", height)
            if height is None:
                height = 4
            if height < 4 or height > 4:
                height = 4

            # Cache data in the workpiece controller
            self.workpieceController.cacheInfo = {
                WorkpieceField.HEIGHT.value: height,
                WorkpieceField.CONTOUR_AREA.value: contourArea,
                # WorkpieceField.CONTOUR.value: contour
            }
            self.workpieceController.scaleFactor = scaleFactor

            dataDict = {WorkpieceField.HEIGHT.value: height, "image": image,"contours":originalContours[0]}

            return Response(Constants.RESPONSE_STATUS_SUCCESS, message=message, data=dataDict).to_dict()
        except Exception as e:
            return Response(Constants.RESPONSE_STATUS_ERROR, message=f"Uncaught exception: {e}").to_dict()

    def _handleLogin(self):
        return self.cameraSystemController.detectQrCode()