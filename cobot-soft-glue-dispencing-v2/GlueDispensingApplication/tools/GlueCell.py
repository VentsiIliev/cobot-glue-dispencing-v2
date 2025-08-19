# from GlueDispensingApplication.tools.enums.GlueType import GlueType
import statistics
from enum import Enum
from collections import deque
import requests
import json
import threading
from GlueDispensingApplication.SensorPublisher import Sensor
from API.MessageBroker import MessageBroker
from pathlib import Path
import time
"""
   Enum representing the types of glue used in the application.

   Attributes:
       TypeA (str): Represents Glue Type A.
       TypeB (str): Represents Glue Type B.
       TypeC (str): Represents Glue Type C.
   """

STORAGE_PATH = Path(__file__).parent.parent / "storage"
print(f"Storage path: {STORAGE_PATH}")

# Full path to config inside storage
config_path = STORAGE_PATH / "glueCells" / "glue_cell_config.json"



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

    def __init__(self, cells, config_data, config_path):
        """
        Initializes a GlueCellsManager instance.

        Args:
            cells (list): A list of GlueCell instances.

        Raises:
            TypeError: If any item in the cells list is not an instance of GlueCell.
        """
        self.logTag = "GlueCellsManager"
        self.setCells(cells)
        self.config_path = config_path
        self.config_data = config_data  # keep a copy of the loaded JSON


    def updateGlueTypeById(self, id, glueType):
        """
        Updates the glue type of a specific glue cell by its unique identifier
        and persists the change to the config file.
        """
        # Normalize string to enum
        if glueType == GlueType.TypeA.value:
            glueType = GlueType.TypeA
        elif glueType == GlueType.TypeB.value:
            glueType = GlueType.TypeB
        elif glueType == GlueType.TypeC.value:
            glueType = GlueType.TypeC
        elif glueType == GlueType.TypeD.value:
            glueType = GlueType.TypeD
        elif isinstance(glueType, GlueType):
            pass
        else:
            raise ValueError(f"[DEBUG] {self.logTag} Invalid glue type: {glueType}")

        print(f"[DEBUG] {self.logTag} Updating glue type for cell {id} to {glueType}")
        # Update in-memory object
        cell = self.getCellById(id)
        if cell is None:
            return False

        print(f"[DEBUG] {self.logTag} Updating cell {id} glue type to {glueType}")
        cell.setGlueType(glueType)

        # Update JSON data
        for c in self.config_data["CELL_CONFIG"]:
            if c["id"] == id:
                c["type"] = glueType.name  # store enum name like "TypeA"
                break

        # Persist to file
        with self.config_path.open("w") as f:
            json.dump(self.config_data, f, indent=2)

        return True


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

class GlueCellsManagerSingleton:
    _manager_instance = None
    STORAGE_PATH = Path(__file__).parent.parent / "storage"
    CONFIG_PATH = STORAGE_PATH / "glueCells" / "glue_cell_config.json"

    @staticmethod
    def get_instance():
        if GlueCellsManagerSingleton._manager_instance is None:
            # Load config JSON inside the manager
            with GlueCellsManagerSingleton.CONFIG_PATH.open("r") as f:
                config_data = json.load(f)

            type_map = {
                "TypeA": GlueType.TypeA,
                "TypeB": GlueType.TypeB,
                "TypeC": GlueType.TypeC,
                "TypeD": GlueType.TypeD
            }

            cells = []
            for cell_cfg in config_data["CELL_CONFIG"]:
                glue_type = type_map.get(cell_cfg["type"])
                if glue_type is None:
                    raise ValueError(f"Unknown glue type in config: {cell_cfg['type']}")
                glue_meter = GlueMeter(cell_cfg["id"], cell_cfg["url"])
                glue_cell = GlueCell(
                    id=cell_cfg["id"],
                    glueType=glue_type,
                    glueMeter=glue_meter,
                    capacity=cell_cfg["capacity"]
                )
                cells.append(glue_cell)

            # ✅ Pass config_data and CONFIG_PATH into manager
            GlueCellsManagerSingleton._manager_instance = GlueCellsManager(
                cells, config_data, GlueCellsManagerSingleton.CONFIG_PATH
            )

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

