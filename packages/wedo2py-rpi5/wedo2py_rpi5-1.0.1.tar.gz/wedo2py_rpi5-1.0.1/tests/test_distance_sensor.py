#!/usr/bin/env python3
import asyncio
from struct import pack, unpack

from bleak import BleakClient

WEDO_MAC = "04:EE:03:16:ED:1D"

SERVICE_WEDO = "00004f0e-1212-efde-1523-785feabcd123"

INPUT_COMMAND_UUID = "00001563-1212-efde-1523-785feabcd123"  # set sensor mode
SENSOR_VALUE_UUID = "00001560-1212-efde-1523-785feabcd123"   # read sensor values

BATTERY_UUID = "00002a19-0000-1000-8000-00805f9b34fb"        # battery level

TYPE_MOTION = 0x23
COMMAND_ID_INPUT_FORMAT = 0x01   # input format command id
COMMAND_TYPE_WRITE = 0x02
INPUT_FORMAT_UNIT_RAW = 0x00

THRESHOLD_CM = 10.0  


async def configure_distance_sensor(client, port: int = 2):
    """
    
    mode = 0x00  # distance mode
    # 11 bytes command
    cmd = bytes([
        COMMAND_ID_INPUT_FORMAT,
        COMMAND_TYPE_WRITE,
        port,
        TYPE_MOTION,
        mode,
        0x01,  # delta
        0x00, 0x00, 0x00,  # padding / reserved
        0x02,
        0x01,
    ])

   
    """
    try:
        data = await client.read_gatt_char(SENSOR_VALUE_UUID)
        if not data:
            return None

        raw = unpack("<B", data[-1:])[0]
        distance_cm = float(raw)
        return distance_cm
    except Exception as e:
        print("Error reading distance:", e)
        return None


async def main():
    print(f"Connecting to WeDo hub at {WEDO_MAC} ...")
    client = BleakClient(WEDO_MAC)

    try:
        await client.connect()
        if not client.is_connected:
            print("Could not connect.")
            return

        print("Connected.")

        try:
            batt_bytes = await client.read_gatt_char(BATTERY_UUID)
            print("Battery level:", batt_bytes[0], "%")
        except Exception as e:
            print("Could not read battery:", e)

        await configure_distance_sensor(client, port=2)

        print("Starting distance loop (Ctrl+C to stop)...\n")

        while True:
            dist = await read_distance_cm(client)
            if dist is not None:
                print(f"Measured distance: {dist:.1f} cm")

                if dist < THRESHOLD_CM:
                    print("Obstacle detected!")
                else:
                    print("No obstacle.")
            else:
                print("No distance value (None).")

            await asyncio.sleep(0.2)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print("Connection error:", e)
    finally:
        try:
            if client.is_connected:
                await client.disconnect()
        except Exception:
            pass
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
