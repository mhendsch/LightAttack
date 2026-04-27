import asyncio
from bleak import BleakClient

BULB_MAC = "E5:90:03:46:53:18"
CHAR_UUID = "00010203-0405-0607-0809-0a0b0c0d2b11"  # UUID from handshake
PAYLOAD = bytes.fromhex("33051501ff00000000000000ff7f00000000005d")           # Example payload (data) of packet
"""
Yellow: 33051501ffff000000000000ff7f0000000000a2
Green:  3305150100ff000000000000ff7f00000000005d
Blue:   330515010000ff0000000000ff7f00000000005d
Red:    33051501ff00000000000000ff7f00000000005d
"""
Yellow = bytes.fromhex(             "33051501ffff000000000000ff7f0000000000a2")
Green = bytes.fromhex(              "3305150100ff000000000000ff7f00000000005d")
Blue = bytes.fromhex(               "330515010000ff0000000000ff7f00000000005d")
Red = bytes.fromhex(                "33051501ff00000000000000ff7f00000000005d")
Purple = bytes.fromhex(             "33051501ff05d50000000000ff7f00000000008d")
Strobe_low = bytes.fromhex(         "3305130563000000000000000000000000000043")
Strobe_high = bytes.fromhex(        "3305130363000000000000000000000000000045")
Strobe_weird = bytes.fromhex(       "3305130463000000000000000000000000000042")
Epilepsy = bytes.fromhex(           "3305130332000000000000000000000000000014")
Segmented_blue_red = bytes.fromhex( "33050a200300000000000000000000000000001f") 



async def calculate_checksum(target):
    print(f"Calculating checksum for: {target.hex()}")
    # Try to calculate last byte of payload
    data = target[:-1]
    actual = target[-1]  # 0x5d = 93
    # Try XOR of slices for last byte
    for start in range(len(data)):
        xor = 0
        for b in data[start:]:
            xor ^= b
        if xor == actual:
            print(f"XOR data[{start}:] = {hex(xor)}")

async def main():
    await calculate_checksum(Yellow)
    await calculate_checksum(Green)
    await calculate_checksum(Blue)
    await calculate_checksum(Red)
    await calculate_checksum(Purple)
    await calculate_checksum(Strobe_low)
    await calculate_checksum(Strobe_high)
    await calculate_checksum(Strobe_weird)
    await calculate_checksum(Epilepsy)
    await calculate_checksum(Segmented_blue_red)


async def discover():
    async with BleakClient(BULB_MAC) as client:
        for service in client.services:
            print(f"Service: {service.uuid}")
            for char in service.characteristics:
                print(f"  Char: {char.uuid} | Properties: {char.properties}")


async def replay(payload):
    async with BleakClient(BULB_MAC) as client:
        await client.write_gatt_char(CHAR_UUID, payload)
        print("Packet sent!")

# asyncio.run(replay(bytes.fromhex("a3ff0304050608ff00000708090a0b0c0d0e00a7")))

asyncio.run(main())
while True:
    color = input("Enter color (yellow, green, blue, red, purple, strobe_low, strobe_high) or 'exit' to quit: ").strip().lower()
    if color == 'exit':
        break
    elif color == 'yellow':
        asyncio.run(replay(Yellow))
    elif color == 'green':
        asyncio.run(replay(Green))
    elif color == 'blue':
        asyncio.run(replay(Blue))
    elif color == 'red':
        asyncio.run(replay(Red))
    elif color == 'purple':
        asyncio.run(replay(Purple))
    elif color == 'strobe_low':
        asyncio.run(replay(Strobe_low))
    elif color == 'strobe_high':
        asyncio.run(replay(Strobe_high))
    else:
        print("Invalid color. Please enter yellow, green, blue, red, purple, strobe_low, or strobe_high.")
