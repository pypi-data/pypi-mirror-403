#!/usr/bin/env python3
import asyncio
from bleak import BleakClient

# MAC address of your WeDo hub
WEDO_MAC = "04:EE:03:16:ED:1D"

# UUIDs from your GATT dump
INPUT_COMMAND_UUID = "00001563-1212-efde-1523-785feabcd123"  # configure sensor
SENSOR_VALUE_UUID  = "00001560-1212-efde-1523-785feabcd123"  # sensor values
BATTERY_UUID       = "00002a19-0000-1000-8000-00805f9b34fb"  # battery

# Type and constants for tilt sensor
TYPE_TILT = 0x22
COMMAND_ID_INPUT_FORMAT = 0x01
COMMAND_TYPE_WRITE      = 0x02


def decode_tilt(raw_bytes):
    """
    Decode BLE tilt sensor bytes into a human-readable label.
    Patterns from your measurements:

      HORIZONTAL: [02 01 00 00 00 00] -> b4=00, b5=00
      RIGHT     : [02 01 00 00 A0 40] -> b4=A0, b5=40
      LEFT      : [02 01 00 00 E0 40] -> b4=E0, b5=40
      UP        : [02 01 00 00 40 40] -> b4=40, b5=40
      DOWN      : [02 01 00 00 10 41] -> b4=10, b5=41
    """
    if raw_bytes is None or len(raw_bytes) < 6:
        return "INVALID"

    b4 = raw_bytes[4]  # 5th byte
    b5 = raw_bytes[5]  # 6th byte

    if b4 == 0x00 and b5 == 0x00:
        return "HORIZONTAL"
    if b4 == 0xA0 and b5 == 0x40:
        return "RIGHT"
    if b4 == 0xE0 and b5 == 0x40:
        return "LEFT"
    if b4 == 0x40 and b5 == 0x40:
        return "UP"
    if b4 == 0x10 and b5 == 0x41:
        return "DOWN"

    return f"UNKNOWN(b4={b4:02X}, b5={b5:02X})"


async def configure_tilt_sensor_port_a(client):
    """
    Configure tilt sensor on Port A (channel=1) in tilt mode.
    Command (11 bytes):
      01 02 CH 22 01 01 00 00 00 02 01
    where:
      CH = 1 (Port A)
      22 = TYPE_TILT
      01 = tilt mode
    """
    channel = 1
    mode = 0x01  # tilt mode

    cmd = bytes([
        COMMAND_ID_INPUT_FORMAT,
        COMMAND_TYPE_WRITE,
        channel,
        TYPE_TILT,
        mode,
        0x01,
        0x00, 0x00, 0x00,
        0x02,
        0x01,
    ])

    await client.write_gatt_char(INPUT_COMMAND_UUID, cmd)
    print("Tilt sensor configured on Port A.")


async def main():
    client = BleakClient(WEDO_MAC)
    print(f"Connecting to {WEDO_MAC} ...")
    await client.connect()
    print("Connected.")

    try:
        # Optional: battery
        try:
            batt = await client.read_gatt_char(BATTERY_UUID)
            print("Battery:", batt[0], "%")
        except Exception as e:
            print("Battery read error:", e)

        await configure_tilt_sensor_port_a(client)

        print("Starting tilt loop (Ctrl+C to stop)...")
        last_label = None

        while True:
            raw = await client.read_gatt_char(SENSOR_VALUE_UUID)
            hex_bytes = " ".join(f"{b:02X}" for b in raw)
            print(f"RAW: [{hex_bytes}]")

            label = decode_tilt(raw)
            if label != last_label:
                print("Tilt:", label)
                last_label = label

            await asyncio.sleep(0.3)

    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        if client.is_connected:
            await client.disconnect()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
