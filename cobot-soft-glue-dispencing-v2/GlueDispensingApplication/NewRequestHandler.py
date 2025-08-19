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
    def __init__(self, controller, settingsController, cameraSystemController, workpieceController, robotController):
        """
              Initializes the RequestHandler with the necessary controllers.

              Args:
                  controller (object): The main controller for handling operations.
                  settingsController (object): The settings controller.
                  cameraSystemController (object): The camera system controller.
                  glueNozzleController (object): The glue nozzle controller.
                  workpieceController (object): The workpieces controller.
                  robotController (object): The robot controller.
              """
        self.controller = controller
        self.settingsController = settingsController
        self.cameraSystemController = cameraSystemController

        self.workpieceController = workpieceController
        self.robotController = robotController

        self.resource_dispatch = {
            Constants.REQUEST_RESOURCE_ROBOT.lower(): self._handleRobot,
            Constants.REQUEST_RESOURCE_CAMERA.lower(): self._handleCamera,
            Constants.REQUEST_RESOURCE_SETTINGS.lower(): self._handleSettings,
            Constants.REQUEST_RESOURCE_WORKPIECE.lower(): self._handleWorkpiece,
        }

    def handleRequest(self, request, data=None):

        if request == "handleExecuteFromGallery":
            return self.handleExecuteFromGallery(data)

        parts = self._parseRequest(request)
        resource = parts[0]

        # if len(parts) >=1 and parts[1] == "saveWorkAreaPoints":
        #     return self.handleSaveWorkAreaPoints(data)

        if resource in self.resource_dispatch:
            return self.resource_dispatch[resource](parts, request, data)

        if request == Constants.START:
            return self._handleStart()
        if request == "login":
            print("handling login")
            user = data[0]
            password = data[1]
            return self._handle_login(user,password)

        if request == Constants.TEST_RUN:
            print("Handling test run")
            return self.controller.testRun()

        raise ValueError(f"Invalid command: {request}")

    def handleSaveWorkAreaPoints(self, points):
        self.cameraSystemController.saveWorkAreaPoints(points)
    def handleExecuteFromGallery(self,workpiece):
        self.controller.handleExecuteFromGallery(workpiece)

    def _handle_login(self,id,password):

        print("In _handle_login ")
        print(f"ID: {id} pass: {password} (type of ID: {type(id)})")
        from API.shared.user.User import User, Role, UserField
        from API.shared.user.CSVUsersRepository import CSVUsersRepository
        from API.shared.user.UserService import UserService
        import os
        csv_file_path = os.path.join(os.path.dirname(__file__), "../API/shared/user/users.csv")
        user_fields = [UserField.ID, UserField.FIRST_NAME, UserField.LAST_NAME, UserField.PASSWORD, UserField.ROLE]
        print(f"userFields: {user_fields}")
        repository = CSVUsersRepository(csv_file_path, user_fields, User)
        service = UserService(repository)
        user = service.getUserById(id)
        print("User ",user)
        if user:
            if user.password == password:  # Replace with hashed comparison in real use
                print(f"Login successful! Welcome, {user.firstName} ({user.role.value})")
                response = Response(Constants.RESPONSE_STATUS_SUCCESS,"1")
                from API.shared.user.Session import SessionManager
                # Login successful
                SessionManager.login(user)
            else:
                print("Incorrect password.")
                response = Response(Constants.RESPONSE_STATUS_SUCCESS,"0")
        else:
            print("User not found.")
            response = Response(Constants.RESPONSE_STATUS_SUCCESS,"-1")

        return  response

    def _handleRobot(self, parts, request, _):
        command = parts[1] if len(parts) > 1 else None
        if command == "calibrate":
            return self._handleRobotCalibration()
        return self.robotController.handle(request, parts)

    def _handleCamera(self, parts, request, data):
        command = parts[1] if len(parts) > 1 else None
        if command == "calibrate":
            return self._handleCameraCalibration()

        response =  self.cameraSystemController.handle(request, parts,data)
        return response

    def _handleSettings(self, parts, request, data):
        return self.settingsController.handle(request, parts, data)

    def _handleWorkpiece(self, parts, request, data):
        command = parts[1] if len(parts) > 1 else None
        print(f"handling wp: {parts} {request}")
        if command == "save":
            return self._handleSaveWorkpiece(request,parts,data)
        elif command == "dxf":
            return self.saveWorkpieceFromDXF(data)
        elif command == "create":
            return self._handleCreateWorkpiece()
        elif command == "getall":

            return self._handleGetAllWorkpieces()
        else:
            raise ValueError(f"Invalid workpiece command: {command}")

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

    def saveWorkpieceFromDXF(self, data):
        result = self.workpieceController.handlePostRequest(data)
        if result:
            return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Workpiece saved successfully").to_dict()
        else:
            return Response(Constants.RESPONSE_STATUS_ERROR, message="Error saving workpieces").to_dict()



    def _handleSaveWorkpiece(self, request,parts,data):
        """
        Prepares and transforms the spray pattern before saving a workpieces.
        """
        sprayPattern = data.get(WorkpieceField.SPRAY_PATTERN.value, [])
        contours = sprayPattern.get("Contour")
        fill = sprayPattern.get("Fill")

        externalContours = data.get(WorkpieceField.CONTOUR.value, [])
        print("originalcnt saved: ", externalContours)
        # externalContour = applyTransformation(self.cameraSystemController.cameraService.getCameraToRobotMatrix(),externalContour)
        if externalContours is None or len(externalContours) == 0:
            externalContour = []
        else:
            externalContour = externalContours[0]
        data[WorkpieceField.CONTOUR.value] = externalContour

        sprayPattern['Contour'] = contours
        sprayPattern['Fill'] = fill

        contour = data.get(WorkpieceField.CONTOUR.value,[])

        data[WorkpieceField.SPRAY_PATTERN.value] = sprayPattern
        print("Data after transform: ", data)
        result =  self.workpieceController.handlePostRequest(data)

        if result:
            return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Workpiece saved successfully").to_dict()
        else:
            return Response(Constants.RESPONSE_STATUS_ERROR, message="Error saving workpieces").to_dict()

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

    def _handleGetAllWorkpieces(self):
        return self.workpieceController.getAllWorkpieces()

    def _handleCreateWorkpiece(self):
        """
        Handles the Create Workpiece action, invoking the controller's method to create a workpieces.

        Returns:
            dict: The response containing workpieces data.
        """
        try:
            result,data = self.controller.createWorkpiece()
            if not result:
                return Response(Constants.RESPONSE_STATUS_ERROR, message=data).to_dict()
            height, contourArea, contour, scaleFactor, image,message,originalContours = data

            # Temporary workaround: force height to 4

            if height is None:
                height = 4
            if height < 4 or height > 4:
                height = 4

            # Cache data in the workpieces controller
            self.workpieceController.cacheInfo = {
                WorkpieceField.HEIGHT.value: height,
                WorkpieceField.CONTOUR_AREA.value: contourArea,
                # WorkpieceField.CONTOUR.value: contour
            }
            self.workpieceController.scaleFactor = scaleFactor

            originalContour = []
            if originalContour is not None and len(originalContours) > 0:
                originalContour = originalContours[0]

            dataDict = {WorkpieceField.HEIGHT.value: height, "image": image,"contours":originalContour}

            return Response(Constants.RESPONSE_STATUS_SUCCESS, message=message, data=dataDict).to_dict()
        except Exception as e:
            import traceback
            print(f"Uncaught exception in _handleCreateWorkpiece: {e}")
            traceback.print_exc()
            # Handle any uncaught exceptions gracefully
            return Response(Constants.RESPONSE_STATUS_ERROR, message=f"Uncaught exception: {e}").to_dict()

    def _parseRequest(self, request):
        # print(request)  # Output: ['robot', 'jog', 'X', 'Minus']
        parts = request.split("/")
        resource = parts[0]
        return parts