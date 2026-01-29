#!/usr/bin/env python3
import asyncio
from struct import pack
from bleak import BleakClient

# ========================
#  SETTINGS
# ========================

WEDO_MAC = "04:EE:03:16:ED:1D"

# UUIDs from GATT
OUTPUT_COMMAND_UUID = "00001565-1212-efde-1523-785feabcd123"  # motor/led/sound
BATTERY_UUID        = "00002a19-0000-1000-8000-00805f9b34fb"  # battery level

# Ports
PORT_A = 1
PORT_B = 2

# Motor control constants (logical, not BLE)
REVERSE      = 0x9B
SPEED_UP     = 0x01
SPEED_DOWN   = 0x7F
MAX_SPEED    = 0x64   # 100
MIN_SPEED    = 0x01   # 1
SPEED_CHANGE = 0x04   # +4 / -4 per step


# ========================
#  Motor Class
# ========================

class Motor:
    """
    Simple class to control a WeDo 2.0 motor over BLE (bleak).
    Uses the format:
      pack("<bbbb", port, 0x01, 0x01, power)
    where power is signed -100..100.
    """

    def __init__(self, client: BleakClient, port: int):
        self.client = client
        self.port = port
        self.speed = 0  # current speed (signed, -100..100)

    async def _send_power(self, power: int):
        """Internal: send raw motor command."""
        if power > 100:
            power = 100
        if power < -100:
            power = -100

        self.speed = power
        cmd = pack("<bbbb", self.port, 0x01, 0x01, power)
        await self.client.write_gatt_char(OUTPUT_COMMAND_UUID, cmd)
        print(f"[MOTOR] port={self.port}, power={power}")

    async def set_power(self, power: int):
        """Set motor power directly (-100..100)."""
        await self._send_power(power)

    async def stop(self):
        """Stop motor (power=0)."""
        await self._send_power(0)

    async def forward(self, power: int = 50):
        """Rotate forward with given power."""
        if power < 0:
            power = -power
        await self._send_power(power)

    async def backward(self, power: int = 50):
        """Rotate backward with given power."""
        if power < 0:
            power = -power
        await self._send_power(-power)

    async def reverse(self):
        """Reverse direction (REVERSE behavior)."""
        if self.speed == 0:
            # If stopped, start backward by default
            await self._send_power(-50)
        else:
            await self._send_power(-self.speed)

    async def speed_up(self, step: int = SPEED_CHANGE):
        """Increase speed (SPEED_UP)."""
        if self.speed > 0:
            new_speed = self.speed + step
        elif self.speed < 0:
            new_speed = self.speed - step
        else:
            new_speed = SPEED_CHANGE
        await self._send_power(new_speed)

    async def speed_down(self, step: int = SPEED_CHANGE):
        """Decrease speed (SPEED_DOWN)."""
        if self.speed > 0:
            new_speed = self.speed - step
        elif self.speed < 0:
            new_speed = self.speed + step
        else:
            new_speed = 0
        await self._send_power(new_speed)


# ========================
#  Hub Class
# ========================

class WeDoHubBle:
    """
    Simple wrapper for WeDo 2.0 hub using bleak.
    Provides:
      - connect() / disconnect()
      - read_battery()
      - motorA / motorB fields (Motor objects)
    """

    def __init__(self, mac: str):
        self.mac = mac
        self.client = BleakClient(mac)
        self.motorA = Motor(self.client, PORT_A)
        self.motorB = Motor(self.client, PORT_B)

    async def connect(self):
        print(f"[HUB] Connecting to {self.mac} ...")
        await self.client.connect()
        if self.client.is_connected:
            print("[HUB] Connected.")
        else:
            raise RuntimeError("Could not connect to WeDo hub.")
        
    async def disconnect(self):
        """Safely disconnect from hub, ignoring DBus errors."""
        if self.client.is_connected:
            try:
                await self.client.disconnect()
            except Exception as e:
                # Some BlueZ/DBus backends throw on disconnect if already gone
                print("[HUB] Error on disconnect (ignored):", e)
        print("[HUB] Disconnected.")

    async def read_battery(self) -> int | None:
        try:
            data = await self.client.read_gatt_char(BATTERY_UUID)
            level = data[0]
            print(f"[HUB] Battery level: {level}%")
            return level
        except Exception as e:
            print("[HUB] Battery read error:", e)
            return None


# ========================
#  DEMO / MAIN
# ========================

async def demo():
    hub = WeDoHubBle(WEDO_MAC)

    try:
        await hub.connect()
        await hub.read_battery()

        # Choose motor port:
        motor = hub.motorB   # or hub.motorA if motor is on port A

        print("\n>>> Forward 50% for 2 seconds")
        await motor.forward(50)
        await asyncio.sleep(2)

        print("\n>>> Speed up a few times")
        for _ in range(3):
            await motor.speed_up()
            await asyncio.sleep(1)

        print("\n>>> Reverse direction")
        await motor.reverse()
        await asyncio.sleep(2)

        print("\n>>> Slow down until stop")
        for _ in range(10):
            await motor.speed_down()
            await asyncio.sleep(0.4)
            if motor.speed == 0:
                break

        print("\n>>> Final stop (safety)")
        await motor.stop()

    except KeyboardInterrupt:
        print("\n[DEMO] Interrupted by user.")
        await motor.stop()
    finally:
        await hub.disconnect()


if __name__ == "__main__":
    asyncio.run(demo())
