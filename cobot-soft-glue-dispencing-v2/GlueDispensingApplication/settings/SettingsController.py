import traceback

from API import Constants
from API.Response import Response
from GlueDispensingApplication.settings.SettingsService import SettingsService
from GlueDispensingApplication.vision.VisionService import VisionServiceSingleton


class SettingsController():
    """
     Controller responsible for handling GET and POST requests related to system settings.

     It interfaces with the SettingsService to retrieve and update application configuration,
     and optionally updates camera settings through the VisionService when applicable.
     """
    def __init__(self,settingsService: SettingsService):
        """
                Initialize the SettingsController.

                Args:
                    settingsService (SettingsService): An instance of SettingsService used to access and update settings.
                """
        self.settingsService = settingsService

    def handle(self,request,parts,data = None):
        command = parts[2]
        if command == "get":
            return self.handleGetSettings(request,parts)
        elif command == "set":
            print("Data in Settings Controller, ",data)
            return self.handleSetSettings(request,parts,data)
        else:
            raise ValueError("Invalid command in SettingsController")

    def handleGetSettings(self,request,parts,data=None):

        resource = parts[1].capitalize()

        print("Resource ", resource)
        data = self.settingsService.getSettings(resource)
        print("Data in get settings, ",data )
        if data is not None:
            return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Success", data=data).to_dict()
        else:
            return Response(Constants.RESPONSE_STATUS_ERROR, message="Error getting settings").to_dict()

    def handleSetSettings(self,request,parts,data = None):
        try:
            resource = parts[1]
            self.settingsService.updateSettings(data)
            if resource == Constants.REQUEST_RESOURCE_CAMERA.lower():
                result, message = VisionServiceSingleton().get_instance().updateCameraSettings(data)
                if result:
                    return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Settings saved successfully").to_dict()
                else:
                    return Response(Constants.RESPONSE_STATUS_ERROR,
                                    message=f"Error saving settings: {message}").to_dict()

            return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Settings saved successfully").to_dict()


        except Exception as e:
            traceback.print_exc()  # This prints the full stack trace
            return Response(Constants.RESPONSE_STATUS_ERROR, message=f"Uncaught exception: {e}").to_dict()