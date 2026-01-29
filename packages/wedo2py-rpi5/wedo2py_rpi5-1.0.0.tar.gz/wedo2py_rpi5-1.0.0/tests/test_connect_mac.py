#!/usr/bin/env python3
import asyncio
from bleak import BleakClient

WEDO_MAC = "04:EE:03:16:ED:1D"

async def main():
    print(f"Trying to connect to {WEDO_MAC} ...")
    client = BleakClient(WEDO_MAC)

    try:
        await client.connect()
        print("Connected:", client.is_connected)

        if not client.is_connected:
            print("Could not stay connected.")
            return

        print("Staying connected for 5 seconds...")
        await asyncio.sleep(5.0)

    except Exception as e:
        print("Connection error:", e)
    finally:
        if client.is_connected:
            print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
