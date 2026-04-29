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




def calculate_checksum(target):
    data = target[:-1]      # all bytes except the last (the checksum)
    xor = 0
    for b in data:
        xor ^= b
    return xor


def find_checksum_range(target):
    actual = target[-1]
    data = target[:-1]
    print(f"\nTarget: {target.hex()}, Expected checksum: {hex(actual)}")
    
    for start in range(len(data)):
        for end in range(start+1, len(data)+1):
            xor = 0
            for b in data[start:end]:
                xor ^= b
            if xor == actual:
                print(f"  MATCH: XOR data[{start}:{end}] = {hex(xor)}")

def build_command(payload_without_checksum: bytes) -> bytes:
    xor = 0
    for b in payload_without_checksum:
        xor ^= b
    return payload_without_checksum + bytes([xor])

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

async def replay_sequence(payloads):
    """Send multiple payloads in one connection"""
    async with BleakClient(BULB_MAC) as client:
        for payload in payloads:
            await client.write_gatt_char(CHAR_UUID, payload)
            await asyncio.sleep(0.5)



# Segment bitmasks
SEG = {
    1:  (0x00, 0x40),
    2:  (0x00, 0x20),
    3:  (0x00, 0x10),
    4:  (0x00, 0x08),
    5:  (0x00, 0x04),
    6:  (0x00, 0x02),
    7:  (0x00, 0x01),
    8:  (0x40, 0x00),
    9:  (0x20, 0x00),
    10: (0x10, 0x00),
    11: (0x08, 0x00),
    12: (0x04, 0x00),
    13: (0x02, 0x00),
    14: (0x01, 0x00),
}

ALL_SEGMENTS = (0xFF, 0x7F)

def segments_mask(*seg_numbers):
    """Build (byte12, byte13) mask for given segment numbers."""
    b12, b13 = 0, 0
    for n in seg_numbers:
        m12, m13 = SEG[n]
        b12 |= m12
        b13 |= m13
    return b12, b13

def set_color(r, g, b, seg_numbers=None):
    """
    Set color on specific segments (default: all).
    Usage: set_color(255, 0, 0)               # all red
           set_color(0, 255, 0, [1,2,3])      # first 3 green
           set_color(0, 0, 255, range(8, 15)) # last 7 blue
    """
    b12, b13 = ALL_SEGMENTS if seg_numbers is None else segments_mask(*seg_numbers)
    payload = bytearray(19)
    payload[0:4] = bytes.fromhex("33051501")
    payload[4] = r
    payload[5] = g
    payload[6] = b
    payload[12] = b12
    payload[13] = b13
    return build_command(payload)

"""
# Examples
asyncio.run(replay(set_color(255, 0, 0)))                      # all red
asyncio.run(replay(set_color(0, 255, 0, [1,2,3])))             # segs 1-3 green
asyncio.run(replay(set_color(0, 0, 255, range(8, 15))))        # segs 8-14 blue
asyncio.run(replay(set_color(255, 0, 255, [1,3,5,7,9,11,13]))) # alternating purple
"""

    
while True:
    color = input("Enter color (yellow, green, blue, red, purple, strobe_low, strobe_high, strobe_weird, epilepsy, segmented_blue_red, custom) or 'exit' to quit: ").strip().lower()
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
    elif color == 'strobe_weird':
        asyncio.run(replay(Strobe_weird))
    elif color == 'epilepsy':
        asyncio.run(replay(Epilepsy))
    elif color == 'segmented_blue_red':
        asyncio.run(replay(Segmented_blue_red))
    elif color == 'custom':
        try:
            rgb_input = input("Enter RGB values (e.g. 255,0,0 for red): ")
            r, g, b = map(int, rgb_input.split(','))
            if not all(0 <= val <= 255 for val in (r, g, b)):
                raise ValueError("RGB values must be between 0 and 255.")

            seg_input = input("Enter segments (e.g. 1,2,3 or press Enter for all): ").strip()
            if seg_input:
                seg_numbers = list(map(int, seg_input.split(',')))
                if not all(1 <= s <= 14 for s in seg_numbers):
                    raise ValueError("Segment numbers must be between 1 and 14.")
            else:
                seg_numbers = None  # all segments

            command = set_color(r, g, b, seg_numbers)
            print(f"Payload length: {len(command)}, hex: {command.hex()}")
            asyncio.run(replay(command))

        except (ValueError, IndexError) as e:
                print(f"Invalid input: {e}")
    else:
        print("Invalid color. Please enter yellow, green, blue, red, purple, strobe_low, strobe_high, strobe_weird, epilepsy, segmented_blue_red, or custom.")
