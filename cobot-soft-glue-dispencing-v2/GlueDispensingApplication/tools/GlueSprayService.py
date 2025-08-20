import time
import minimalmodbus
from GlueDispensingApplication.modbusCommunication.ModbusClient import ModbusClient
from linuxUtils import *
from datetime import datetime, timedelta
from GlueDispensingApplication.modbusCommunication.ModbusClient import ModbusClient
from GlueDispensingApplication.Statistics import Statistics
import threading
import time
from datetime import datetime, timedelta

class Timer:
    def __init__(self, timeout_minutes, on_timeout_callback):
        """
        :param timeout_minutes: Duration after which to trigger the callback.
        :param on_timeout_callback: Function to call when timeout is reached.
        """
        self.timeout_minutes = timeout_minutes
        self.on_timeout_callback = on_timeout_callback
        self.start_time = None
        self.stop_time = None
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self.elapsed_seconds = None

    def start(self):
        """Starts or restarts the generator timer."""
        self.start_time = datetime.now()
        self.stop_time = None
        self.elapsed_seconds = None
        self._stop_event.clear()

        if self._monitor_thread and self._monitor_thread.is_alive():
            return  # Already running

        self._monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self._monitor_thread.start()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Timer started (timeout = {self.timeout_minutes} min)")

    def stop(self):
        """Stops the generator timer."""
        self._stop_event.set()
        if self._monitor_thread and threading.current_thread() != self._monitor_thread:
            self._monitor_thread.join(timeout=1)
        self._monitor_thread = None
        self.stop_time = datetime.now()
        if self.start_time:
            self.elapsed_seconds = (self.stop_time - self.start_time).total_seconds()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Timer stopped, elapsed: {self.elapsed_seconds:.2f} seconds")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Timer stopped")

    def _monitor(self):
        while not self._stop_event.is_set():
            if self.start_time and datetime.now() - self.start_time > timedelta(minutes=self.timeout_minutes):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Generator timeout reached!")
                self.on_timeout_callback()
                break
            else:
                # Check every 5 seconds
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Timer is running...")
            time.sleep(5)

