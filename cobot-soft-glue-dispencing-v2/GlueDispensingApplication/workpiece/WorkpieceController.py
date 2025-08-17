from API.shared.workpiece.WorkpieceService import WorkpieceService
from API import Constants
from GlueDispensingApplication.workpiece.Workpiece import Workpiece


class WorkpieceController:
    """
        Controller class to handle requests related to Workpieces. It provides the functionality to save
        a workpieces to the WorkpieceService after validating and updating the request data.

        Attributes:
            workpieceService (WorkpieceService): An instance of WorkpieceService used to save the workpieces.
            cacheInfo (dict): A cache used to store temporary data for processing requests.
            scaleFactor (float): A factor used for scaling workpieces measurements, defaulted to 1.

        Methods:
            __init__(workpieceService: WorkpieceService): Initializes the WorkpieceController with a WorkpieceService instance.
            handlePostRequest(request): Handles POST requests to save a workpieces, updating the request data with any cached information.
        """
    def __init__(self, workpieceService: 'WorkpieceService'):
        """
                Initializes the WorkpieceController with a WorkpieceService instance.

                Args:
                    workpieceService (WorkpieceService): An instance of WorkpieceService used to save workpieces.

                Raises:
                    ValueError: If the workpieceService provided is not an instance of WorkpieceService.
                """
        if not isinstance(workpieceService, WorkpieceService):
            raise ValueError("workpieceService must be an instance of WorkpieceService")
        self.workpieceService = workpieceService
        self.cacheInfo = {}
        self.scaleFactor = 1

    def getAllWorkpieces(self):
        return self.workpieceService.loadAllWorkpieces()

    def handlePostRequest(self, data):
        """
              Handles POST requests related to workpieces, such as saving the workpieces to the database.

              It checks the action type in the request and updates the request data by merging any cached information.
              After processing the data, it uses the WorkpieceService to save the workpieces.

              Args:
                  request (Request): The request object containing the action and data for processing.

              Returns:
                  bool: The result of the workpieces saving operation, returned from the WorkpieceService.

              Raises:
                  ValueError: If the action in the request is invalid or unsupported.

              Debugging Output:
                  The method prints debugging information to the console, such as request data and updates.
              """

        print("data in workpieces controller",data)
        # add the cached info to the data
        print("before if")
        if self.cacheInfo:
            print("IN IF")
            data.update(self.cacheInfo)
            self.cacheInfo = {}
            self.scaleFactor = 1
        print("New DATA: ",data)

        workpiece = Workpiece.fromDict(data)
        print("WP: ",workpiece)
        return self.workpieceService.saveWorkpiece(workpiece)

