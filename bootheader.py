import struct
from checksum import checksum

SECTIONS = {
    "boot": 0x20,
    "firmware": 0x30,
    "decompressor": 0x40,
    "recovery": 0x50,
}
FIELDS = ["address", "size", "checksum", "compressed"]

def parse_boot_header(data):
    return {
        section: {
            field: struct.unpack_from(">I", data, offset + i * 4)[0]
            for i, field in enumerate(FIELDS)
        }
        for section, offset in SECTIONS.items()
    }


def parse_section(data, offset):
    return {
        field: struct.unpack_from(">I", data, offset + i * 4)[0]
        for i, field in enumerate(FIELDS)
    }

def boot_header_to_bytes(header):
    data = bytearray(0x60)
    for section, offset in SECTIONS.items():
        struct.pack_into(">IIII", data, offset, *[header[section][field] for field in FIELDS])
    return bytes(data)

def print_boot_header(header):
    print(f"{'Section':<14}{'Address':<12}{'Size':<12}{'Checksum':<12}{'Compressed':<12}")
    print("-" * 60)
    for section, values in header.items():
        print(f"{section:<14}{values['address']:<12X}{values['size']:<12}{values['checksum']:<12X}{values['compressed']:<12}")

def verify_section_crc(header, section, data):
    # if section not in header:
    #     raise ValueError("Invalid section name")
    base = 0xFFC00000
    start = header[section]["address"] - base
    size = header[section]["size"]
    chunk = data[start:start + size]
    return checksum(chunk)
