from process import TekFileProcessor
from bootheader import parse_boot_header, print_boot_header, calc_section_crc, parse_section, print_section, boot_header_to_bytes
from console import error, warning, success, notice, checksum_message
from checksum import checksum

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
]

p = TekFileProcessor()

# Read input tar
for name in files:
    p.tar_read(path=name, file="rom.tar")

# Create new ROM file from template
p.allocate(size=0x400000, name="rom.bin", init=0xff)
template_rom = "roms/tekrom315.bin"
p.read(file=template_rom)
p.append(dest="rom.bin", src=template_rom, start=0, end=0x400000)

# Read and parse original header
romdata = p.get("rom.bin")
header = parse_boot_header(romdata)
print_boot_header(header)

# Write each section back to ROM
p.replace(dest="rom.bin", src="easteregg.png", at=0x26EB60)
p.replace(dest="rom.bin", src="filesystem.bin", at=0x280000)
p.replace(dest="rom.bin", src="devicedata.bin", at=0x3E0000)

# Write firmware sections
p.replace(dest="rom.bin", src="bootloader.bin", at=header["boot"]["start"])
p.replace(dest="rom.bin", src="decompressor.bin", at=header["decompressor"]["start"])
p.replace(dest="rom.bin", src="firmware.z", at=header["firmware"]["start"])
p.replace(dest="rom.bin", src="recovery.z", at=header["recovery"]["start"])

# Verify all checksums
romdata = p.get("rom.bin")
crc_boot = calc_section_crc(header["boot"], romdata)
crc_firmware = calc_section_crc(header["firmware"], romdata)
crc_decompressor = calc_section_crc(header["decompressor"], romdata)
crc_recovery = calc_section_crc(header["recovery"], romdata)

sw_section = parse_section(romdata, header["firmware"]["at"])
rec_section = parse_section(romdata, header["recovery"]["at"])
crc_fw = calc_section_crc(sw_section, romdata)
crc_rec = calc_section_crc(rec_section, romdata)

checksum_message("Boot checksum", crc_boot, header["boot"]["checksum"])
checksum_message("Firmware checksum", crc_fw, sw_section["checksum"])
checksum_message("Recovery checksum", crc_rec, rec_section["checksum"])
checksum_message("Decompressor checksum", crc_decompressor, header["decompressor"]["checksum"])

p.write(name="rom.bin")
success("ROM packed successfully")
