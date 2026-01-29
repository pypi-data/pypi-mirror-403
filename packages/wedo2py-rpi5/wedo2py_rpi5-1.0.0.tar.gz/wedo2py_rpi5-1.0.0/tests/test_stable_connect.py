#!/usr/bin/env python3
import asyncio
from bleak import BleakClient, BleakScanner

HANDLE_BATTERY = 0x48  # battery characteristic handle

async def find_wedo():
    print("?? Scanning for WeDo hub... (����� �� hub)")
    devices = await BleakScanner.discover(timeout=5.0)

    for d in devices:
        print(f"Found: {d.name} [{d.address}]")
        if d.name and ("LPF2" in d.name or "WeDo" in d.name or "smarthub_eveanast" in d.name):
            print(f"? Using hub: {d.name} [{d.address}]")
            return d.address
    return None

async def main():
    address = await find_wedo()
    if not address:
        print("? WeDo hub not found. Try again.")
        return

    client = BleakClient(address)

    try:
        print("?? Connecting...")
        await client.connect()
        if not await client.is_connected():
            print("? Could not stay connected.")
            return

        print("? Connected. Starting loop (Ctrl+C ��� �����)...\n")

        await client.get_services()

        while True:
            if not await client.is_connected():
                print("? Disconnected from hub!")
                break

            try:
                data = await client.read_gatt_char(HANDLE_BATTERY)
                battery = data[0]
                print(f"?? Battery: {battery}%")
            except Exception as e:
                print(f"? Error reading battery: {e}")
                break

            await asyncio.sleep(2.0)

    except Exception as e:
        print(f"? Connection error: {e}")
    finally:
        if await client.is_connected():
            await client.disconnect()
        print("?? Finished.")

if __name__ == "__main__":
    asyncio.run(main())
