from teklib.process import TekFileProcessor, known_locales
from teklib.console import checksum_message, warning
from teklib.strings import decode_table
import struct
import sys


def block_size(data, offset):
    return struct.unpack_from(">I", data, offset + 0x5c)[0]


def block_checksum(data, offset):
    return struct.unpack_from(">I", data, offset + 0x08)[0]


def block_end(data, offset):
    return offset + 0x60 + block_size(data, offset)


def test_checksums(p):
    checksum_message("Firmware block checksum",  p.checksum(name="lzw/firmware.z"), p.value(name="header_0.bin", at="0x08") )
    checksum_message("Locale block checksum",    p.checksum(name="locales.dat"),     p.value(name="header_1.bin", at="0x08") )
    checksum_message("Bootstrap block checksum", p.checksum(name="bootstrap.dat"),   p.value(name="header_2.bin", at="0x08") )


def print_header(data, index, offset):
    print(f"Header {index}:")
    print(f"  offset     0x{offset:08X}")
    print(f"  checksum   0x{block_checksum(data, offset):08X}")
    print(f"  data size  0x{block_size(data, offset):08X}")
    print(f"  next       0x{block_end(data, offset):08X}")


def unpack_fw(input_file, output_tar):
    files_to_save = [
        "header_0.bin", "header_1.bin", "header_2.bin",
        "firmware.dat", "bootstrap.dat", "locales.dat",
        "lzw/firmware.z"]

    locale_names = known_locales()

    p = TekFileProcessor()

    p.zip_read( file=input_file, path="tds3000c.img")

    for name in files_to_save:
        p.allocate(size=0, name=name)

    data = p.get("tds3000c.img")
    headers = []
    offset = 0

    while offset < len(data):
        if data[offset:offset + 8] != b"TDS 3000":
            warning(f"No Tektronix header at 0x{offset:08X}, stopping")
            break

        headers.append(offset)
        offset = block_end(data, offset)

    if len(headers) != 3:
        warning(f"Expected 3 Tektronix headers, found {len(headers)}")
        sys.exit(1)

    for i, offset in enumerate(headers):
        p.append(dest=f"header_{i}.bin", src="tds3000c.img", start=offset, end=offset + 0x60)
        print_header(data, i, offset)

    firmware_header = headers[0]
    locale_header = headers[1]
    bootstrap_header = headers[2]

    p.append(dest="lzw/firmware.z", src="tds3000c.img", start=firmware_header + 0x60, end=block_end(data, firmware_header))
    p.unlzw( src="lzw/firmware.z", dest="firmware.dat")

    p.append(dest="locales.dat", src="tds3000c.img", start=locale_header + 0x60, end=block_end(data, locale_header))
    p.append(dest="bootstrap.dat", src="tds3000c.img", start=bootstrap_header + 0x60, end=block_end(data, bootstrap_header))

    test_checksums(p)

    offset = locale_header + 0x60
    end = block_end(data, locale_header)
    index = 0

    while offset < end:
        chunk_size = struct.unpack_from(">I", data, offset)[0]

        if chunk_size == 0:
            break

        if offset + chunk_size > end:
            warning(f"Locale chunk {index}: size runs past block end")
            break

        if data[offset + 4:offset + 6] != b"\x1f\x9d":
            warning(f"Locale chunk {index}: missing LZW magic")

        if index < len(locale_names):
            name = locale_names[index]
        else:
            name = f"buffer_{index}"

        p.allocate(size=0, name=f"{name}.dat")
        p.allocate(size=0, name=f"lzw/{name}.z")
        p.allocate(size=0, name=f"locale/{name}.txt")

        p.append(dest=f"lzw/{name}.z", src="tds3000c.img", start=offset + 4, end=offset + chunk_size)
        p.unlzw( src=f"lzw/{name}.z", dest=f"{name}.dat")

        try:
            results = decode_table(p.get(f"{name}.dat"))
            s = []
            for i, (string_offset, string) in enumerate(results):
                s.append(f"{i:4d}\t0x{string_offset:04x}\t{string}\n")
            s = ''.join(s)
            p.append(data=s.encode('utf-8'), dest=f"locale/{name}.txt")
            files_to_save.append(f"locale/{name}.txt")
        except Exception as e:
            warning(f"{name}: could not decode string table: {e}")

        files_to_save.append(f"{name}.dat")
        files_to_save.append(f"lzw/{name}.z")

        offset += chunk_size
        index += 1

    print("\nSaving files...")
    for name in files_to_save:
        p.print(name=name)
    p.tar_add( output=output_tar, names=files_to_save)
    p.tar_write( output=output_tar)

    print(f"--> {output_tar}")


if len(sys.argv) == 3:
    input_file = sys.argv[1]
    output_tar = sys.argv[2]
    unpack_fw(input_file, output_tar)
else:
    print("Usage: python unpack_tds3000c_fw.py <input_zip> <output.tar>")
    sys.exit(1)
