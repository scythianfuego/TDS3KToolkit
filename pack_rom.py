from process import TekFileProcessor, known_locales, align
from bootheader import pack_section, parse_boot_header, print_boot_header, calc_section_crc, parse_section, print_section, boot_header_to_bytes
from console import error, warning, success, notice, checksum_message
from checksum import checksum
import struct

# Input files expected in tar archive
files = [
    "header.bin",
    "bootloader.bin",
    "decompressor.bin",
    "recovery.z",
    "recovery.bin",
    "firmware.bin",
    "firmware.z",
    "easteregg.png",
    "filesystem.bin",
    "devicedata.bin"
] + known_locales(".z")

p = TekFileProcessor()

# Read input tar
for name in files:
    p.tar_read(path=name, file="rom.tar")

# Create new ROM file
p.allocate(size=0x400000, name="rom.bin", init=0xff)

# Read and parse original header
romdata = p.get("rom.bin")
header = parse_boot_header(romdata)
print_boot_header(header)

# Write each section back to ROM
p.replace(dest="rom.bin", src="easteregg.png", at=0x26EB60)
p.replace(dest="rom.bin", src="filesystem.bin", at=0x280000)
p.replace(dest="rom.bin", src="devicedata.bin", at=0x3E0000)

# Write firmware sections
base = 0xFFC00000
decompressor_at = align(0x4000 + 0x10 + p.size(name="recovery.z"))
pe = struct.pack(">8I",
    0x4,
    0xFFFEBBDC, 0xFFFEEA4C, 0xFFFEA074,
    0xFFFE0040, 0xFFFF4420, 0xFFFF92E4, 0xFFE6EB60
)

# pad end of firmware to 4 bytes with zeroes
offset = align(0x40010 + p.size(name="firmware.z")) - 4
p.replace(dest="rom.bin", data=struct.pack(">I", 0), at=offset)

# write sections
p.replace(dest="rom.bin", src="bootloader.bin", at=0x100)
p.replace(dest="rom.bin", src="firmware.z", at=0x40000 + 0x10)
p.replace(dest="rom.bin", src="recovery.z", at=0x4000 + 0x10)
p.replace(dest="rom.bin", src="decompressor.bin", at=decompressor_at)

# update headers
boot = { "address": base + 0x100, "size": p.size(name="bootloader.bin"), "checksum": p.checksum(name="bootloader.bin"), "compressed": 0 }
recovery = { "address": base + 0x4000, "size": p.size(name="recovery.z"), "checksum": p.checksum(name="recovery.z"), "compressed": 1 }
firmware = { "address": base + 0x40000, "size": p.size(name="firmware.z"), "checksum": p.checksum(name="firmware.z"), "compressed": 1 }
decompressor = { "address": base + decompressor_at, "size": p.size(name="decompressor.bin"), "checksum": p.checksum(name="decompressor.bin"), "compressed": 0 }

# Handle locale files
offset = align(0x40010 + p.size(name="firmware.z"))
for localename in known_locales(".z"):
    size = p.size(name=localename) + 4
    p.replace(dest="rom.bin", data=struct.pack(">I", size), at=offset)
    p.replace(dest="rom.bin", src=localename, at=offset + 4)
    offset = align(offset + size)

print_section("Recovery", recovery)

# top headers
p.replace(dest="rom.bin", data=pe, at=0x0)
p.replace(dest="rom.bin", data=pack_section(boot), at=0x20)
p.replace(dest="rom.bin", data=pack_section(decompressor), at=0x40)
p.replace(dest="rom.bin", data=pack_section(firmware), at=0x30)
p.replace(dest="rom.bin", data=pack_section(recovery), at=0x50)
# in-place headers
p.replace(dest="rom.bin", data=pack_section(recovery), at=0x4000)
p.replace(dest="rom.bin", data=pack_section(firmware), at=0x40000)

p.write(name="rom.bin")
success("ROM packed successfully")
