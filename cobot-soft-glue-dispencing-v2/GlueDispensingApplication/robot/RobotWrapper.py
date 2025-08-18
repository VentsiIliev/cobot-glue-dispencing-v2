import logging
import platform
import logging
if platform.system() == "Windows":
    from fairino.windows import Robot
elif platform.system() == "Linux":
    logging.info("Linux detected")
    from fairino.linux import Robot
else:
    raise Exception("Unsupported OS")

from enum import Enum
class TestRobotWrapper():
    """
       A mock wrapper class simulating robot control functionality for testing purposes.
       """
    def __init__(self):
        pass

    def moveCart(self,position, tool, user, vel=100, acc=30):
        print("MoveCart: ", position, tool, user, vel, acc)
        return position

    def moveL(self,position, tool, user, vel, acc, blendR):
        print("MoveL: ", position, tool, user, vel, acc, blendR)
        return position

    def getCurrentPosition(self):
        return [0, 0, 0, 0, 0, 0]

    def getCurrentLinierSpeed(self):
        return "Test Robot"

    def enable(self):
        pass
    def disable(self):
        pass
    def printSdkVerison(self):
        pass
    def setDigitalOutput(self, portId, value):
        pass


class Axis(Enum):
    """
    Enum representing robot movement axes.
    """
    X = 1
    Y = 2
    Z = 3
    RX = 4
    RY = 5
    RZ = 6

    def __str__(self):
        return self.name

    @staticmethod
    def get_by_string(name):
        """
        Retrieve an Axis enum value by its string representation.

        Args:
            name (str): The string representation of the axis.

        Returns:
            Axis: The corresponding Axis enum value.

        Raises:
            ValueError: If the string does not match any Axis enum.
        """
        try:
            return Axis[name.upper()]
        except KeyError:
            raise ValueError(f"Invalid axis name: {name}")

class Direction(Enum):
    """
       Enum representing movement directions along an axis.
       """
    MINUS = 0
    PLUS = 1

    def __str__(self):
        return self.name

    @staticmethod
    def get_by_string(name):
        try:
            return Direction[name.upper()]
        except KeyError:
            raise ValueError(f"Invalid Direction name: {name}")

class RobotWrapper:
    """
      A wrapper for the real robot controller, abstracting motion and I/O operations.
      """
    def __init__(self, ip):
        """
               Initializes the robot wrapper and connects to the robot via RPC.

               Args:
                   ip (str): IP address of the robot controller.
               """
        self.ip = ip
        self.robot = Robot.RPC(self.ip)

        """overSpeedStrategy: over speed handling strategy
        0 - strategy off;
        1 - standard;
        2 - stop on error when over speeding;
        3 - adaptive speed reduction, default 0"""
        self.overSpeedStrategy = 3



    def moveCart(self,position, tool, user, vel=100, acc=30):
        """
              Moves the robot in Cartesian space.

              Args:
                  position (list): Target Cartesian position.
                  tool (int): Tool frame ID.
                  user (int): User frame ID.
                  vel (float): Velocity.
                  acc (float): Acceleration.

              Returns:
                  list: Result from robot move command.
              """
        return self.robot.MoveCart(position, tool, user, vel=vel, acc=acc)

    def moveL(self,position, tool, user, vel, acc, blendR):
        """
              Executes a linear movement with blending.

              Args:
                  position (list): Target position.
                  tool (int): Tool frame ID.
                  user (int): User frame ID.
                  vel (float): Velocity.
                  acc (float): Acceleration.
                  blendR (float): Blend radius.

              Returns:
                  list: Result from robot linear move command.
              """

        return self.robot.MoveL(position, tool, user, vel=vel, acc=acc, blendR=blendR)

    def getCurrentPosition(self):
        """
              Retrieves the current TCP (tool center point) position.

              Returns:
                  list: Current robot TCP pose.
              """
        currentPose = self.robot.GetActualTCPPose()
        # check if int
        if isinstance(currentPose, int):
            currentPose = None
        else:
            currentPose = currentPose[1]

        return currentPose

    def getCurrentLinerSpeed(self):
        """
               Retrieves the current linear speed of the TCP.

               Returns:
                   float: TCP composite speed.
               """
        res = self.robot.GetActualTCPCompositeSpeed()
        # result = res[0]
        # compSpeed = res[1]
        # linSpeed = compSpeed[0]
        # linSpeed = res[1][0]
        # print(f"result {result}  comp Speed {compSpeed} linSpeed {linSpeed}")
        # return linSpeed
        return res


    def enable(self):
        """
               Enables the robot, allowing motion.
               """
        self.robot.RobotEnable(1)

    def disable(self):
        """
             Disables the robot, preventing motion.
             """
        self.robot.RobotEnable(0)

    def printSdkVersion(self):
        """
              Prints the current SDK version of the robot controller.
              """
        version = self.robot.GetSDKVersion()
        print(version)
        return version

    def setDigitalOutput(self, portId, value):
        """
              Sets a digital output pin on the robot.

              Args:
                  portId (int): Output port number.
                  value (int): Value to set (0 or 1).
              """
        return  self.robot.SetDO(portId, value)

    def startJog(self,axis,direction,step,vel,acc):
        """
              Starts jogging the robot in a specified axis and direction.

              Args:
                  axis (Axis): Axis to jog.
                  direction (Direction): Jog direction (PLUS or MINUS).
                  step (float): Distance to move.
                  vel (float): Velocity of jog.
                  acc (float): Acceleration of jog.

              Returns:
                  object: Result of the StartJOG command.
              """
        axis = axis.value
        direction = direction.value
        print(f"StartJOG: axis={axis}, direction={direction}, step={step}, vel={vel}, acc={acc}")
        return self.robot.StartJOG(ref=4,nb=axis,dir=direction,vel=vel,acc=acc,max_dis=step)


    def stopMotion(self):
        """
               Stops all current robot motion.

               Returns:
                   object: Result of StopMotion command.
               """
        return self.robot.StopMotion()

    def resetAllErrors(self):
        """
               Resets all current error states on the robot.

               Returns:
                   object: Result of ResetAllError command.
               """
        return self.robot.ResetAllError()
