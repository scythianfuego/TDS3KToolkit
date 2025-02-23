from process import TekFileProcessor

# usage 3.41.zip -> 3.41.unpacked.tar
# read fw1 from zip tds3000_3.41_063354011_tek.zip
# -> disk1/fwdisk1.dat
# -> disk2/fwdisk2.dat
# allocat zero buffer, will be expanded as needed
# copy

rom = "roms/tekrom341.bin"

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

p.allocate(size=0, name="header.bin")
p.allocate(size=0, name="bootloader.bin")
p.allocate(size=0, name="recovery.bin")
p.allocate(size=0, name="compressor.bin")
p.allocate(size=0, name="firmware.bin")
p.allocate(size=0, name="easteregg.png")
p.allocate(size=0, name="filesystem.bin")
p.allocate(size=0, name="devicedata.bin")

p.append(dest="header.bin", src=rom, start="0x0", end="0x100")
p.append(dest="easteregg.png", src=rom, start="0x26EB60", end="0x280000")
p.append(dest="filesystem.bin", src=rom, start="0x280000", end="0x3E0000")
p.append(dest="devicedata.bin", src=rom, start="0x3E0000", end="0x400000")

p.tar_add(output="rom.tar", names=files)
p.tar_write(output="rom.tar")

