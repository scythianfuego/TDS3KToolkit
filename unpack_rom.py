from teklib import (
    TekFileProcessor, align, localename, known_locales,
    parse_boot_header, print_boot_header,
    calc_section_crc, parse_section, print_section,
    error, warning, success, notice, checksum_message,
    checksum
)
import sys

def unpack_rom(rom, output_tar):
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
        ] + known_locales(".z") + ["locale/" + f for f in known_locales(".bin")]


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


    offset = align(sw_section["end"])
    locale_count = 0

    while True:
        size = p.value(name=rom, at=offset)
        magic = p.value(name=rom, at=offset+4) & 0xffff0000
        if size > 0x10000:
            break

        name = localename(locale_count)

        if (magic != 0x1F9D0000):
            warning(f"{name}: data corrupt")
        else:
            p.append(dest=f"{name}.z", src=rom, start=offset+4, end=offset+size)
            p.unlzw(src=f"{name}.z", dest=f"locale/{name}.bin")

        offset += size
        offset = align(offset)
        locale_count += 1


    for name in files:
        p.print(name=name)


    p.tar_add(output="rom.tar", names=files)
    p.tar_write(output="rom.tar")


if len(sys.argv) == 3:
    rom = sys.argv[1]
    output_tar = sys.argv[2]
    unpack_rom(rom, output_tar)
else:
    print("Usage: python unpack_rom.py <rom_file> <output.tar>")
    sys.exit(1)
