# from GlueDispensingApplication.tools.enums.GlueType import GlueType
import statistics
from enum import Enum
from collections import deque
import requests
import json
import threading
from GlueDispensingApplication.SensorPublisher import Sensor
from API.MessageBroker import MessageBroker
import time
"""
   Enum representing the types of glue used in the application.

   Attributes:
       TypeA (str): Represents Glue Type A.
       TypeB (str): Represents Glue Type B.
       TypeC (str): Represents Glue Type C.
   """

class GlueType(Enum):
    TypeA = "Type A"
    TypeB = "Type B"
    TypeC = "Type C"
    TypeD = "Type D"

    def __str__(self):
        """
        Return the string representation of the glue type.

        Returns:
            str: The human-readable glue type value (e.g., "Type A").
        """
        return self.value


class GlueDataFetcher:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(GlueDataFetcher, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent reinitialization on subsequent instantiations
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.weight1 = 0
        self.weight2 = 0
        self.weight3 = 0
        self.url = "http://192.168.222.143/weights"
        self.fetchTimeout = 10
        self._stop_thread = threading.Event()
        self.thread = None
        self._initialized = True
        self.broker = MessageBroker()

    def fetch(self):
        try:
            response = requests.get(self.url, timeout=self.fetchTimeout)
            response.raise_for_status()
            weights = json.loads(response.text.strip())
            # print("Weights: ",weights)
            self.weight1 = float(weights.get("weight1", 0))
            self.weight2 = float(weights.get("weight2", 0))
            self.weight3 = float(weights.get("weight3", 0))

            self.broker.publish("GlueMeter_1/VALUE", self.weight1)
            self.broker.publish("GlueMeter_2/VALUE", self.weight2)
            self.broker.publish("GlueMeter_3/VALUE", self.weight3)

            # print(f"weights: weight1={self.weight1}, weight2={self.weight2}, weight3={self.weight3}")
        except Exception as e:
            pass
            # print(f"Error fetching weights: {e}")

    def _fetch_loop(self):
        while not self._stop_thread.is_set():
            self.fetch()
            time.sleep(0.1)

    def start(self):
        if self.thread is None or not self.thread.is_alive():
            self._stop_thread.clear()
            self.thread = threading.Thread(target=self._fetch_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self._stop_thread.set()
        if self.thread is not None:
            self.thread.join()



class GlueCell:
    """
    Represents a glue cell in the dispensing application.

    Attributes:
        id (int): The unique identifier for the glue cell.
        glueType (GlueType): The type of glue used in the cell.
        glueMeter (GlueMeter): The glue meter associated with the cell for measuring glue weight.
        capacity (int): The maximum capacity of the glue cell.

    Methods:
        setId(id): Sets the unique identifier for the glue cell.
        setGlueType(glueType): Sets the type of glue used in the cell.
        setGlueMeter(glueMeter): Sets the glue meter for the cell.
        setCapacity(capacity): Sets the maximum capacity of the glue cell.
        getGlueInfo(): Retrieves the current glue weight and percentage of capacity used.
    """

    def __init__(self, id, glueType, glueMeter, capacity):
        """
        Initializes a GlueCell instance.

        Args:
            id (int): The unique identifier for the glue cell.
            glueType (GlueType): The type of glue used in the cell.
            glueMeter (GlueMeter): The glue meter associated with the cell.
            capacity (int): The maximum capacity of the glue cell.

        Raises:
            TypeError: If glueType is not an instance of GlueType or glueMeter is not an instance of GlueMeter.
            ValueError: If capacity is less than or equal to 0.
        """
        self.logTag = "GlueCell"
        self.setId(id)
        self.setGlueType(glueType)
        self.setGlueMeter(glueMeter)
        self.setCapacity(capacity)

    def setId(self, id):
        """
        Sets the unique identifier for the glue cell.

        Args:
            id (int): The unique identifier for the glue cell.
        """
        self.id = id

    def setGlueType(self, glueType):
        """
        Sets the type of glue used in the cell.

        Args:
            glueType (GlueType): The type of glue used in the cell.

        Raises:
            TypeError: If glueType is not an instance of GlueType.
        """
        if not isinstance(glueType, GlueType):
            raise TypeError(f"[DEBUG] [{self.logTag}] glueType must be an instance of GlueType class, got {type(glueType)}")
        self.glueType = glueType

    def setGlueMeter(self, glueMeter):
        """
        Sets the glue meter for the cell.

        Args:
            glueMeter (GlueMeter): The glue meter associated with the cell.

        Raises:
            TypeError: If glueMeter is not an instance of GlueMeter.
        """

        if not isinstance(glueMeter, GlueMeter):
            raise TypeError(f"[DEBUG] [{self.logTag}] glueMeter must be an instance of GlueMeter class, got {type(glueMeter)}")
        self.glueMeter = glueMeter

    def setCapacity(self, capacity):
        """
        Sets the maximum capacity of the glue cell.

        Args:
            capacity (int): The maximum capacity of the glue cell.

        Raises:
            ValueError: If capacity is less than or equal to 0.
        """
        if capacity <= 0:
            raise ValueError(f"DEbug] [{self.logTag}] capacity must be greater than 0, got {capacity}")
        self.capacity = capacity

    def getGlueInfo(self):
        """
        Retrieves the current glue weight and percentage of capacity used.

        Returns:
            list: A list containing the current glue weight and percentage of capacity used.
        """
        weight = self.glueMeter.fetchData()
        if weight < 0:
            weight = 0
        percent = int((weight / self.capacity) * 100)
        return [weight, percent]

    def __str__(self):
        """
        Returns a string representation of the GlueCell instance.

        Returns:
            str: A string representation of the GlueCell instance.
        """
        return f"GlueCell(id={self.id}, glueType={self.glueType}, glueMeter={self.glueMeter}, capacity={self.capacity})"



class GlueMeter(Sensor):
    """
    Represents a glue meter used to measure the weight of glue in a container.

    Attributes:
        url (str): The URL endpoint for fetching glue weight data.
        fetchTimeout (int): The timeout duration (in seconds) for HTTP requests.

    Methods:
        __init__(url, fetchTimeout=2):
            Initializes a GlueMeter instance with the specified URL and timeout.
        setFetchTimeut(timeout):
            Sets the timeout duration for HTTP requests.
        setUrl(url):
            Sets the URL endpoint for fetching glue weight data.
        fetchData():
            Fetches the current glue weight from the URL and calculates the net weight.
        __str__():
            Returns a string representation of the GlueMeter instance.
    """

    def __init__(self,id, url, fetchTimeout=10, useLowPass=False, alpha=0.3):
        self.id = id
        self.name = f"GlueMeter_{self.id}"
        self.state = "Initializing"
        self.setFetchTimeut(fetchTimeout)
        self.setUrl(url)
        self.smoothedValue = None
        self.pollTime = 0.5
        self.type = "http"
        self.useLowPass = useLowPass
        self.alpha = alpha  # Smoothing factor for low-pass filter
        self.lastValue = None  # Last smoothed value for low-pass
        self.fetcher = GlueDataFetcher()


    def setFetchTimeut(self, timeout):
        """
        Sets the timeout duration for HTTP requests.

        Args:
            timeout (int): The timeout duration (in seconds).

        Raises:
            ValueError: If timeout is less than or equal to 0.
        """
        if timeout <= 0:
            raise ValueError(f"[DEBUG] [{self.name}] fetchTimeout must be greater than 0, got {timeout}")
        self.fetchTimeout = timeout

    def setUrl(self, url):
        """
        Sets the URL endpoint for fetching glue weight data.

        Args:
            url (str): The URL endpoint.
        """
        self.url = url

    def fetchData(self):
        weight = 0
        try:
            if self.id == 1:
                weight = self.fetcher.weight1

            if self.id == 2:
                weight = self.fetcher.weight2

            if self.id == 3:
                weight = self.fetcher.weight3

            self.state = "READY"
            self.lastValue = weight
            return  weight
        # try:
        #     response = requests.get(self.url, timeout=self.fetchTimeout)
        #     response.raise_for_status()
        #
        #     weight = float(response.text.strip())
        #     # weight = (weight / 100) / 1.831 - 5231  # Calibrated glue weight
        #
        #     self.state = "READY"
        #
        #     if self.useLowPass:
        #         if self.lastValue is None:
        #             self.lastValue = weight
        #         else:
        #             self.lastValue = self.alpha * weight + (1 - self.alpha) * self.lastValue
        #         return self.lastValue
        #     else:
        #         self.lastValue = weight
        #         return weight

        except requests.exceptions.Timeout:
            self.state = "DISCONNECTED"
            print(f"[{self.name}] Connection timeout.")
            return None

        except requests.exceptions.RequestException as e:
            self.state = "ERROR"
            # print(f"[{self.name}] Request error: {e}")
            return None

    def __str__(self):
        """
        Returns a string representation of the GlueMeter instance.

        Returns:
            str: A string representation of the GlueMeter instance.
        """
        return f"GlueMeter(url={self.url})"

    ### SENSOR INTERFACE METHODS IMPLEMENTATION

    def getState(self):
        return self.state


    def getValue(self):
        return self.lastValue


    def getName(self):
        return self.name

    def testConnection(self):
        # Not needed, as fetchData determines state
        self.fetchData()

    def reconnect(self):
        # Not needed, as fetchData attempts fresh HTTP request each time
        pass


class GlueCellsManager:
    """
    Manages multiple glue cells in the dispensing application.

    Attributes:
        cells (list): A list of GlueCell instances.

    Methods:
        setCells(cells): Sets the list of glue cells.
        getCellById(id): Retrieves a glue cell by its unique identifier.
    """

    def __init__(self, cells):
        """
        Initializes a GlueCellsManager instance.

        Args:
            cells (list): A list of GlueCell instances.

        Raises:
            TypeError: If any item in the cells list is not an instance of GlueCell.
        """
        self.logTag = "GlueCellsManager"
        self.setCells(cells)

    def setCells(self, cells):
        """
        Sets the list of glue cells.

        Args:
            cells (list): A list of GlueCell instances.

        Raises:
            TypeError: If any item in the cells list is not an instance of GlueCell.
        """
        if not all(isinstance(cell, GlueCell) for cell in cells):
            raise TypeError(f"[DEBUG] {self.logTag} All items in the cells list must be instances of GlueCell")
        self.cells = cells

    def getCellById(self, id):
        """
        Retrieves a glue cell by its unique identifier.

        Args:
            id (int): The unique identifier of the glue cell.

        Returns:
            GlueCell: The glue cell with the specified identifier, or None if not found.
        """
        for cell in self.cells:
            if cell.id == id:
                return cell
        return None

    def pollGlueDataById(self,id):
        weight, percent = self.getCellById(id).getGlueInfo()
        return weight, percent

    def __str__(self):
        """
        Returns a string representation of the GlueCellsManager instance.

        Returns:
            str: A string representation of the GlueCellsManager instance.
        """
        return f"CellsManager(cells={self.cells})"



"""cells config in format [ID, GLUE TYPE, GLUE METER URL, CAPACITY]"""
GLUE_CELL_MANAGER = None
GLUE_CELL_CAPACITY = 5000
GLUE_CELL_1_CFG = [1,GlueType.TypeA,"http://192.168.222.143/weight1",GLUE_CELL_CAPACITY]
GLUE_CELL_2_CFG = [2,GlueType.TypeB,"http://192.168.222.143/weight2",GLUE_CELL_CAPACITY]
GLUE_CELL_3_CFG = [3,GlueType.TypeC,"http://192.168.222.143/weight3",GLUE_CELL_CAPACITY]
CELL_CONFIG = [GLUE_CELL_1_CFG, GLUE_CELL_2_CFG, GLUE_CELL_3_CFG]

class GlueCellsManagerSingleton:
    _manager_instance = None

    @staticmethod
    def get_instance():
        if GlueCellsManagerSingleton._manager_instance is None:

            cells = []
            for cfg in CELL_CONFIG:
                glueMeter = GlueMeter(cfg[0],cfg[2])
                glueCell = GlueCell(id=cfg[0], glueType=cfg[1], glueMeter=glueMeter, capacity=cfg[3])
                cells.append(glueCell)

            GlueCellsManagerSingleton._manager_instance = GlueCellsManager(cells)

        return GlueCellsManagerSingleton._manager_instance


"""     EXAMPLE USAGE   """
if __name__ == "__main__":
    # try:
    #     print("Meter 1: ",GlueCellsManagerSingleton.get_instance().pollGlueDataById(1))
    #     # print("Meter 2: ",GlueCellsManagerSingleton.get_instance().pollGlueDataById(2))
    #     # print("Meter 3: ",GlueCellsManagerSingleton.get_instance().pollGlueDataById(3))
    # except Exception as e:
    #     print(f"Error: {e}")

    fetcher= GlueDataFetcher()
    fetcher.start()
    import time
    while True:
        time.sleep(1)  # Add a delay to allow the fetcher thread to run
        print("running")

