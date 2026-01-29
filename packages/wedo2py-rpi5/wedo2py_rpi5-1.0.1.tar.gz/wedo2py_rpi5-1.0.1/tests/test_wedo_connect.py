#!/usr/bin/env python3
import asyncio
from bleak import BleakClient, BleakScanner

HANDLE_BATTERY = 0x48  # characteristic handle for battery level

async def main():
    print("?? Scanning for WeDo hub... (turn it on!)")
    devices = await BleakScanner.discover(timeout=5.0)

    hub = None
    for d in devices:
        if d.name and ("LPF2" in d.name or "WeDo" in d.name or "smarthub_eveanast" in d.name):
            hub = d
            break

    if not hub:
        print("? Hub not found. Make sure it is powered on.")
        return

    print(f"?? Found WeDo hub: {hub.name} [{hub.address}]")
    async with BleakClient(hub.address) as client:
        print("?? Connecting...")
        await client.get_services()

        # Read battery
        battery_bytes = await client.read_gatt_char(HANDLE_BATTERY)
        battery = battery_bytes[0]
        print(f"?? Battery level: {battery}%")

        print("? Test completed OK")

asyncio.run(main())
