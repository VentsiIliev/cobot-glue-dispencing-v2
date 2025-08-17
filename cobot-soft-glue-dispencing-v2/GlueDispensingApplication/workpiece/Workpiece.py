import numpy as np
from API.shared.workpiece.Workpiece import BaseWorkpiece
from API.shared.interfaces.JsonSerializable import JsonSerializable
from API.shared.workpiece.Workpiece import WorkpieceField
from GlueDispensingApplication.tools.enums.Program import Program
from GlueDispensingApplication.tools.enums.ToolID import ToolID
from GlueDispensingApplication.tools.GlueCell import GlueType
from GlueDispensingApplication.tools.enums.Gripper import Gripper


class Workpiece(BaseWorkpiece, JsonSerializable):
    """
        A class representing a workpieces in a glue dispensing application, including its properties such as ID,
        name, description, tool, gripper, glue type, program, material, contour, offset, height, nozzles,
        contour area, and spray pattern.

        Inherits from BaseWorkpiece and JsonSerializable for basic workpieces functionality and serialization support.
        """
    def __init__(self, workpieceId, name, description, toolID, gripperID, glueType, program, material, contour, offset,
                 height,
                 nozzles, contourArea, glueQty,sprayWidth,sprayPattern=None):
        """
              Initializes a Workpiece object with specified parameters.

              Args:
                  workpieceId (int): The unique identifier for the workpieces.
                  name (str): The name of the workpieces.
                  description (str): A description of the workpieces.
                  toolID (ToolID): The tool ID associated with the workpieces.
                  gripperID (Gripper): The gripper ID associated with the workpieces.
                  glueType (GlueType): The type of glue used in the workpieces.
                  program (Program): The program associated with the workpieces.
                  material (str): The material of the workpieces.
                  contour (list of np.ndarray): The contour points of the workpieces.
                  offset (float): The offset of the workpieces.
                  height (float): The height of the workpieces.
                  nozzles (list): The list of nozzles associated with the workpieces.
                  contourArea (float): The area of the contour.
                  sprayPattern (optional, list): The spray pattern used for the workpieces. Defaults to an empty list if None.

              """
        if sprayPattern is None:
            sprayPattern = []
        self.workpieceId = workpieceId
        self.name = name
        self.description = description
        self.toolID = toolID
        self.gripperID = gripperID
        self.glueType = glueType
        self.program = program
        self.material = material
        self.contour = contour  # This should be a list of nd arrays
        self.offset = offset
        self.height = height
        self.sprayPattern = sprayPattern
        self.contourArea = contourArea
        self.nozzles = nozzles
        self.glueQty = glueQty
        self.sprayWidth = sprayWidth

    def __str__(self):
        """
              Provides a string representation of the Workpiece object.

              Returns:
                  str: A formatted string describing the Workpiece with key details.
              """
        return (f"Workpiece ID: {self.workpieceId} \n"
                f"   Name: {self.name}\n"
                f"   Description: {self.description}\n"
                f"   Spray Type: {self.toolID}\n"
                f"   Glue Type: {self.glueType}\n"
                f"   Program: {self.program}\n"
                f"   Tool ID: {self.toolID}\n"
                f"   Gripper ID: {self.gripperID}\n"
                f"   Material: {self.material}\n"
                f"   Offset: {self.offset}\n"
                f"   Height: {self.height}\n"
                f"   Nozzles: {self.nozzles}\n"
                f"   Area: {self.contourArea}\n"
                f"   Glue QTY: {self.glueQty}\n"
                f"   Spray Width: {self.sprayWidth}\n"
                f"   Contour Points: {self.contour}\n" 
                f"   Spray Pattern: {self.sprayPattern}\n")
                # f"   Spray Pattern: {{ Contour: {len(self.sprayPattern.get('Contour', []))}, Fill: {len(self.sprayPattern.get('Fill', []))} }}\n")

    def get_spray_pattern_contours(self):
        """
        Return list of spray pattern contour entries.
        Each entry is a dict: {"contour": np.ndarray, "settings": dict}
        """
        contours = []
        for entry in self.sprayPattern.get("Contour", []):
            contour_points = np.array(entry.get("contour", []), dtype=np.float32).reshape(-1, 2)
            contours.append({
                "contour": contour_points,
                "settings": entry.get("settings", {})
            })
        return contours


    def get_spray_pattern_fills(self):
        """
        Return list of spray pattern fill entries.
        Each entry is a dict: {"contour": np.ndarray, "settings": dict}
        """
        fills = []
        for entry in self.sprayPattern.get("Fill", []):
            contour_points = np.array(entry.get("contour", []), dtype=np.float32).reshape(-1, 2)
            fills.append({
                "contour": contour_points,
                "settings": entry.get("settings", {})
            })
        return fills





    @staticmethod
    def serialize(workpiece):
        def convert_ndarray_to_list(obj):
            if isinstance(obj, np.ndarray):
                if obj.ndim == 2 and obj.shape[1] == 2:
                    obj = obj.reshape(-1, 1, 2)  # ✅ normalize before list conversion
                return obj.tolist()
            elif isinstance(obj, dict) and "contour" in obj:
                contour = obj["contour"]
                if isinstance(contour, np.ndarray) and contour.ndim == 2 and contour.shape[1] == 2:
                    contour = contour.reshape(-1, 1, 2)
                return {
                    "contour": convert_ndarray_to_list(contour),
                    "settings": dict(obj.get("settings", {}))
                }
            elif isinstance(obj, list):
                return [convert_ndarray_to_list(item) for item in obj]
            return obj

        # ✅ Handle dict contour directly
        contour_data = convert_ndarray_to_list(workpiece.contour)

        if isinstance(workpiece.sprayPattern, dict):
            spray_pattern_dict = {
                key: [convert_ndarray_to_list(seg) for seg in val]
                for key, val in workpiece.sprayPattern.items()
            }
        else:
            spray_pattern_dict = convert_ndarray_to_list(workpiece.sprayPattern)

        workpiece.contour = contour_data
        workpiece.sprayPattern = spray_pattern_dict
        return workpiece.toDict()

    @staticmethod
    @staticmethod
    def deserialize(data):
        def convert_list_to_ndarray(obj):
            if isinstance(obj, dict) and "contour" in obj:
                arr = np.array(obj["contour"], dtype=np.float32)

                # ✅ Normalize shape to (N, 1, 2)
                if arr.ndim == 1 and arr.shape[0] == 2:
                    arr = arr.reshape(1, 1, 2)  # single point → (1, 1, 2)
                elif arr.ndim == 2 and arr.shape[1] == 2:
                    arr = arr.reshape(-1, 1, 2)  # (N, 2) → (N, 1, 2)

                return {
                    "contour": arr,
                    "settings": obj.get("settings", {})
                }

            elif isinstance(obj, list):
                return [convert_list_to_ndarray(item) for item in obj]

            return obj

        # ----- Main contour -----
        raw_contour = data.get(WorkpieceField.CONTOUR.value, [])

        if isinstance(raw_contour, dict):
            contour = convert_list_to_ndarray(raw_contour)
        elif isinstance(raw_contour, list):
            contour = [convert_list_to_ndarray(seg) for seg in raw_contour]
        else:
            contour = raw_contour  # unexpected type, leave as-is

        # ----- Spray pattern -----
        raw_spray_pattern = data.get(WorkpieceField.SPRAY_PATTERN.value, {})
        spray_pattern = {}

        if isinstance(raw_spray_pattern, dict):
            for key, pattern in raw_spray_pattern.items():
                spray_pattern[key] = [convert_list_to_ndarray(seg) for seg in pattern]
        else:
            spray_pattern = raw_spray_pattern

        # ----- Build workpiece -----
        workpiece = Workpiece.fromDict(data)
        workpiece.contour = contour
        workpiece.sprayPattern = spray_pattern
        return workpiece

    def toDict(self):
        """
                Convert the Workpiece object into a dictionary representation.

                Returns:
                    dict: A dictionary containing the Workpiece's properties, suitable for serialization or storage.
                """
        return {
            WorkpieceField.WORKPIECE_ID.value: self.workpieceId,
            WorkpieceField.NAME.value: self.name,
            WorkpieceField.DESCRIPTION.value: self.description,
            WorkpieceField.TOOL_ID.value: self.toolID.value,
            WorkpieceField.GRIPPER_ID.value: self.gripperID.value,
            WorkpieceField.GLUE_TYPE.value: self.glueType.value,
            WorkpieceField.PROGRAM.value: self.program.value,
            WorkpieceField.MATERIAL.value: self.material,
            WorkpieceField.CONTOUR.value: self.contour,
            WorkpieceField.OFFSET.value: self.offset,
            WorkpieceField.HEIGHT.value: self.height,
            WorkpieceField.GLUE_QTY.value: self.glueQty,
            WorkpieceField.SPRAY_WIDTH.value: self.sprayWidth,
            WorkpieceField.SPRAY_PATTERN.value: self.sprayPattern,
            WorkpieceField.CONTOUR_AREA.value: self.contourArea,
            WorkpieceField.NOZZLES.value: self.nozzles

        }

    @staticmethod
    def flatten_spray_pattern(obj):
        """
             Flatten nested spray pattern lists into a single list.

             Args:
                 obj (list): The spray pattern (possibly nested) to be flattened.

             Returns:
                 list: A flattened list containing all points from the spray pattern.
             """
        if isinstance(obj, list):
            flat_obj = []
            for item in obj:
                if isinstance(item, list):
                    flat_obj.extend(Workpiece.flatten_spray_pattern(item))
                else:
                    flat_obj.append(item)
            return flat_obj
        return [obj]

    @staticmethod
    def reshape_spray_pattern(obj):
        """
        Reshape spray pattern list into list of (N, 1, 2) numpy arrays.

        Args:
            obj (list): The spray pattern, either a single contour or a list of contours.

        Returns:
            list: A list of numpy arrays representing the reshaped spray pattern contours.

        Raises:
            ValueError: If the spray pattern format is invalid or unrecognized.
        """
        if not obj:
            return []

        # If it's a single contour, flatten and reshape it
        if all(isinstance(pt, (list, np.ndarray)) and len(pt) == 2 for pt in obj):
            grouped = np.array(obj, dtype=np.float32).reshape(-1, 1, 2)
            return [grouped]

        # If it's a list of contours
        if isinstance(obj, list) and all(isinstance(c, list) for c in obj):
            result = []
            for contour in obj:
                if not contour:
                    continue
                flat = Workpiece.flatten_spray_pattern(contour)
                if all(isinstance(x, (int, float)) for x in flat):
                    grouped = [[flat[i], flat[i + 1]] for i in range(0, len(flat), 2)]
                elif all(isinstance(x, list) and len(x) == 2 for x in flat):
                    grouped = flat
                else:
                    raise ValueError(f"Invalid spray pattern shape: {flat}")
                result.append(np.array(grouped, dtype=np.float32).reshape(-1, 1, 2))
            return result

        raise ValueError(f"Unknown spray pattern format: {obj}")

    @staticmethod
    def fromDict(dict):
        """
        Deserialize a dictionary into a Workpiece object.

        Args:
          dict (dict): A dictionary representation of a Workpiece.

        Returns:
          Workpiece: The reconstructed Workpiece object.
        """
        return Workpiece(
            workpieceId=dict[WorkpieceField.WORKPIECE_ID.value],
            name=dict[WorkpieceField.NAME.value],
            description=dict[WorkpieceField.DESCRIPTION.value],
            toolID=ToolID(dict[WorkpieceField.TOOL_ID.value]),
            gripperID=Gripper(dict[WorkpieceField.GRIPPER_ID.value]),
            glueType=GlueType(dict[WorkpieceField.GLUE_TYPE.value]),
            program=Program(dict[WorkpieceField.PROGRAM.value]),
            material=dict[WorkpieceField.MATERIAL.value],
            contour=dict[WorkpieceField.CONTOUR.value],
            offset=dict[WorkpieceField.OFFSET.value],
            height=dict[WorkpieceField.HEIGHT.value],
            nozzles=dict.get(WorkpieceField.NOZZLES.value, []),  # Setting nozzles to empty list if missing
            contourArea=dict[WorkpieceField.CONTOUR_AREA.value],
            glueQty=dict[WorkpieceField.GLUE_QTY.value],
            sprayWidth=dict[WorkpieceField.SPRAY_WIDTH.value],
            sprayPattern=dict.get(WorkpieceField.SPRAY_PATTERN.value, [])
            # Setting spray pattern to empty list if missing
        )
