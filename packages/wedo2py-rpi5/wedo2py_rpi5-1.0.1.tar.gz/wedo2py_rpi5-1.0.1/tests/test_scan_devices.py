#!/usr/bin/env python3
import asyncio
from bleak import BleakScanner

async def main():
    print("?? Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=5.0)

    if not devices:
        print("? No devices found.")
        return

    print("\n?? Found devices:")
    for d in devices:
        print(f"- {d.name} [{d.address}]")

asyncio.run(main())
