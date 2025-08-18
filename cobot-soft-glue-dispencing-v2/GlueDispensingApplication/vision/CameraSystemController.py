from API import Constants
from API.Response import Response
import traceback

import time
class CameraSystemController():
    """
    A controller class to handle camera-related requests and interact with the CameraService.

    This class acts as a mediator between external requests and the CameraService, facilitating actions like
    retrieving the latest camera frame, enabling or disabling raw mode, and updating camera settings.

    Attributes:
        cameraService (CameraService): The service object that provides camera functionalities such as
                                       retrieving frames and modifying camera settings.

    Methods:
        handleGetRequest(request):
            Handles GET requests, specifically retrieving the latest frame from the camera system.

        handlePostRequest(request):
            Placeholder method for handling POST requests. Currently does nothing.

        handleExecuteRequest(request):
            Handles execute requests, enabling or disabling raw mode on the camera.

        updateCameraSettings(settings):
            Updates the camera settings using the provided dictionary of settings.
    """

    def __init__(self, cameraService: 'CameraService'):
        """
             Initializes the CameraSystemController with the given CameraService instance.

             The controller will interact with the CameraService to perform camera-related actions.

             Args:
                 cameraService (CameraService): The service that provides methods to interact with the camera hardware.
             """
        self.cameraService = cameraService

    def handle(self, request, parts):
        command = parts[1]
        if command == "getLatestFrame":
            return self.handleLatestFrame()
        elif command == "rawModeOn":
            return self.handleRawModeOn()
        elif command == "rawModeOff":
            return self.handleRawModeOff()
        elif command == "login":
            return self.handleLogin()
        elif command == "STOP_CONTOUR_DETECTION":
            return self.stopContourDetection()
        elif command == "START_CONTOUR_DETECTION":
            return self.startContourDetection()
        elif command == "captureCalibrationImage":
            return  self.captureCalibrationImage()
        elif command == "testCalibration":
            return self.cameraService.testCalibration()



    def captureCalibrationImage(self):
        result,message =  self.cameraService.captureCalibrationImage()
        if not result:
            return Response(Constants.RESPONSE_STATUS_ERROR, message=message).to_dict()
        return Response(Constants.RESPONSE_STATUS_SUCCESS, message=message).to_dict()
    def updateCameraSettings(self, settings: dict):
        """
          Updates the camera settings with the provided configuration.

          This method passes the provided settings dictionary to the CameraService, where it updates the camera's
          configuration based on the given key-value pairs.

          Args:
              settings (dict): A dictionary containing the camera settings to be updated.

          Returns:
              bool: Returns `True` if the settings were successfully updated, otherwise `False`.
          """
        return self.cameraService.updateSettings(settings)

    def handleLogin(self):
        import re
        data = self.cameraService.detectQrCode()

        pattern = r"id\s*=\s*(\S+)\s+password\s*=\s*(\S+)"
        match = re.search(pattern, data)
        if match:
            data= {
                "id": match.group(1),
                "password": match.group(2)
            }

        print("in handle login data: ",data)
        if data is None:
            return Response(Constants.RESPONSE_STATUS_ERROR,"No QR code detected",data = data)
        return Response(Constants.RESPONSE_STATUS_SUCCESS, "",data = data)

    def handleLatestFrame(self):
        # if not hasattr(self, "_latest_frame_call_count"):
        #     self._latest_frame_call_count = 0
        #     self._latest_frame_last_time = time.time()
        # self._latest_frame_call_count += 1

        # # Print call count and frequency every 10 calls
        # if self._latest_frame_call_count % 10 == 0:
        #     now = time.time()
        #     elapsed = now - self._latest_frame_last_time
        #     freq = 10 / elapsed if elapsed > 0 else float("inf")
        #     print(
        #         f"[handleLatestFrame] Called {self._latest_frame_call_count} times, last 10 calls: {freq:.2f} calls/sec")
        #     self._latest_frame_last_time = now

        try:
            frame = self.cameraService.getLatestFrame()

            if frame is None:
                data = {"frame": None}
                message = "FRAME IS NONE"
            else:
                data = {"frame": frame}
                message = "Frame taken"
            return Response(Constants.RESPONSE_STATUS_SUCCESS, message=message, data=data).to_dict()
        except Exception as e:
            return Response(Constants.RESPONSE_STATUS_ERROR,
                            message=f"Error getting latest frame: {e}").to_dict()

    def handleRawModeOn(self):
        self.cameraService.setRawMode(True)
        return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Raw mode enabled").to_dict()

    def handleRawModeOff(self):
        self.cameraService.setRawMode(False)
        return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Raw mode disabled").to_dict()

    def stopContourDetection(self):
        self.cameraService.stopContourDetection()

    def startContourDetection(self):
        self.cameraService.startContourDetection()