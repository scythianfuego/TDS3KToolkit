from process import TekFileProcessor

from bootheader import parse_boot_header, print_boot_header, calc_section_crc, parse_section, print_section
from console import error, warning, success, notice, checksum_message
from checksum import checksum

# usage 3.41.zip -> 3.41.unpacked.tar
# read fw1 from zip tds3000_3.41_063354011_tek.zip
# -> disk1/fwdisk1.dat
# -> disk2/fwdisk2.dat
# allocat zero buffer, will be expanded as needed
# copy

rom = "roms/tekrom315.bin"

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

p.read(file=rom)

for name in files:
    p.allocate(size=0, name=name)

p.append(dest="header.bin", src=rom, start="0x0", end="0x100")
p.append(dest="easteregg.png", src=rom, start="0x26EB60", end="0x280000")
p.append(dest="filesystem.bin", src=rom, start="0x280000", end="0x3E0000")
p.append(dest="devicedata.bin", src=rom, start="0x3E0000", end="0x400000")

romdata = p.get(rom)
header = parse_boot_header(romdata)
print_boot_header(header)

# rom header
crc_boot = calc_section_crc(header["boot"], romdata)
crc_firmware = calc_section_crc(header["firmware"], romdata)
crc_decompressor = calc_section_crc(header["decompressor"], romdata)
crc_recovery = calc_section_crc(header["recovery"], romdata)

# actual firmware and recovery headers
sw_section = parse_section(romdata, header["firmware"]["at"])
rec_section = parse_section(romdata, header["recovery"]["at"])
crc_fw = calc_section_crc(sw_section, romdata)
crc_rec = calc_section_crc(rec_section, romdata)

print_section(f"recovery at 0x{header["recovery"]["at"]:X}", rec_section)
print_section(f"firmware at 0x{header["firmware"]["at"]:X}", sw_section)

checksum_message("Boot checksum", crc_boot, header["boot"]["checksum"], fail=1)
checksum_message("Firmware checksum", crc_fw, sw_section["checksum"], fail=1)
checksum_message("Recovery checksum", crc_rec, rec_section["checksum"], fail=1)
checksum_message("Decompressor checksum", crc_decompressor, header["decompressor"]["checksum"], fail=1)

p.append(dest="firmware.z", src=rom, start=sw_section["start"], end=sw_section["end"])
p.unlzw(src="firmware.z", dest="firmware.bin")
p.append(dest="decompressor.bin", src=rom, start=header["decompressor"]["start"], end=header["decompressor"]["end"])
p.append(dest="bootloader.bin", src=rom, start=header["boot"]["start"], end=header["boot"]["end"])
p.append(dest="recovery.z", src=rom, start=rec_section["start"], end=rec_section["end"])
p.unlzw(src="recovery.z", dest="recovery.bin")

for name in files:
    p.print(name=name)


p.tar_add(output="rom.tar", names=files)
p.tar_write(output="rom.tar")

