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

# Verify against known sequences
test_cases = {
    "Green":        bytes.fromhex("3305150100ff000000000000ff7f00000000005d"),
    "Blue":         bytes.fromhex("330515010000ff0000000000ff7f00000000005d"),
    "Red":          bytes.fromhex("33051501ff00000000000000ff7f00000000005d"),
    "Purple":       bytes.fromhex("33051501ff05d50000000000ff7f00000000008d"),
    "Strobe_low":   bytes.fromhex("3305130563000000000000000000000000000043"),
    "Strobe_high":  bytes.fromhex("3305130363000000000000000000000000000045"),
}

for name, seq in test_cases.items():
    calc = calculate_checksum(seq)
    actual = seq[-1]
    status = "OK" if calc == actual else "FAIL"
    print(f"{status} {name}: calculated={hex(calc)}, actual={hex(actual)}")


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


#asyncio.run(replay(build_command(bytes.fromhex("33050a"))))
"""
Red_no_checksum = bytearray(bytes.fromhex("33051501ff00000000000000ff7f00000000005d")[:-1])
print(f"Red without checksum: {Red_no_checksum.hex()}, length: {len(Red_no_checksum)}")

# Now test each byte position in the "middle" region (bytes 7-18)
# by setting it to ff while zeroing the rest
segment_tests = {}
for pos in range(7, 19):
    payload = bytearray(Red_no_checksum)  # start from known-good
    payload[13] = 0x00  # zero out original ff
    payload[14] = 0x00  # zero out original 7f
    payload[pos] = 0xFF  # set test byte
    segment_tests[f"pos_{pos:02d}_=FF"] = bytes(payload)

# Also test the original ff7f positions with different values
for val in [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80]:
    payload = bytearray(Red_no_checksum)
    payload[13] = val
    payload[14] = 0x00
    segment_tests[f"byte13={val:02x}"] = bytes(payload)

    payload2 = bytearray(Red_no_checksum)
    payload2[13] = 0x00
    payload2[14] = val
    segment_tests[f"byte14={val:02x}"] = bytes(payload2)

for name, payload in segment_tests.items():
    print(f"\n--- {name} | len={len(payload)+1} | {build_command(payload).hex()} ---")
    asyncio.run(replay(build_command(payload)))
    input("Press Enter for next...")
"""
"""
Red_no_checksum = bytearray(bytes.fromhex("33051501ff00000000000000ff7f00000000005d")[:-1])

shift_tests = {}

# Shift ff7f to every possible position pair in the packet
for pos in range(4, 18):  # start after header bytes
    payload = bytearray(Red_no_checksum)
    # Zero out original ff7f
    payload[13] = 0x00
    payload[14] = 0x00
    # Place ff7f at new position
    payload[pos] = 0xFF
    if pos + 1 < 19:
        payload[pos + 1] = 0x7F
    shift_tests[f"ff7f_at_pos_{pos:02d}-{pos+1:02d}"] = bytes(payload)

# Also test ff7f with the byte8=ff finding — keep byte8=ff and shift ff7f
for pos in range(4, 18):
    payload = bytearray(Red_no_checksum)
    payload[13] = 0x00
    payload[14] = 0x00
    payload[8] = 0xFF   # known "all lights on" byte
    payload[pos] = 0xFF
    if pos + 1 < 19:
        payload[pos + 1] = 0x7F
    shift_tests[f"byte8ff+ff7f_at_{pos:02d}"] = bytes(payload)

for name, payload in shift_tests.items():
    cmd = build_command(payload)
    print(f"\n--- {name} ---")
    print(f"    {cmd.hex()}")
    asyncio.run(replay(cmd))
    input("Press Enter for next...")
"""
"""
Red_no_checksum = bytearray(bytes.fromhex("33051501ff00000000000000ff7f00000000005d")[:-1])

# Hypothesis: bytes 4-9 each control one segment's color (6 bytes = 6 segments?)
# Test by setting one byte to ff (red channel) at a time
seg_tests = {}

for pos in range(4, 10):
    payload = bytearray(19)
    payload[0] = 0x33
    payload[1] = 0x05
    payload[2] = 0x15
    payload[3] = 0x01
    payload[pos] = 0xFF      # set just this segment to red
    payload[13] = 0xFF       # keep ff7f in original position
    payload[14] = 0x7F
    seg_tests[f"only_pos_{pos:02d}_red"] = bytes(payload)

# Also test pairs — maybe each segment is 2 bytes (R+G or similar)
for pos in range(4, 10, 2):
    payload = bytearray(19)
    payload[0] = 0x33
    payload[1] = 0x05
    payload[2] = 0x15
    payload[3] = 0x01
    payload[pos] = 0xFF
    payload[pos+1] = 0x00    # R=255, G=0
    payload[13] = 0xFF
    payload[14] = 0x7F
    seg_tests[f"pair_pos_{pos:02d}_red"] = bytes(payload)

for name, payload in seg_tests.items():
    cmd = build_command(payload)
    print(f"\n--- {name} ---")
    print(f"    {cmd.hex()}")
    asyncio.run(replay(cmd))
    input("Press Enter for next...")
"""
"""
Red_no_checksum = bytearray(19)
Red_no_checksum[0:4] = bytes.fromhex("33051501")
Red_no_checksum[13] = 0xFF
Red_no_checksum[14] = 0x7F

split_tests = {}

# Test RGB for second group at bytes 8-10
colors = {"red": (0xFF,0,0), "green": (0,0xFF,0), "blue": (0,0,0xFF), "white": (0xFF,0xFF,0xFF)}

for c1name, c1 in colors.items():
    for c2name, c2 in colors.items():
        payload = bytearray(Red_no_checksum)
        payload[4], payload[5], payload[6] = c1   # first group RGB
        payload[8], payload[9], payload[10] = c2  # second group RGB
        split_tests[f"seg1={c1name}_seg2={c2name}"] = bytes(payload)

for name, payload in split_tests.items():
    cmd = build_command(payload)
    print(f"\n--- {name} ---")
    print(f"    {cmd.hex()}")
    asyncio.run(replay(cmd))
    input("Press Enter for next...")
"""
"""
base = bytearray(19)
base[0:4] = bytes.fromhex("33051501")
base[4] = 0xFF  # Red
base[13] = 0xFF
base[14] = 0x7F

mask_tests = {}

# Test each byte in positions 7-12 as a bitmask
for pos in range(7, 13):
    for val in [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0xFF]:
        payload = bytearray(base)
        payload[pos] = val
        mask_tests[f"pos{pos:02d}=0x{val:02x}"] = bytes(payload)

for name, payload in mask_tests.items():
    cmd = build_command(payload)
    print(f"\n--- {name} ---")
    print(f"    {cmd.hex()}")
    asyncio.run(replay(cmd))
    input("Press Enter for next...")
"""
"""
base = bytearray(19)
base[0:4] = bytes.fromhex("33051501")
base[13] = 0xFF
base[14] = 0x7F

two_group_tests = {}

color_pairs = [
    ("red_red",     (0xFF,0,0),    (0xFF,0,0)),
    ("red_green",   (0xFF,0,0),    (0,0xFF,0)),
    ("red_blue",    (0xFF,0,0),    (0,0,0xFF)),
    ("green_blue",  (0,0xFF,0),    (0,0,0xFF)),
    ("blue_red",    (0,0,0xFF),    (0xFF,0,0)),
    ("white_black", (0xFF,0xFF,0xFF), (0,0,0)),
    ("black_white", (0,0,0),       (0xFF,0xFF,0xFF)),
]

# Test second group at bytes 9, 10, 11
for name, c1, c2 in color_pairs:
    payload = bytearray(base)
    payload[4], payload[5], payload[6] = c1   # first group
    payload[9], payload[10], payload[11] = c2  # second group hypothesis
    two_group_tests[f"9-11_{name}"] = bytes(payload)

for name, payload in two_group_tests.items():
    cmd = build_command(payload)
    print(f"\n--- {name} ---")
    print(f"    {cmd.hex()}")
    asyncio.run(replay(cmd))
    input("Press Enter for next...")
"""
"""
base = bytearray(19)
base[0:4] = bytes.fromhex("33051501")
base[4] = 0xFF  # first half = red

second_half_tests = {}

# ff7f = ff green + 7f blue? or ff red + 7f green?
# Try pure values to figure out channel mapping
second_half_tests["ff_00"] = (0xFF, 0x00)  # should be one pure color
second_half_tests["00_ff"] = (0x00, 0xFF)  # different pure color  
second_half_tests["00_7f"] = (0x00, 0x7F)  # half of second channel
second_half_tests["7f_00"] = (0x7F, 0x00)  # half of first channel
second_half_tests["ff_ff"] = (0xFF, 0xFF)  # both maxed
second_half_tests["7f_7f"] = (0x7F, 0x7F)  # both half

for name, (b13, b14) in second_half_tests.items():
    payload = bytearray(base)
    payload[13] = b13
    payload[14] = b14
    cmd = build_command(payload)
    print(f"\n--- second_half={name} ---")
    print(f"    {cmd.hex()}")
    asyncio.run(replay(cmd))
    input("Press Enter for next...")
#asyncio.run(replay(build_command(bytes.fromhex("33051501ff00000101010000000000ff7f0000"))))
"""
"""
base = bytearray(19)
base[0:4] = bytes.fromhex("33051501")
base[4] = 0xFF  # red

mask_tests = {}

# Test byte 13 as segment enable bitmask
for val in [0x00, 0x01, 0x03, 0x07, 0x0f, 0x1f, 0x3f, 0x7f, 0xff]:
    payload = bytearray(base)
    payload[13] = val
    payload[14] = 0x00
    mask_tests[f"byte13=0x{val:02x}_byte14=0x00"] = bytes(payload)

# And byte 14 as segment enable bitmask    
for val in [0x00, 0x01, 0x03, 0x07, 0x0f, 0x1f, 0x3f, 0x7f, 0xff]:
    payload = bytearray(base)
    payload[13] = 0x00
    payload[14] = val
    mask_tests[f"byte13=0x00_byte14=0x{val:02x}"] = bytes(payload)

# Known distinct states to confirm the strip is responding
RESET_RED  = bytes.fromhex("33051501ff00000000000000ff7f00000000005d")  # all red
RESET_BLUE = bytes.fromhex("330515010000ff0000000000ff7f00000000005d")  # all blue

for name, payload in mask_tests.items():
    cmd = build_command(payload)
    print(f"\n--- {name} ---")
    print(f"    {cmd.hex()}")
    # Alternate between red and blue reset so change is always visible
    asyncio.run(replay_sequence([RESET_BLUE, cmd]))
    input("Press Enter for next...")
"""
""" Test first half of strip
RESET_BLUE = bytes.fromhex("330515010000ff0000000000ff7f00000000005d")

confirm_tests = {
    "seg7_only":    0x01,
    "seg6_only":    0x02,
    "seg5_only":    0x04,
    "seg4_only":    0x08,
    "seg3_only":    0x10,
    "seg2_only":    0x20,
    "seg1_only":    0x40,  # hypothesis
    "all_7":        0x7F,
    "all_confirmed":0xFF,  # we know this is invalid, just reconfirm
}

for name, mask in confirm_tests.items():
    payload = bytearray(19)
    payload[0:4] = bytes.fromhex("33051501")
    payload[4] = 0xFF   # red
    payload[13] = mask
    cmd = build_command(payload)
    print(f"\n--- {name} (mask=0x{mask:02x}) ---")
    print(f"    {cmd.hex()}")
    asyncio.run(replay_sequence([RESET_BLUE, cmd]))
    input("Press Enter for next...")
"""
"""
# Test second half of strip
RESET_BLUE = bytes.fromhex("330515010000ff0000000000ff7f00000000005d")

seg_tests = {}
for bit in [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x7F, 0xFF]:
    payload = bytearray(19)
    payload[0:4] = bytes.fromhex("33051501")
    payload[4] = 0xFF           # red
    payload[13] = 0x7F          # keep segments 1-7 on for reference
    payload[12] = bit           # test byte 12 for segments 8-14
    seg_tests[f"byte12=0x{bit:02x}"] = bytes(payload)

for name, payload in seg_tests.items():
    cmd = build_command(payload)
    print(f"\n--- {name} ---")
    print(f"    {cmd.hex()}")
    asyncio.run(replay_sequence([RESET_BLUE, cmd]))
    input("Press Enter for next...")
"""
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
