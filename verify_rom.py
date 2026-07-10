import sys
import struct
from teklib.process import TekFileProcessor, align
from teklib.bootheader import parse_boot_header, print_boot_header, parse_section
from teklib.console import error, warning, success, checksum_message, CYAN, RESET


failure_count = 0


def fail(text):
    global failure_count
    failure_count += 1
    error(text)

def signature_message(text, calculated, expected):
    if (calculated != expected):
        fail(f"{text:<35} = {calculated:08X} --> failed")
        return False
    return True

def section_message(text):
    print(f"\n-> {CYAN}{text}{RESET}\n")

def verified_checksum(text, calculated, expected):
    checksum_message(text, calculated, expected)
    if calculated != expected:
        global failure_count
        failure_count += 1
        return False
    return True

def checkjunk(data, start, end, expected):
    for i in range(start, end, 4):
        if (data[i:i+4] != expected.to_bytes(4, byteorder='big')):
            return i
    return 0


# ensure header values are sane
def check_header_line(line, name, compressed, address, address_max = None):
  if (address_max == None):
    address_max = address

  if line["address"] < 0xFFC00000:
    fail(f"{name}: bad address")
    return False

  if line["checksum"] == 0 or line["checksum"] == 0xFFFFFFFF:
    fail(f"{name}: checksum is corrupt")
    return False

  if line["compressed"] != compressed:
    fail(f"{name}: flags incorrect")
    return False

  if line["address"] > address_max or line["address"] < address:
    warning(f"{name}: Unexpected address: 0x{line['address']:08X}")
    return True

  return success(f"{name} header fields")

# ensure header sizes are within limits
def check_header_line_size(line, name, size, min, max):
  if line["size"] < min or line["size"] > max:
    fail(f"{name}: unexpected size: {line['size']}")
    return False

  if line["size"] != size:
    warning(f"{name}: size {line['size']} differs from known size {size}")
    return True

  success(f"{name} size")
  return True

