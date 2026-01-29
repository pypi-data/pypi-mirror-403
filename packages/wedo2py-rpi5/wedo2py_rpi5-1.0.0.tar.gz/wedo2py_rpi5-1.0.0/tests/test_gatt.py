#!/usr/bin/env python3
import asyncio
from bleak import BleakClient

WEDO_MAC = "04:EE:03:16:ED:1D"

async def main():
    print(f"Connecting to {WEDO_MAC} ...")
    client = BleakClient(WEDO_MAC)

    try:
        await client.connect()
        if not client.is_connected:
            print("Could not connect")
            return
        print("Connected\n")

        services = client.services

        print("Listing Services + Characteristics:\n")
        for service in services:
            print(f"Service UUID: {service.uuid}")
            for char in service.characteristics:
                print(f"   Char UUID: {char.uuid}   | handle: {char.handle}   | props: {char.properties}")
            print()

    finally:
        try:
            if client.is_connected:
                await client.disconnect()
        except Exception:
            pass

    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
