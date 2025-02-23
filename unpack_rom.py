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


processor = TekFileProcessor()

# processor.do("read", file=rom)

config = [
    { "do": "read", "file": rom},
    { "do": "allocate", "size": 0, "name": "header.bin"},
    { "do": "allocate", "size": 0, "name": "bootloader.bin"},
    { "do": "allocate", "size": 0, "name": "recovery.bin"},
    { "do": "allocate", "size": 0, "name": "compressor.bin"},
    { "do": "allocate", "size": 0, "name": "firmware.bin"},
    { "do": "allocate", "size": 0, "name": "easteregg.png"},
    { "do": "allocate", "size": 0, "name": "filesystem.bin"},
    { "do": "allocate", "size": 0, "name": "devicedata.bin"},

    {"do": "append", "to": "header.bin", "from": rom, "start": "0x0", "end": "0x100"},
    {"do": "append", "to": "easteregg.png", "from": rom, "start": "0x26EB60", "end": "0x280000"},
    {"do": "append", "to": "filesystem.bin", "from": rom, "start": "0x280000", "end": "0x3E0000"},
    {"do": "append", "to": "devicedata.bin", "from": rom, "start": "0x3E0000", "end": "0x400000"},

    {"do": "tar_add", "output": "rom.tar", "names": files},
    {"do": "tar_write", "output": "rom.tar"}
]

processor.process(config)
