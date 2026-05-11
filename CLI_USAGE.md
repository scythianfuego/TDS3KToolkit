# CLI Usage & Script Descriptions

This repository provides small command-line utilities for inspecting, extracting, and (re)building Tektronix ROM and firmware images. Each script is intentionally single-purpose and designed to be run from a shell. Below you'll find what each script does, the files it expects and produces, and helpful notes for common failure modes.

---

## 1) unpack_rom.py — Parse and extract a ROM image

Purpose

- Parse a raw Tektronix ROM image, validate header fields and checksums, and extract every embedded component into a tar archive.

Inputs

- A single ROM binary file (raw flash dump).

Outputs (added to the tar archive)

- header.bin — first 0x100 bytes (boot header)
- bootloader.bin — bootloader section
- decompressor.bin — Tektronix LZW decompressor code
- recovery.z / recovery.bin — compressed and decompressed recovery images
- firmware.z / firmware.bin — compressed and decompressed firmware
- filesystem.bin, devicedata.bin — filesystem and device metadata
- locale/<locale>.bin — decompressed locale data for each supported locale (best guess on languages)

Behavior and checks

- Reads and prints boot header fields and section headers.
- Computes and reports checksums for boot, decompressor, firmware, and recovery sections.
- Attempts to unlzw compressed sections and warns if data seems corrupt.
- Iterates locale blobs after the firmware section and extracts them until an invalid size is encountered. The code expects 11 locales in the usual images.

Usage

```bash
python unpack_rom.py <rom_file> <output.tar>
```

Notes

- If checksums fail, the ROM may be corrupted and may not boot. The script still extracts what it can while reporting errors.
- The output tar contains the files listed above and can be used with `pack_rom.py` to re-create a ROM image.

---

## 2) pack_rom.py — Build a ROM image from components

Purpose

- Assemble a ROM binary from the set of files normally produced by `unpack_rom.py`.

Inputs

- A tar archive containing the files `header.bin`, `bootloader.bin`, `decompressor.bin`, `recovery.z`, `firmware.z`, `easteregg.png`, `filesystem.bin`, `devicedata.bin` and locale .z files (named as the project `known_locales()` expects).

Output

- A single ROM binary file (size 0x400000 by default) containing written sections, headers, and appended locales.

Behavior and notes

- The script creates a 4 MB ROM image filled with 0xFF, writes fixed sections (e.g., easteregg, filesystem) at predefined offsets, and places the compressed firmware, recovery and decompressor at expected addresses.
- It writes updated section headers (using `pack_section`) and appends locale blobs after the firmware. The script also pads the end of firmware to a 4-byte boundary.
- Ensure the input tar contains the expected file names. Missing or incorrectly named files will produce a broken ROM.
- After packing, run `verify_rom.py` to confirm header fields and checksums are valid before flashing to hardware.

Usage

```bash
python pack_rom.py <input.tar> <output_rom.bin>
```

---

## 3) unpack_fw.py — Extract firmware content from a vendor ZIP

Purpose

- Process a Tektronix-provided firmware ZIP archive (the `tds3000_*.zip` style archives), extract disk images, split LZW blocks, and decode locale string tables.

Inputs

- Firmware ZIP archive (containing `disk1/fwdisk1.dat`, `disk2/fwdisk2.dat`, `disk2/fwdisk2a.dat`, `disk3/fwdisk3.dat`, `disk4/fwdisk4.dat`).

Outputs

- A collection of files in the output tar: `service.dat`, `recovery.dat`, `firmware.dat`, compressed LZW blobs under `lzw/`, per-locale `.dat` and `.z` files, and `locale/<locale>.txt` with decoded string tables.

Behavior and checks

- Reads fwdisk files, extracts compressed service/recovery/firmware.
- Validates checksums.
- Decodes locale tables and generates plain-text `locale/<locale>.txt` files.

Usage

```bash
python unpack_fw.py <input_zip> <output.tar>
```

---

## 4) verify_rom.py — Validate a ROM image

Purpose

- Integrity check on a ROM image.

Checks performed

- Verifies magic values at header offsets and section signatures (e.g. boot magic, compressed-data signature 0x1F9D0000).
- Validates header fields (addresses, sizes, compression flags) against sane ranges and expected values.
- Ensures reserved flash regions are empty where required.
- Calculates checksums for boot, firmware, recovery and the decompressor and reports mismatches. Some checks print failures that will likely prevent the ROM from booting.
- Scans locale blobs and reports the number and sizes (expects 11 locales in standard images).

Usage

```bash
python verify_rom.py <rom_file>
```

Notes

- Use this after `pack_rom.py` to confirm the image is structurally correct and has valid checksums before attempting to flash hardware.

---

## Common troubleshooting

- Missing files when packing: ensure you used `unpack_rom.py` and retained the expected file names inside the tar. `pack_rom.py` relies on exact names.
- Checksum failures: re-run `verify_rom.py` and inspect the printed checksum values. If firmware/recovery checks fail, the ROM may be corrupted.
- Locale extraction problems: the code expects 11 locales; if you see a different count, the layout might be non-standard or the ROM is damaged.
- LZW/unlzw errors: corrupted compressed blobs can prevent `unlzw()` from decoding; check printed warnings and source offsets.
