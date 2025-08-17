import time
import minimalmodbus
import logging
from GlueDispensingApplication.modbusCommunication.modbus_lock import modbus_lock

class ModbusClient:
    """
    ModbusClient class provides functionality to communicate with a Modbus slave device
    using the Modbus RTU protocol via a serial connection. It allows for reading and
    writing registers on the Modbus slave device.

    Attributes:
        slave (int): The Modbus slave address (default is 10).
        client (minimalmodbus.Instrument): An instance of the minimalmodbus Instrument class
                                           used for Modbus communication.
    """
    def __init__(self, slave=10, port='COM5', baudrate=115200, bytesize=8,
                 stopbits=1, timeout=0.01,parity = minimalmodbus.serial.PARITY_NONE):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.slave = slave
        try:
            self.client = minimalmodbus.Instrument(port, self.slave, debug=False)
        except Exception as e:
            raise Exception(f"Could not open port {port}. Please check the connection and port settings.") from e

        self.client.serial.baudrate = baudrate
        self.client.serial.bytesize = bytesize
        self.client.serial.stopbits = stopbits
        self.client.serial.timeout = timeout
        self.client.serial.parity = parity

    def writeRegister(self, register, value,signed=False):
        maxAttempts = 1
        attempts = 0
        while attempts < maxAttempts:
            with modbus_lock:
                try:
                    self.client.write_register(register, value,signed=signed)
                    break
                except minimalmodbus.ModbusException as e:
                    import traceback
                    traceback.print_exc()
                    if "Checksum error in rtu mode" in str(e):
                        break
                    else:
                        import traceback
                        traceback.print_exc()
                    attempts += 1
                    time.sleep(0.1)

    def writeRegisters(self, start_register, values):
        maxAttempts = 1
        attempts = 0
        while attempts < maxAttempts:
            with modbus_lock:
                try:
                    self.client.write_registers(start_register, values)
                    break
                except minimalmodbus.ModbusException as e:
                    if "Checksum error in rtu mode" in str(e):
                        break
                    else:
                        import traceback
                        traceback.print_exc()
                    attempts += 1

    def read(self, register):
        with modbus_lock:
            value = None
            try:
                print(f"Read value: {value} from register: {register}")
                value = self.client.read_register(register,signed=True)
                return value
            except (minimalmodbus.ModbusException, minimalmodbus.InvalidResponseError, IOError) as e:
                import traceback
                # traceback.print_exc()
                if "Checksum error in rtu mode" in str(e):
                    return value
                else:
                    import traceback
                    traceback.print_exc()

    def readBit(self,address,functioncode=1):
        with modbus_lock:
            return self.client.read_bit(address,functioncode=functioncode)

    def writeBit(self,address,value):
        maxAttempts = 1
        attempts = 0
        while attempts < maxAttempts:
            with modbus_lock:
                try:
                    self.client.write_bit(address, value)
                    break
                except minimalmodbus.ModbusException as e:
                    if "Checksum error in rtu mode" in str(e):
                        import traceback
                        traceback.print_exc()
                        break
                    else:
                        import traceback
                        traceback.print_exc()
                    attempts += 1
                    time.sleep(0.1)

    def close(self):
        self.client.serial.close()

