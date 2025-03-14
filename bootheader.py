import struct
from checksum import checksum

SECTIONS = {
    "boot": 0x20,
    "firmware": 0x30,
    "decompressor": 0x40,
    "recovery": 0x50,
}
FIELDS = ["address", "size", "checksum", "compressed"]


def parse_section(data, offset):
    section = {
        field: struct.unpack_from(">I", data, offset + i * 4)[0]
        for i, field in enumerate(FIELDS)
    }
    at = section["address"] - 0xFFC00000
    start = at
    start += 0x10 if section["compressed"] else 0
    section["at"] = at # header start
    section["start"] = start # data start
    section["end"] = section["start"] + section["size"]
    return section

def parse_boot_header(data):
    header = {
        section: parse_section(data, offset)
        for section, offset in SECTIONS.items()
    }
    return header


def boot_header_to_bytes(header):
    data = bytearray(0x60)
    for section, offset in SECTIONS.items():
        struct.pack_into(">IIII", data, offset, *[header[section][field] for field in FIELDS])
    return bytes(data)

def print_section(section, values):
    print(f"{section:<22}{values['address']:<12X}{values['size']:<12}{values['checksum']:<12X}{values['compressed']:<12}")

def print_boot_header(header):
    print(f"{'Section':<22}{'Address':<12}{'Size':<12}{'Checksum':<12}{'Compressed':<12}")
    print("-" * 60)
    for section, values in header.items():
        print_section(section, values)

def calc_section_crc(section, data):
    start = section["start"]
    end = section["end"]
    chunk = data[start:end]
    return checksum(chunk)
