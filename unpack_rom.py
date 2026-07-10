from teklib import (
    TekFileProcessor, align, localename, known_locales,
    parse_boot_header, print_boot_header,
    calc_section_crc, parse_section, print_section,
    error, warning, checksum_message
)
import sys
import struct
import tarfile

def unpack_rom(rom, output_tar):
    files = [
        "header.bin",
        "bootloader.bin",
        "decompressor.bin",
        "recovery.z",
        "firmware.z",
        "easteregg.png",
        "filesystem.bin",
        "dispbmp.bin"
        ]


    p = TekFileProcessor()

    p.read(file=rom)
    romdata = p.get(rom)
    if len(romdata) != 0x400000:
        raise ValueError(f"expected a 0x400000-byte ROM, got 0x{len(romdata):X} bytes")

    for name in files:
        p.allocate(size=0, name=name)

    p.append(dest="header.bin", src=rom, start="0x0", end="0x100")
    p.append(dest="easteregg.png", src=rom, start="0x26EB60", end="0x280000")
    p.append(dest="filesystem.bin", src=rom, start="0x280000", end="0x3E0000")
    p.append(dest="dispbmp.bin", src=rom, start="0x3E0000", end="0x400000")

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
    if rec_section["address"] == 0xFFFFFFFF or rec_section["compressed"] > 1:
        warning("Recovery in-place header corrupt; using top recovery descriptor")
        rec_section = header["recovery"]
    crc_fw = calc_section_crc(sw_section, romdata)
    crc_rec = calc_section_crc(rec_section, romdata)

    print_section(f"recovery at 0x{header['recovery']['at']:X}", rec_section)
    print_section(f"firmware at 0x{header['firmware']['at']:X}", sw_section)

    checksum_message("Boot checksum", crc_boot, header["boot"]["checksum"], fail=1)
    checksum_message("Firmware checksum", crc_fw, sw_section["checksum"], fail=1)
    checksum_message("Recovery checksum", crc_rec, rec_section["checksum"], fail=1)
    checksum_message("Decompressor checksum", crc_decompressor, header["decompressor"]["checksum"], fail=1)

    p.append(dest="firmware.z", src=rom, start=sw_section["start"], end=sw_section["end"])
    try:
        p.unlzw(src="firmware.z", dest="views/firmware.bin")
        files.append("views/firmware.bin")
    except ValueError as e:
        warning(f"firmware.z: could not unpack LZW view: {e}")
    p.append(dest="decompressor.bin", src=rom, start=header["decompressor"]["start"], end=header["decompressor"]["end"])
    p.append(dest="bootloader.bin", src=rom, start=header["boot"]["start"], end=header["boot"]["end"])
    p.append(dest="recovery.z", src=rom, start=rec_section["start"], end=rec_section["end"])
    try:
        p.unlzw(src="recovery.z", dest="views/recovery.bin")
        files.append("views/recovery.bin")
    except ValueError as e:
        warning(f"recovery.z: could not unpack LZW view: {e}")


    offset = align(sw_section["end"])
    locale_count = 0

    while True:
        size = p.value(name=rom, at=offset)
        magic = p.value(name=rom, at=offset+4)
        if size is None or magic is None:
            break
        magic = magic & 0xffff0000
        if size < 8 or size > 0x10000:
            break

        name = localename(locale_count)
        compressed_name = f"{name}.z"
        p.allocate(size=0, name=compressed_name)
        p.append(dest=compressed_name, src=rom, start=offset+4, end=offset+size)
        files.append(compressed_name)

        if (magic != 0x1F9D0000):
            warning(f"{name}: data corrupt")
        else:
            view_name = f"views/{name}.bin"
            try:
                p.unlzw(src=compressed_name, dest=view_name)
                files.append(view_name)
            except ValueError as e:
                warning(f"{compressed_name}: could not unpack LZW view: {e}")

        offset += size
        offset = align(offset)
        locale_count += 1


    for name in files:
        p.print(name=name)


    p.tar_add(output=output_tar, names=files)
    p.tar_write(output=output_tar)


if len(sys.argv) == 3:
    rom = sys.argv[1]
    output_tar = sys.argv[2]
    try:
        unpack_rom(rom, output_tar)
    except (OSError, ValueError, TypeError, struct.error, tarfile.TarError) as e:
        error(f"unpack_rom.py: {e}")
        sys.exit(1)
else:
    print("Usage: python unpack_rom.py <rom_file> <output.tar>")
    sys.exit(1)
