import sys

from PyQt6.QtWidgets import QApplication

from GlueDispensingApplication.GlueSprayingApplication import GlueSprayingApplication
from GlueDispensingApplication.DomesticRequestSender import DomesticRequestSender
# from GlueDispensingApplication.RequestHandler import RequestHandler
# IMPORT SERVICES
from GlueDispensingApplication.settings.SettingsService import SettingsService
from GlueDispensingApplication.vision.VisionService import VisionServiceSingleton
from GlueDispensingApplication.tools.GlueNozzleService import GlueNozzleService
from API.shared.workpiece.WorkpieceService import WorkpieceService
from GlueDispensingApplication.robot.RobotService import RobotService
from GlueDispensingApplication.robot.RobotCalibrationService import RobotCalibrationService
# IMPORT CONTROLLERS
from GlueDispensingApplication.settings.SettingsController import SettingsController
from GlueDispensingApplication.vision.CameraSystemController import CameraSystemController
from GlueDispensingApplication.tools.GlueNozzleController import GlueNozzleController
from GlueDispensingApplication.workpiece.WorkpieceController import WorkpieceController
from GlueDispensingApplication.robot.RobotController import RobotController
from GlueDispensingApplication.robot.RobotConfig import  *
from API.MessageBroker import MessageBroker
from GlueDispensingApplication.SensorPublisher import SensorPublisher
from GlueDispensingApplication.tools.ProximitySensor import ProximitySensor
from GlueDispensingApplication.tools.GlueCell import GlueCellsManagerSingleton,GlueDataFetcher
# from GlueDispensingApplication.tools.Trolly import Trolly
import logging

import os

if os.environ.get("WAYLAND_DISPLAY"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"


logging.basicConfig(
    level=logging.CRITICAL,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
)
# GUI RELATED IMPORTS
proximitySensor = ProximitySensor(13)
sensorPublisher = SensorPublisher()

# sensorPublisher.registerSensor(proximitySensor)
# register glue meters
glueFetcher = GlueDataFetcher()
glueFetcher.start()


# register trolleys
# trolleyLeft = Trolly(22)
# trolleyRight = Trolly(20)
# sensorPublisher.registerSensor(trolleyLeft)
# sensorPublisher.registerSensor(trolleyRight)

newGui = False
testRobot = False
if newGui:
    from pl_gui.PlGui import PlGui
else:
    from pl_gui.newMenu.newNavigationMenu import ApplicationDemo, MockController

if testRobot:
    from GlueDispensingApplication.robot.RobotWrapper import TestRobotWrapper
    robot = TestRobotWrapper()
else:
    from GlueDispensingApplication.robot.RobotWrapper import RobotWrapper
    robot = RobotWrapper(ROBOT_IP)

if __name__ == "__main__":
    messageBroker = MessageBroker()
    # INIT SERVICES
    settingsService = SettingsService()
    cameraService = VisionServiceSingleton().get_instance()

    try:
        glueNozzleService = GlueNozzleService.get_instance()
        # sensorPublisher.registerSensor(glueNozzleService)
        # glueNozzleService._startCommandProcessor()
    except Exception as e:
        glueNozzleService = None


    workpieceService = WorkpieceService()

    robotService = RobotService(robot,settingsService, glueNozzleService)

    robotCalibrationService = RobotCalibrationService()

    # INIT CONTROLLERS
    settingsController = SettingsController(settingsService)
    cameraSystemController = CameraSystemController(cameraService)
    # glueNozzleController = GlueNozzleController(glueNozzleService)
    workpieceController = WorkpieceController(workpieceService)
    robotController = RobotController(robotService,robotCalibrationService)

    # INIT APPLICATION

    glueSprayingApplication = GlueSprayingApplication(None, cameraService, settingsService,
                                                      glueNozzleService, workpieceService,
                                                      robotService,robotCalibrationService)  # Initialize ActionManager with a placeholder callback

    # INIT REQUEST HANDLER
    # requestHandler = RequestHandler(glueSprayingApplication, settingsController, cameraSystemController,
    #                                 glueNozzleController, workpieceController,robotController)
    from GlueDispensingApplication.NewRequestHandler import RequestHandler
    requestHandler = RequestHandler(glueSprayingApplication, settingsController, cameraSystemController,
                                     workpieceController,robotController)
    logging.info("Request Handler initialized")
    """GUI RELATED INITIALIZATIONS"""

    # INIT DOMESTIC REQUEST SENDER
    domesticRequestSender = DomesticRequestSender(requestHandler)
    logging.info("Domestic Request Sender initialized")
    # INIT MAIN WINDOW

    if newGui:
        from pl_gui.controller.Controller import Controller

        controller= Controller(domesticRequestSender)

        gui=PlGui(controller=controller)

        gui.start()

        # gui = GUI_NEW(domesticRequestSender)
        # gui.start()
    else:
        from pl_gui.newMenu.controller.Controller import Controller
        from pl_gui.newMenu.NewGui import PlGui

        controller= Controller(domesticRequestSender)
        gui = PlGui(controller=controller)
        gui.start()

    # root = tk.Tk()
        # mainWindow = MainWindow(root, domesticRequestSender)
        # # Set the callback function for the glue spraying application
        # glueSprayingApplication.callbackFunction = mainWindow.manageCallback
        # # START GUI
        # gui = GUI(domesticRequestSender, mainWindow)
        # gui.start()


