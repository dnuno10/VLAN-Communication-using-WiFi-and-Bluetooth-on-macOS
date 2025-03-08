import asyncio
import base64
import os
from bleak import BleakClient, BleakScanner, BleakError

SERVER_ADDRESS = "BBBEE165-C972-C885-0014-2C71CB79A3EB"

SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHAR_UUID    = "12345678-1234-5678-1234-56789abcdef1"

CHUNK_SIZE   = 300
DELAY_BETWEEN_CHUNKS = 0.05 

async def ensure_connected(client):
    if not client.is_connected:
        print("Disconnected; attempting to reconnect...")
        try:
            await client.connect()
            print("Reconnected!")
        except BleakError as e:
            print(f"Reconnect failed: {e}")
            raise

async def send_command(client, command: str) -> str:
    await ensure_connected(client)
    try:
        await client.write_gatt_char(CHAR_UUID, command.encode("utf-8"))
        response = await client.read_gatt_char(CHAR_UUID)
        return response.decode("utf-8", errors="replace")
    except BleakError as e:
        if "disconnected" in str(e).lower():
            print("Disconnected mid-command. Trying one reconnect...")
            await ensure_connected(client)
            await client.write_gatt_char(CHAR_UUID, command.encode("utf-8"))
            response = await client.read_gatt_char(CHAR_UUID)
            return response.decode("utf-8", errors="replace")
        else:
            raise

async def main():
    print("Scanning for BLE devices...")
    _ = await BleakScanner.discover()
    print(f"Connecting to BLE Server at {SERVER_ADDRESS} ...")

    async with BleakClient(SERVER_ADDRESS) as client:
        print("Connected to BLE Server")

        while True:
            print("\nOptions:")
            print("1. List files on server")
            print("2. Download a file from server")
            print("3. Upload a file to server")
            print("4. Exit")

            choice = input("Enter choice: ").strip()

            if choice == "1":
                resp = await send_command(client, "LIST")
                print("\nServer Response:\n", resp)

            elif choice == "2":
                filename = input("Enter filename to download> ").strip()
                await chunked_download(client, filename)

            elif choice == "3":
                local_path = input("Enter local file path to upload> ").strip()
                await chunked_upload(client, local_path)

            elif choice == "4" or choice.upper() == "EXIT":
                print("Exiting client...")
                break

            else:
                resp = await send_command(client, choice)
                print("\nServer Response:\n", resp)

async def chunked_download(client, filename: str):
    offset = 0
    all_chunks = []

    while True:
        cmd = f"DOWNLOAD {filename}:{offset}"
        response = await send_command(client, cmd)

        if not response.startswith("CHUNK:"):
            print("\nServer Response:\n", response)
            return

        parts = response.split(":", 4)
        if len(parts) < 5:
            print("Unexpected CHUNK format:", response)
            return

        chunk_filename = parts[1]
        range_str      = parts[2]
        base64_chunk   = parts[3]
        status         = parts[4]

        try:
            start_end = range_str.split("-")
            next_offset = int(start_end[1])
        except:
            print("Could not parse range:", range_str)
            return

        if base64_chunk:
            all_chunks.append(base64_chunk)

        if status == "DONE":
            break
        elif status == "CONT":
            offset = next_offset
        else:
            print("Unknown chunk status:", status)
            return

    full_base64 = "".join(all_chunks)
    try:
        file_bytes = base64.b64decode(full_base64)
        out_name = f"downloaded_{filename}"
        with open(out_name, "wb") as f:
            f.write(file_bytes)
        print(f"Downloaded file saved as '{out_name}'")
    except Exception as e:
        print(f"Error decoding/saving file: {e}")

async def chunked_upload(client, local_path: str):
    if not os.path.isfile(local_path):
        print(f"Local file not found: {local_path}")
        return

    filename = os.path.basename(local_path)
    try:
        with open(local_path, "rb") as f:
            raw_data = f.read()
        b64 = base64.b64encode(raw_data).decode("utf-8")
    except Exception as e:
        print(f"Error reading local file: {e}")
        return

    offset = 0
    total_len = len(b64)

    while offset < total_len:
        end = min(offset + CHUNK_SIZE, total_len)
        chunk = b64[offset:end]
        status = "CONT"
        if end >= total_len:
            status = "DONE"

        cmd = f"UPLOADCHUNK:{filename}:{offset}-{end}:{chunk}:{status}"
        resp = await send_command(client, cmd)
        print("\nServer Response:\n", resp)

        await asyncio.sleep(DELAY_BETWEEN_CHUNKS)

        if resp.upper().startswith("ERROR"):
            return
        if status == "DONE":
            return

        offset = end

if __name__ == "__main__":
    asyncio.run(main())
