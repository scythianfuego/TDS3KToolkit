import struct

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

def boot_header_to_bytes(header):
    data = bytearray(0x60)
    for section, offset in SECTIONS.items():
        struct.pack_into(">IIII", data, offset, *[header[section][field] for field in FIELDS])
    return bytes(data)

def print_boot_header(header):
    print(f"{'Section':<12}{'Address':<12}{'Size':<12}{'Checksum':<12}{'Is Compressed':<12}")
    print("-" * 60)
    for section, values in header.items():
        print(f"{section:<12}{values['address']:<12}{values['size']:<12}{values['checksum']:<12}{values['compressed']:<12}")

def verify_section_crc(header, section, data, crc_function):
    if section not in header:
        raise ValueError("Invalid section name")
    start = header[section]["address"]
    size = header[section]["size"]
    chunk = data[start:start + size]
    return crc_function(chunk)