class GlueSprayService:
    def __init__(self,generatorTurnOffTimeout=10):

        self.relaysId = 1
        self.motorsId = 1
        self.fanId = 1
        self.generatorTurnOffTimeout = generatorTurnOffTimeout # minutes
        self.timer = Timer(self.generatorTurnOffTimeout, self.generatorOff)

        self.glueA_addresses = 0  # MOTOR
        self.glueB_addresses = 1  # MOTOR
        self.glueC_addresses = 2  # MOTOR
        self.glueD_addresses = 3  # MOTOR

        self.generator_relay_address = 8  # generator relay address

        self.fanSpeed_address = 14  # fan speed address values 1-100 + 28

        self.generatorCurrentState = False  # Initial generator state

        self.glueMapping = {
            1: self.glueA_addresses,
            2: self.glueB_addresses,
            3: self.glueC_addresses,
            4: self.glueD_addresses
        }

    """ MOTOR CONTROL """

    def motorOff(self,motorAddress,speedReverse,delay):
        result = False
        try:
            client = self.getModbusClient(self.motorsId)

            # client.writeRegister(motorAddress, 0)
            # client.writeRegister(motorAddress, -speedReverse, signed=True)  # Set reverse speed

            print(f"Motor reverse time = {delay} seconds")
            # time.sleep(delay)  # Wait for the motor to stop complete reverse movement

            client.writeRegister(motorAddress, 0)  # Reverse steps if needed
            client.close()
            print(f"Motor {motorAddress} Off")
            result = True
        except Exception as e:
            print(f"Error turning off motor {motorAddress}: {e}")
        return result

    def motorOn(self, motorAddress, speed):
        result = False
        try:
            client = self.getModbusClient(self.motorsId)
            client.writeRegister(motorAddress, speed)  # Ensure final speed is set
            client.close()
            print(f"Motor {motorAddress} On with speed {speed}")
            result = True
        except Exception as e:
            print(f"Error turning on motor {motorAddress}: {e}")
        return result


    def motorState(self, motorAddress):
        result = False
        state = None
        try:
            """READ MOTOR STATE"""
            client = self.getModbusClient(self.motorsId)
            client.writeRegister(motorAddress, 0)  # reset motor
            state = client.read(motorAddress)  # Read motor state
            print(f"Motor {motorAddress} state: {state}")
            client.close()
            result = True
        except Exception as e:
            import traceback
            # traceback.print_exc()
            print(f"Error reading motor {motorAddress} state: {e}")

        return result, state


    """ GENERATOR CONTROL """

    def generatorOff(self):

        if self.generatorCurrentState is False:
            print("Generator is already OFF")
            return True

        result = False
        try:
            client = self.getModbusClient(self.relaysId)
            client.writeRegister(self.generator_relay_address, 0)
            client.close()

            self.timer.stop()
            Statistics.incrementGeneratorOnSeconds(self.timer.elapsed_seconds or 0)


            print("Generator OFF")
            result = True
            self.generatorCurrentState = False
        except Exception as e:
            print(f"Error turning off generator: {e}")
        return result

    def generatorOn(self):

        if self.generatorCurrentState is True:
            print("Generator is already ON")
            return True

        result = False
        try:
            client = self.getModbusClient(self.relaysId)
            client.writeRegister(self.generator_relay_address, 1)

            self.timer.start()


            print("Generator ON")
            result = True
            self.generatorCurrentState = True
        except Exception as e:
            print(f"Error turning on generator: {e}")
        return result

    def generatorState(self):
        """READ GENERATOR STATE"""
        result = False
        state = None
        try:
            client = self.getModbusClient(self.relaysId)
            state = client.readBit(self.generator_relay_address, functioncode=1)
            client.close()
            print(f"Generator state: {state}")
            result = True
        except Exception as e:
            print(f"Error reading generator state: {e}")
        return result, state

    """ FAN CONTROL """

    def fanOff(self):  # FAN SPEED
        result = False
        try:
            client = self.getModbusClient(self.fanId)
            client.writeRegister(self.fanSpeed_address, 0)
            client.close()
            print(f"Fan OFF")
            result = True
        except Exception as e:
            print(f"Error turning off fan: {e}")
        return result

    def fanOn(self,value):  # FAN SPEED
        result = False
        try:
            client = self.getModbusClient(self.fanId)
            client.writeRegister(self.fanSpeed_address, value + 28)
            client.close()
            print(f"Fan ON with speed {value}")
            result = True
        except Exception as e:
            print(f"Error turning on fan: {e}")
        return result

    def fanState(self):
        """READ FAN STATE"""
        result = False
        state = None
        try:
            client = self.getModbusClient(self.fanId)
            state = client.read(self.fanSpeed_address)  # Read fan speed
            client.close()
            print(f"Fan speed: {state}")
            result = True
        except Exception as e:
            print(f"Error reading fan state: {e}")
        return result, state

    """ GLUE SPRAY CONTROL"""

    def startGlueDispensing(self,glueType_addresses, speed, stepsReverse, speedReverse, delay=0.5, fanSpeed=0):
        result = False
        try:
            motorAddress = glueType_addresses[1]
            self.fanOn(fanSpeed)

            self.generatorOn()

            time.sleep(delay)
            self.relayOn(glueType_addresses[0])  # Turn on glue relay
            # [134, 2]
            # self.relayOn(134) # Turn on glue B relay
            self.motorOn(motorAddress, speed, speedReverse, stepsReverse)
            # self.motorOn(2,speed, speedReverse, stepsReverse)  # Turn off glue B motor
            print(
                f"Glue dispensing started for {glueType_addresses[0]} at speed {speed}, stepsReverse {stepsReverse}, speedReverse {speedReverse}")
            result = True
        except Exception as e:
            import traceback
            self.generatorOff()
            print(f"Error starting glue dispensing for {glueType_addresses[0]}: {e}")
            traceback.print_exc()
        return result

    def stopGlueDispensing(self,glueType_addresses,delay=0.5):
        result = False
        try:
            motorAddress = glueType_addresses[1]
            print(motorAddress)
            self.motorOff(motorAddress)
            # print(f"MotorB {self.glueB_addresses} Off")
            # self.motorOff(2)  # Turn off glue B motor
            time.sleep(delay)
            self.generatorOff()
            print(f"Glue dispensing stopped for {glueType_addresses[0]}")
            result = True
        except Exception as e:
            print(f"Error stopping glue dispensing for {glueType_addresses[0]}: {e}")
        return result

    def getModbusClient(self,slaveId):
        port = get_modbus_port()
        # port = "/dev/ttyS1"
        # client = minimalmodbus.Instrument(port, slaveId)
        client = ModbusClient(slave=slaveId, port=port)
        print(f"Connected Port: {port} Slave Id: {slaveId}")

        """CLIENT CONFIG"""
        if slaveId == self.relaysId:
            client.client.serial.baudrate = 115200
        elif slaveId == self.motorsId:
            client.client.serial.baudrate = 115200
            # print(" client.serial.baudrate = 115200")
        else:
            # print("Invalid slave id: ", slaveId)
            raise ValueError("Invalid slave id: ",slaveId)
        client.client.serial.bytesize = 8
        client.client.serial.parity = minimalmodbus.serial.PARITY_NONE
        client.client.serial.stopbits = 1
        client.client.serial.timeout = 0.1  # 500 ms timeout
        client.clear_buffers_before_each_transaction = True
        # client.close_port_after_each_call = False
        client.mode = minimalmodbus.MODE_RTU
        client.client.serial.inter_byte_timeout = 0.02  # 20 ms delay

        return client

if __name__ == "__main__":
    glueService = GlueSprayService()
    # glueService.generatorOn()
    # time.sleep(1)
    # glueService.generatorOff()
    client = glueService.getModbusClient(1)
    # glueService.relaysId(134)  # Turn on glue A relay

    # state = glueService.motorState(5)
    # print("Motor State: ", state)


    print("Motor State: ",glueService.motorState(2))
    while True:
        glueService.motorOff(1,0,0.0)
        time.sleep(1)
    # glueService.motorOn(2,5000)
    # time.sleep(5)
    # glueService.motorOff(1,0,0.0)