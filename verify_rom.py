import sys
from teklib.process import TekFileProcessor, align
from teklib.bootheader import parse_boot_header, print_boot_header, parse_section
from teklib.console import error, warning, success, notice, checksum_message, CYAN, RESET



def signature_message(text, calculated, expected):
    if (calculated != expected):
        error(f"{text:<35} = {calculated:08X} --> failed")

def section_message(text):
    print(f"\n-> {CYAN}{text}{RESET}\n")

def signature_fail(text, calculated, expected):
    if (calculated == expected):
        error(f"{text:<35} != {calculated:08X} --> failed")

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
    error(f"{name}: Bad address")
    return False

  if line["checksum"] == 0 or line["checksum"] == 0xFFFFFFFF:
    error(f"{name}: checksum is corrupt")
    return False

  if line["compressed"] != compressed:
    error(f"{name}: flags incorrect")
    return False

  if line["address"] > address_max or line["address"] < address:
    warning(f"{name}: Unexpected address: 0x{line['address']:08X}")
    return True

  return success(f"{name} header fields")

# ensure header sizes are within limits
def check_header_line_size(line, name, size, min, max):
  if line["size"] < min or line["size"] > max:
    error(f"{name}: Unexpected size: {line['size']}")
    return False

  if line["size"] != size:
    warning(f"{name}: Unexpected size, old software? size={line['size']}")
    return True

  success(f"{name} size")
  return True

def run_rom_check(rom):
  p = TekFileProcessor()
  p.read(file=rom)

  romdata = p.get(rom)
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
    error("Firmware section not found")

  address = header["recovery"]["address"] - 0xFFC00000
  if (address > 0 and address < 0x3FFFFF):
    recovery_header = parse_section(romdata, address)
    check_header_line(recovery_header, f"Recovery at 0x{address:X}", 1, 0xFFC04000)
  else:
    error("Recovery section not found")

  # check header after 0x60 is empty
  junk = checkjunk(romdata, 0x60, 0x100,  0xFFFFFFFF)
  if junk != 0:
      error(f"Header: not empty at 0x{junk:x}")
  else:
      success("Flash is empty: 0x60-0x100")

  # header after 0x60 is empty
  junk = checkjunk(romdata, 0x1E68, 0x4000, 0xFFFFFFFF)
  if junk != 0:
      error(f"Bootloader: not empty at 0x{junk:x}")
  else:
      success("Flash is empty: 0x1E68-0x4000")

  signature_message("Bootloader is corrupt", p.value(name=rom, at="0x100"), 0x3CC0FFC0)
  signature_message("Decompressor is corrupt", p.value(name=rom, at="0x100"), 0x3CC0FFC0)
  signature_message("Recovery section is corrupt", p.value(name=rom, at="0x4000"), 0xFFC04000)
  signature_message("Recovery compressed data corrupt", p.value(name=rom, at="0x4010") & 0xFFFF0000, 0x1F9D0000)


  section_message("Checksums (ROM will not boot if failed)")

  section = header["boot"]
  checksum_message("Bootloader checksum",
      p.checksum(name=rom, start=section["start"], end=section["end"]),
      header["boot"]["checksum"]
  )

  start = header["firmware"]["address"] - 0xFFC00000
  section = parse_section(romdata, start)
  locale_start = align(section["end"])
  checksum_message(f"Firmware checksum at 0x{start:x}",
      p.checksum(name=rom, start=section["start"], end=section["end"]),
      section["checksum"]
  )


  section_message("Checksums (must be correct, but not verified)")

  start = header["recovery"]["address"] - 0xFFC00000
  section = parse_section(romdata, start)
  checksum_message(f"Recovery checksum at 0x{start:x}",
      p.checksum(name=rom, start=section["start"], end=section["end"]),
      section["checksum"],
      fail=1
  )


  section = header["decompressor"]
  checksum_message("Decompressor checksum",
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
  checksum_message("Easter egg checksum", p.checksum(name=rom, start=0x26EB60, end=0x280000), 0x2A5DADCC )
  checksum_message("Filesystem checksum", p.checksum(name=rom, start=0x280000, end=0x3E0000) )
  checksum_message("Device data checksum", p.checksum(name=rom, start=0x3E0000, end=0x3FFFFF) )

  # TODO: check if compressed data is actually unpackable
  # TODO: check filesystem consistency

  section_message("Checking locale data")
  offset = locale_start
  locale_count = 0

  while True:
    size = p.value(name=rom, at=offset)
    magic = p.value(name=rom, at=offset+4) & 0xffff0000
    if size > 0x10000:
        break

    if (magic != 0x1F9D0000):
        warning(f"Locale{locale_count}: data corrupt")

    if (size < 0x5000 or size > 0xA000):
        warning(f"Locale{locale_count}: unexpected size {size}")

    offset += size
    offset = align(offset)
    locale_count += 1

  if (locale_count != 11):
    warning(f"Unexpected number of locales: {locale_count}")
  else:
    success("Found all 11 locales")

  print("\nRom check complete\n")


if len(sys.argv) == 2:
    input_file = sys.argv[1]
    run_rom_check(input_file)
else:
  print("Usage: python verify_rom.py <file>")
  sys.exit(1)