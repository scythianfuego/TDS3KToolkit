from process import TekFileProcessor

from bootheader import parse_boot_header, print_boot_header, verify_section_crc, parse_section
from console import error, warning, success, notice, checksum_message

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
    "recovery.bin",
    "compressor.bin",
    "firmware.bin",
    "easteregg.png",
    "filesystem.bin",
    "devicedata.bin"
    ]


p = TekFileProcessor()

p.read(file=rom)


outputnames = ["header.bin", "bootloader.bin", "recovery.bin", "compressor.bin", "firmware.z", "firmware.bin", "easteregg.png", "filesystem.bin", "devicedata.bin" ]
for name in outputnames:
    p.allocate(size=0, name=name)

p.allocate(size=0, name="header.bin")
p.allocate(size=0, name="bootloader.bin")
p.allocate(size=0, name="recovery.bin")
p.allocate(size=0, name="compressor.bin")
p.allocate(size=0, name="firmware.z")
p.allocate(size=0, name="firmware.bin")
p.allocate(size=0, name="easteregg.png")
p.allocate(size=0, name="filesystem.bin")
p.allocate(size=0, name="devicedata.bin")

p.append(dest="header.bin", src=rom, start="0x0", end="0x100")
p.append(dest="easteregg.png", src=rom, start="0x26EB60", end="0x280000")
p.append(dest="filesystem.bin", src=rom, start="0x280000", end="0x3E0000")
p.append(dest="devicedata.bin", src=rom, start="0x3E0000", end="0x400000")

romdata = p.get(rom)
header = parse_boot_header(romdata)
print_boot_header(header)

crc_boot = verify_section_crc(header, "boot", romdata)
crc_firmware = verify_section_crc(header, "firmware", romdata)
crc_decompressor = verify_section_crc(header, "decompressor", romdata)
crc_recovery = verify_section_crc(header, "recovery", romdata)

print(f"Boot checksum: {crc_boot:08X}")
print(f"Firmware checksum: {crc_firmware:08X}")
print(f"Decompressor checksum: {crc_decompressor:08X}")
print(f"Recovery checksum: {crc_recovery:08X}")

start = header["firmware"]["address"] - 0xFFC00000 + 0x10
end = start + header["firmware"]["size"]

p.append(dest="firmware.z", src=rom, start=start, end=end)
p.unlzw(src="firmware.z", dest="firmware.bin")

sw_section = parse_section(romdata, 0x40000)
start = sw_section["address"] - 0xFFC00000 + 0x10
end = start + sw_section["size"]
print(f"Software section: {start:08X} - {end:08X}")
crc_test = calculate_checksum(romdata[start:end])
print(f"Firmware checksum: {crc_test:08X}")
p.print_value(text="Expected checksum", name=rom, at="0x40008")

# p.tar_add(output="rom.tar", names=files)
# p.tar_write(output="rom.tar")