def run_rom_check(rom):
  global failure_count
  failure_count = 0

  p = TekFileProcessor()
  p.read(file=rom)

  romdata = p.get(rom)
  if len(romdata) != 0x400000:
    raise ValueError(f"expected a 0x400000-byte ROM, got 0x{len(romdata):X} bytes")

  header = parse_boot_header(romdata)
  print(f"ROM check for {rom}")
  section_message("Header data")
  print_boot_header(header)

  # Check headers and know magic values
  section_message("Consistency check")
  signature_message("Header: Magic incorrect at 0x0", p.value(name=rom, at="0x0"), 0x00000004)
  signature_message("Header: Magic incorrect at 0x4", p.value(name=rom, at="0x4"), 0xFFFEBBDC)
  signature_message("Header: Magic incorrect at 0x8", p.value(name=rom, at="0x8"), 0xFFFEEA4C)
  signature_message("Header: Magic incorrect at 0xC", p.value(name=rom, at="0xC"), 0xFFFEA074)

  # Maximum allowed bootloader size = 0x4000−0x100
  check_header_line(header["boot"], "Bootloader", 0, 0xFFC00100)
  check_header_line_size(header["boot"], "Bootloader", 7512, 5000, 16128)

  # Decompressor should be small enough to fit before the firmware
  check_header_line(header["decompressor"], "Decompressor", 0, 0xFFC3E000, 0xFFC40000)
  check_header_line_size(header["decompressor"], "Decompressor", 4100, 4000, 8192)

  # Sizes for firmware and recovery sections are ignored
  check_header_line(header["firmware"], "Firmware", 1, 0xFFC40000)
  check_header_line(header["recovery"], "Recovery", 1, 0xFFC04000)

  address = header["firmware"]["address"] - 0xFFC00000
  if (address > 0 and address < 0x3FFFFF):
    fw_header = parse_section(romdata, address)
    check_header_line(fw_header, f"Firmware at 0x{address:X}", 1, 0xFFC40000)
  else:
    fail("Firmware section not found")

  address = header["recovery"]["address"] - 0xFFC00000
  if (address > 0 and address < 0x3FFFFF):
    recovery_header = parse_section(romdata, address)
    check_header_line(recovery_header, f"Recovery at 0x{address:X}", 1, 0xFFC04000)
  else:
    fail("Recovery section not found")

  # check header after 0x60 is empty
  junk = checkjunk(romdata, 0x60, 0x100,  0xFFFFFFFF)
  if junk != 0:
      fail(f"Header: not empty at 0x{junk:x}")
  else:
      success("Flash is empty: 0x60-0x100")

  # header after 0x60 is empty
  junk = checkjunk(romdata, 0x1E68, 0x4000, 0xFFFFFFFF)
  if junk != 0:
      fail(f"Bootloader: not empty at 0x{junk:x}")
  else:
      success("Flash is empty: 0x1E68-0x4000")

  signature_message("Bootloader is corrupt", p.value(name=rom, at="0x100"), 0x3CC0FFC0)
  signature_message("Recovery section is corrupt", p.value(name=rom, at="0x4000"), 0xFFC04000)
  signature_message("Recovery compressed data corrupt", p.value(name=rom, at="0x4010") & 0xFFFF0000, 0x1F9D0000)


  section_message("Checksums (ROM will not boot if failed)")

  section = header["boot"]
  verified_checksum("Bootloader checksum",
      p.checksum(name=rom, start=section["start"], end=section["end"]),
      header["boot"]["checksum"]
  )

  start = header["firmware"]["address"] - 0xFFC00000
  section = parse_section(romdata, start)
  locale_start = align(section["end"])
  verified_checksum(f"Firmware checksum at 0x{start:x}",
      p.checksum(name=rom, start=section["start"], end=section["end"]),
      section["checksum"]
  )


  section_message("Checksums (required)")

  start = header["recovery"]["address"] - 0xFFC00000
  section = parse_section(romdata, start)
  verified_checksum(f"Recovery checksum at 0x{start:x}",
      p.checksum(name=rom, start=section["start"], end=section["end"]),
      section["checksum"]
  )


  section = header["decompressor"]
  verified_checksum("Decompressor checksum",
      p.checksum(name=rom, start=section["start"], end=section["end"]),
      header["decompressor"]["checksum"]
  )


  section_message("Checksums, not updated with firmware (ignored)")

  section = header["firmware"]
  checksum_message("Firmware checksum - header",
      p.checksum(name=rom, start=section["start"], end=section["end"]),
      header["firmware"]["checksum"],
      fail=0
  )

  section = header["recovery"]
  checksum_message("Recovery checksum",
      p.checksum(name=rom, start=section["start"], end=section["end"]),
      header["recovery"]["checksum"],
      fail=0
  )


  section_message("Checksums, other")

  # Raptor team PNG
  checksum_message("Easter egg checksum", p.checksum(name=rom, start=0x26EB60, end=0x280000) )
  checksum_message("Filesystem checksum", p.checksum(name=rom, start=0x280000, end=0x3E0000) )
  checksum_message("dispBmp checksum", p.checksum(name=rom, start=0x3E0000, end=0x3FFFFF) )

  # TODO: check if compressed data is actually unpackable
  # TODO: check filesystem consistency

  section_message("Checking locale data")
  offset = locale_start
  locale_count = 0

  while True:
    if offset + 8 > len(romdata):
        break

    size = p.value(name=rom, at=offset)
    magic = p.value(name=rom, at=offset+4)
    if size < 8 or size > 0x10000:
        break

    if ((magic & 0xFFFF0000) != 0x1F9D0000):
        fail(f"Locale{locale_count}: LZW magic is missing")

    if (size < 0x5000 or size > 0xA000):
        warning(f"Locale{locale_count}: unexpected size {size}")

    offset += size
    offset = align(offset)
    locale_count += 1

  if (locale_count != 11):
    fail(f"Expected 11 locales, found {locale_count}")
  else:
    success("Found all 11 locales")

  if failure_count:
    fail_word = "failure" if failure_count == 1 else "failures"
    print(f"\nROM check complete: {failure_count} {fail_word}\n")
    return 1

  print("\nROM check complete: no failures\n")
  return 0


def main(argv):
  if len(argv) != 2:
    print("Usage: python verify_rom.py <rom_file>")
    return 1

  try:
    return run_rom_check(argv[1])
  except (OSError, ValueError, TypeError, struct.error) as e:
    error(f"verify_rom.py: {e}")
    return 1


if __name__ == "__main__":
  raise SystemExit(main(sys.argv))
