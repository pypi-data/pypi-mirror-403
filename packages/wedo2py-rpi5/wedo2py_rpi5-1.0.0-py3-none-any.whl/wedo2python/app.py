#!/usr/bin/env python3
#NEW APP WITH BLEAK LIBRARY FOR RASPBERRY PI 5

import asyncio
import time
from time import sleep
from struct import pack, unpack

from bleak import BleakClient


class WeDo2Python:
    """
    Constants for communication with WeDo 2.0 peripherals
    """
    HANDLE_PORT = 0x15
    HANDLE_BUTTON = 0x11
    HANDLE_SENSOR_VALUE = 0x32
    HANDLE_INPUT_COMMAND = 0x3A
    HANDLE_OUTPUT_COMMAND = 0x3D
    HANDLE_BATTERY_LEVEL = 0x48

    HANDLE_CCC_BUTTON = 0x12
    HANDLE_CCC_PORT = 0x16
    HANDLE_CCC_SENSOR_VALUE = 0x33
    HANDLE_CCC_BATTERY_LEVEL = 0x49

    # BLE UUIDs from GATT 
    SERVICE_IO_UUID = "00004f0e-1212-efde-1523-785feabcd123"

    INPUT_COMMAND_UUID = "00001563-1212-efde-1523-785feabcd123"   # configure sensor modes
    SENSOR_VALUE_UUID = "00001560-1212-efde-1523-785feabcd123"    # sensor values
    OUTPUT_COMMAND_UUID = "00001565-1212-efde-1523-785feabcd123"  # motor / LED / sound
    BATTERY_UUID = "00002a19-0000-1000-8000-00805f9b34fb"         # battery level

    # ==== Sensor and device types ====
    TYPE_TILT = 0x22
    TYPE_MOTION = 0x23

    # Command types and formats
    COMMAND_ID_INPUT_VALUE = 0
    COMMAND_ID_INPUT_FORMAT = 1
    COMMAND_TYPE_READ = 1
    COMMAND_TYPE_WRITE = 2

    # Motor control constants
    REVERSE = 0x9B
    SPEED_UP = 0x01
    SPEED_DOWN = 0x7F
    MAX_SPEED = 0x64
    MIN_SPEED = 0x01
    SPEED_CHANGE = 0x04

    INPUT_FORMAT_UNIT_RAW = 0
    INPUT_FORMAT_UNIT_PERCENT = 1
    INPUT_FORMAT_UNIT_SI = 2

    SENSOR_MODE = 1

    # Tilt direction constants
    TILT_HORIZONTAL = 0
    TILT_UP = 3
    TILT_RIGHT = 5
    TILT_LEFT = 7
    TILT_DOWN = 9
    TILT_UNKNOWN = 10

    KEEP_ALIVE = b"\x01\x00"


    def __init__(self, address: str):
        # BLE
        self.address = address
        self.client: BleakClient | None = None
        self.connected = False

        # Event loop
        self._loop = asyncio.new_event_loop()

        # state
        self.direction = 0
        self.distance = 10
        self.piezoTone = 0
        self.battery_level = 100
        self.motorPower: dict[int, int] = {}      # motor port -> power
        self.motorDirection: dict[int, int] = {}  # motor port -> direction (+1 / -1)

        print(f"Connecting to Lego WeDo 2.0 Device: {address}\n")
        sleep(0.5)


    # ========= HELP FOR ASYNC =========

    def _run(self, coro):
        """Run an async coroutine into event loop."""
        asyncio.set_event_loop(self._loop)
        return self._loop.run_until_complete(coro)
    
    def _start_keep_alive(self):
        async def _keep_alive():
            while self.connected:
                try:
                    await asyncio.sleep(2.5)
                    await self.client.write_gatt_char(self.INPUT_COMMAND_UUID, b"\x01\x00")
                    #print("[KEEPALIVE]")
                except Exception:
                    break
        self._run(_keep_alive())


    # ========= BLE CONNECT / DISCONNECT / BATTERY =========

    async def _connect_async(self):
        if self.client is None:
            self.client = BleakClient(self.address)
        await self.client.connect()
        self.connected = self.client.is_connected
        if self.connected:
            print("WeDo 2.0 Device Connected.\n")
            sleep(0.5)
            await self._read_battery_level_async()
        else:
            print("Could not connect to WeDo 2.0 hub.")

    def connect(self):
        self._start_keep_alive()
        self._run(self._connect_async())
        if self.connected:
            return

    async def _disconnect_async(self):
        if self.client and self.connected:
            try:
                await self.client.disconnect()
            except Exception as e:
                print("[HUB] Error on disconnect (ignored):", e)
            self.connected = False
            print("Disconnected!\n")

    def disconnect(self):
        self._run(self._disconnect_async())
        self.connected = False


    async def _read_battery_level_async(self):
        try:
            if not self.client:
                return None
            data = await self.client.read_gatt_char(self.BATTERY_UUID)
            if data:
                self.battery_level = data[0]
                print(f"Battery Level: {self.battery_level}%\n")
                print("-------------------------------------------\n")
                return self.battery_level
            else:
                print("Could not read battery level.")
                return None
        except Exception as e:
            print(f"Error reading battery level: {e}")
            return None

    def read_battery_level(self):
        """ wrapper."""
        return self._run(self._read_battery_level_async())

    # ========= SOUND / PIEZO =========

    def sound(self, tone_id: int = 1):
        """
        Play a piezo tone. User selects tone number (1-16)

        Example:
        sound(1) > A
        sound(5) > eH
        sound(16) > cH Long
        """

        TONES = {
            1:  b'\x05\x02\x04\xB8\x01\xF4\x01',  # A
            2:  b'\x05\x02\x04\x5D\x01\x5E\x01',  # F
            3:  b'\x05\x02\x04\x0B\x02\x96\x00',  # cH
            4:  b'\x05\x02\x04\xB8\x01\xE8\x03',  # A 1000
            5:  b'\x05\x02\x04\x93\x02\xF4\x01',  # eH
            6:  b'\x05\x02\x04\xBA\x02\x5E\x01',  # fH
            7:  b'\x05\x02\x04\x9F\x01\xF4\x01',  # gS
            8:  b'\x05\x02\x04\xE4\x02\xFA\x00',  # fS
            9:  b'\x05\x02\x04\x10\x03\xFA\x00',  # G
            10: b'\x05\x02\x04\xC7\x01\xFA\x00',  # aS
            11: b'\x05\x02\x04\x4B\x02\xFA\x00',  # dH
            12: b'\x05\x02\x04\x2A\x02\xFA\x00',  # cSH
            13: b'\x05\x02\x04\xD2\x01\x7D\x00',  # B
            14: b'\x05\x02\x04\xE4\x02\x7D\x00',  # fSH
            15: b'\x05\x02\x04\xB8\x01\xF4\x03',  # A 500
            16: b'\x05\x02\x04\x0B\x02\xF4\x01',  # cH Long
        }

        if tone_id not in TONES:
            print(f"Invalid tone {tone_id}. Choose 1-16.")
            return

        tone = TONES[tone_id]

        async def _sound_async():
            try:
                await self.client.write_gatt_char(self.OUTPUT_COMMAND_UUID, tone)
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"Error playing piezo tone: {e}")

        self._run(_sound_async())
        time.sleep(0.05)

    def sound_off(self):
        """
        Stop the sound
        """
        async def _sound_off_async():
            try:
                if not self.client:
                    return
                pass
            except Exception as e:
                print(f"Error turning piezo sound off: {e}")

        self._run(_sound_off_async())
        time.sleep(0.05)


    # ========= LED COLOR =========

    def set_color(self, color_name: str):
        """
        Change LED colors.
        """
        color_map = {
            'off': 0x00,
            'pink': 0x01,
            'purple': 0x02,
            'blue': 0x03,
            'lightblue': 0x04,
            'cyan': 0x05,
            'green': 0x06,
            'yellow': 0x07,
            'orange': 0x08,
            'red': 0x09,
            'white': 0x0A
        }

        async def _set_color_async():
            if color_name not in color_map:
                print(f"The color {color_name} is invalid.")
                return

            color_code = color_map[color_name]
            cmd = bytes([0x06, 0x04, 0x01, color_code])
            try:
                if not self.client:
                    return
                await self.client.write_gatt_char(self.OUTPUT_COMMAND_UUID, cmd)
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"Error changing color: {e}")

        self._run(_set_color_async())
        time.sleep(0.05)


    def colors(self):
        """
        show all the colors sequentially.
        """
        for name in ['off', 'pink', 'purple', 'blue', 'lightblue',
                     'cyan', 'green', 'yellow', 'orange', 'red', 'white']:
            self.set_color(name)
            sleep(0.5)

    # ========= PORT HELPER =========

    def port(self, port_name: str) -> int | None:
        """
        Return port number for 'A' or 'B'.
        """
        ports = {
            'A': 1,
            'B': 2
        }
        try:
            if port_name in ports:
                return ports[port_name]
            else:
                print(f"The port {port_name} is invalid. Please input 'A' or 'B'.")
                return None
        except Exception as e:
            print(f"Error retrieving port: {e}")
            return None

    # ========= MOTOR CONTROL =========

    async def _send_motor_command_async(self, motor_port: int, power: int):
        """
        Send command in motor
        pack("<bbbb", port, 0x01, 0x01, signed_power)
        """
        if not self.client:
            return

        if power > 100:
            power = 100
        if power < -100:
            power = -100

        cmd = pack("<bbbb", motor_port, 0x01, 0x01, power)
        try:
            await self.client.write_gatt_char(self.OUTPUT_COMMAND_UUID, cmd)
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"Error turning motor on/off: {e}")

    def set_motor_power(self, motor_port: int, motor_power: int):
        """
        It puts power to the motor (without changing direction).
        """
        motor_name = "A" if motor_port == 1 else "B"
        self.motorPower[motor_port] = motor_power
        print(f"Motor {motor_name} power set to {motor_power}%.")

    def motor_reverse(self, motor_port: int):
        """
        Reversal of direction.
        """
        current_direction = self.motorDirection.get(motor_port, 1)
        new_direction = -current_direction
        self.motorDirection[motor_port] = new_direction

    def motor_that_way(self, motor_port: int):
        """
        Sets direction "right" (positive).        
        """
        self.motorDirection[motor_port] = 1

    def motor_this_way(self, motor_port: int):
        """
        Sets direction "left" (negative).
        """
        self.motorDirection[motor_port] = -1

    def motor_on(self, motor_port: int):
        """
        Starts motor with current power & direction.

        """
        direction = self.motorDirection.get(motor_port, 1)
        power = self.motorPower.get(motor_port, 100)

        async def _motor_on_async():
            await self._send_motor_command_async(motor_port, direction * power)

        self._run(_motor_on_async())

    def motor_off(self, motor_port: int):
        """
        Stop motor (power=0).
        """
        async def _motor_off_async():
            await self._send_motor_command_async(motor_port, 0)

        self._run(_motor_off_async())

    # ========= DISTANCE SENSOR =========

    def distance_sensor(self, port: int):
        """
        Configure motion/distance sensor in specific port.
        """
        async def _config_distance_async():
            if not self.client:
                return
            # 01 02 CH 23 00 01 00 00 00 02 01
            cmd = bytes([
                self.COMMAND_ID_INPUT_FORMAT,
                self.COMMAND_TYPE_WRITE,
                port,
                self.TYPE_MOTION,
                0x00,      # mode for distance
                0x01,      # delta
                0x00, 0x00, 0x00,
                0x02,
                0x01,
            ])
            try:
                await self.client.write_gatt_char(self.INPUT_COMMAND_UUID, cmd)
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"Error configuring distance sensor: {e}")

        self._run(_config_distance_async())
        time.sleep(0.05)

    def read_distance_value(self):
        """
        Read value from distance sensor.
        Return distance "cm".
        """
        async def _read_dist_async():
            try:
                if not self.client:
                    return None
                data = await self.client.read_gatt_char(self.SENSOR_VALUE_UUID)
                await asyncio.sleep(0.05)
                if not data or len(data) < 1:
                    return None
                raw = data[-1]
                return int(raw)
            except Exception as e:
                print(f"Error reading distance sensor data: {e}")
                return None

        return self._run(_read_dist_async())

        time.sleep(0.05)

    # ========= TILT SENSOR =========

    def tilt_sensor(self, port: int):
        """
        Configure tilt sensor in specific port.
        """
        async def _config_tilt_async():
            if not self.client:
                return
            # 01 02 CH 22 01 01 00 00 00 02 01
            cmd = bytes([
                self.COMMAND_ID_INPUT_FORMAT,
                self.COMMAND_TYPE_WRITE,
                port,
                self.TYPE_TILT,
                0x01,  # tilt mode
                0x01,  # delta
                0x00, 0x00, 0x00,
                0x02,
                0x01,
            ])
            try:
                await self.client.write_gatt_char(self.INPUT_COMMAND_UUID, cmd)
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"Error configuring tilt sensor: {e}")

        self._run(_config_tilt_async())
        time.sleep(0.05)


    @staticmethod
    def _decode_tilt_to_constant(raw_bytes: bytes) -> int:
        """
        Take the 6 bytes from SENSOR_VALUE_UUID and turns them into one of:       
        TILT_HORIZONTAL, TILT_UP, TILT_RIGHT, TILT_LEFT, TILT_DOWN, TILT_UNKNOWN
        Based on the patterns we measured:

          HORIZONTAL: [02 01 00 00 00 00] -> b4=00, b5=00
          RIGHT     : [02 01 00 00 A0 40] -> b4=A0, b5=40
          LEFT      : [02 01 00 00 E0 40] -> b4=E0, b5=40
          UP        : [02 01 00 00 40 40] -> b4=40, b5=40
          DOWN      : [02 01 00 00 10 41] -> b4=10, b5=41
        """
        if raw_bytes is None or len(raw_bytes) < 6:
            return WeDo2Python.TILT_UNKNOWN

        b4 = raw_bytes[4]
        b5 = raw_bytes[5]

        if b4 == 0x00 and b5 == 0x00:
            return WeDo2Python.TILT_HORIZONTAL
        if b4 == 0xA0 and b5 == 0x40:
            return WeDo2Python.TILT_RIGHT
        if b4 == 0xE0 and b5 == 0x40:
            return WeDo2Python.TILT_LEFT
        if b4 == 0x40 and b5 == 0x40:
            return WeDo2Python.TILT_UP
        if b4 == 0x10 and b5 == 0x41:
            return WeDo2Python.TILT_DOWN
        return WeDo2Python.TILT_UNKNOWN

    def read_tilt_value(self):
        """
        Read br raw bytes from tilt sensor and return
        one of the TILT_* constants (0,3,5,7,9,10).
        """
        async def _read_tilt_async():
            try:
                if not self.client:
                    return None
                data = await self.client.read_gatt_char(self.SENSOR_VALUE_UUID)
                if not data:
                    return None
                tilt_const = self._decode_tilt_to_constant(data)
                self.direction = tilt_const
                return tilt_const
            except Exception as e:
                print(f"Error reading tilt sensor data: {e}")
                return None

        return self._run(_read_tilt_async())
        time.sleep(0.05)


    def print_tilt_any(self, tilt_value: int):
        """
          Read any orientation of tilt sensor
        """
        if tilt_value == self.TILT_HORIZONTAL:
            return None
        if tilt_value in [self.TILT_LEFT, self.TILT_RIGHT,
                          self.TILT_UP, self.TILT_DOWN]:
            return tilt_value
        return None
