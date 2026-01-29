#!/usr/bin/env python3
import asyncio
from struct import pack
from bleak import BleakClient

WEDO_MAC = "04:EE:03:16:ED:1D"

OUTPUT_COMMAND_UUID = "00001565-1212-efde-1523-785feabcd123"
BATTERY_UUID        = "00002a19-0000-1000-8000-00805f9b34fb"

# 1 = Port A, 2 = Port B
PORT_A = 1
PORT_B = 2


async def motor_set_power(client: BleakClient, port: int, power: int):
    """
    Set motor power on given port (1=A, 2=B).
    power: -100 .. 100  (signed int8)
    This matches the format used in your WeDo2Python_App:
      pack("<bbbb", port, 0x01, 0x01, direction * power)
    """
    if power > 100:
        power = 100
    if power < -100:
        power = -100

    # 4-byte command: [port, 0x01, 0x01, signed_power]
    cmd = pack("<bbbb", port, 0x01, 0x01, power)
    await client.write_gatt_char(OUTPUT_COMMAND_UUID, cmd)
    print(f"Motor command sent: port={port}, power={power}")


async def main():
    client = BleakClient(WEDO_MAC)
    print(f"Connecting to {WEDO_MAC} ...")
    await client.connect()
    print("Connected.")

    try:
        # Optional: battery check
        try:
            batt = await client.read_gatt_char(BATTERY_UUID)
            print("Battery level:", batt[0], "%")
        except Exception as e:
            print("Battery read error:", e)

        motor_port = PORT_A  

        print("\n> Forward (50%) for 2 seconds")
        await motor_set_power(client, motor_port, 50)
        await asyncio.sleep(2)

        print("\n> Stop")
        await motor_set_power(client, motor_port, 0)
        await asyncio.sleep(1)

        print("\n> Backward (-50%) for 2 seconds")
        await motor_set_power(client, motor_port, -50)
        await asyncio.sleep(2)

        print("\n> Stop")
        await motor_set_power(client, motor_port, 0)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        if client.is_connected:
            print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

