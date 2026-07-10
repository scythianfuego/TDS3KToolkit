# CLI usage

Here are the command-line scripts for looking at, unpacking, and rebuilding
Tektronix TDS3000 ROM and firmware files.

## unpack_rom.py - unpack a ROM image

Use this to split a raw ROM dump into files inside a tar archive.

```bash
python unpack_rom.py <rom_file> <output.tar>
```

It writes:

- `header.bin`: first `0x100` bytes.
- `bootloader.bin`: bootloader section.
- `decompressor.bin`: Tek LZW decompressor code.
- `recovery.z`: compressed recovery stream from the ROM.
- `firmware.z`: compressed firmware stream from the ROM.
- `views/recovery.bin` and `views/firmware.bin`: unpacked views for reading.
- `filesystem.bin`: flash filesystem.
- `dispbmp.bin`: palette and RLE boot/update screen assets.
- `locale_<locale>.z`: compressed locale data.
- `views/locale_<locale>.bin`: unpacked locale views.

The script prints header fields, section headers, and checksums. It also tries
to unpack compressed sections and warns if something looks damaged. Locale data
is read after the firmware section until the next size value stops making
sense. Normal ROMs usually store locales in this order:
`en, it, kr, de, es, ja, fr, pt, ru, cn, tw`.

Notes:

- If checksums fail, the ROM may be damaged or may not boot. The script still
  saves what it can.
- Files at the tar root are the files `pack_rom.py` can use later.
- Files under `views/` are only there to make reading easier. `pack_rom.py`
  uses `firmware.z` and `recovery.z`, not the unpacked views.

## pack_rom.py - build a ROM image

Use this to make a ROM binary from the files normally made by `unpack_rom.py`.

```bash
python pack_rom.py <input.tar> <output_rom.bin>
```

The input tar should contain `header.bin`, `bootloader.bin`,
`decompressor.bin`, `recovery.z`, `firmware.z`, `easteregg.png`,
`filesystem.bin`, `dispbmp.bin`, and the expected `locale_<locale>.z` files.

The script makes a 4 MB ROM filled with `0xFF`, writes fixed sections at their
known offsets, updates section headers, and appends locale blocks after the
firmware. If unpacked firmware or recovery views are in the tar, it skips them.

After packing, run:

```bash
python verify_rom.py <output_rom.bin>
```

Do this before flashing anything.

## ftlfs.py - extract or rebuild the flash filesystem

Use this for the flash filesystem inside a ROM dump, or for a standalone
`filesystem.bin`.

```bash
python ftlfs.py extract <rom_or_filesystem.bin> <output_dir> [--fs-only]
python ftlfs.py pack <extract_dir> <output.bin> [--rom-template <rom.bin>]
```

Notes:

- `raw/key_XX.bin` files are the original payloads and can be packed back.
- `decoded/key_XX.json` files are editable views when a schema exists.
- If both raw and decoded files exist, the decoded JSON is used first.

## unpack_fw.py - unpack a vendor firmware ZIP

Use this on Tektronix firmware ZIP files `tds3000_*.zip`.

```bash
python unpack_fw.py <input_zip> <output.tar>
```

The ZIP should contain the usual update files:
`disk1/fwdisk1.dat`, `disk2/fwdisk2.dat`, `disk2/fwdisk2a.dat`,
`disk3/fwdisk3.dat`, and `disk4/fwdisk4.dat`.

The output tar includes files such as `service.dat`, `recovery.dat`,
`firmware.dat`, compressed LZW blobs under `lzw/`, per-locale `.dat` and `.z`
files, and decoded locale text under `locale/<locale>.txt`.

The text line numbers are sorted decoder output. They are not firmware message
IDs. If a locale text table cannot be decoded, the script prints a warning and
keeps the `.dat` and `.z` files. It does not create an empty `.txt` file.
If an LZW stream itself cannot be unpacked, its compressed bytes are kept as
`lzw/invalid_XX.z`; no empty `.dat` file is created.

## unpack_tds3000c_fw.py - unpack a TDS3000C firmware ZIP

Use this on TDS3000C firmware archives that contain `tds3000c.img`.

```bash
python unpack_tds3000c_fw.py <input_zip> <output.tar>
```

The output tar contains the three update headers, compressed and decompressed
firmware, bootstrap data, raw locale data, compressed locale streams, and any
locale text views that decode successfully.

## extract_boot_splash.py and pack_boot_splash.py - boot screen images

Use these to unpack and repack the boot/update screen image blocks.

```bash
python extract_boot_splash.py <rom_or_dispbmp.bin> -o <output_dir>
python pack_boot_splash.py <input_4bpp_indexed.png> <output_block.bin>
```

Extraction accepts either a full 4 MB ROM image or the 128 KiB `dispbmp.bin`
block. It writes `palette.txt`, `palette.png`, one
`block_XX_splash.png` file for each screen. Source offsets, RLE sizes, extra
tail sizes, and gaps between blocks are printed on screen.

Packing takes a non-interlaced indexed PNG with 4 bits per pixel and writes one
Tek RLE block:

```text
u32 pair_byte_count
RLE byte pairs
```

Some Tek ROMs have RLE streams with extra tail bytes or small overlaps with the
next count word. The PNG contains only the visible framebuffer, so these source
details are not needed when packing it. The packer makes a block the scope can
read; it does not try to match Tek's original byte stream.

## verify_rom.py - check a ROM image

Use this to check a ROM image before flashing it.

```bash
python verify_rom.py <rom_file>
```

It checks header magic values, section signatures, section sizes and addresses,
reserved flash areas, checksums, and locale block sizes. Standard images are
expected to have 11 locales. A failed required check or a missing locale makes
the script exit with a nonzero status.

## Common problems

- Missing files while packing: unpack with `unpack_rom.py` and keep the file
  names from the tar.
- Checksum failures: run `verify_rom.py` and compare the reported values.
- Locale problems: standard images have 11 locales. A different count can mean
  a different layout or a damaged ROM.
- LZW errors: compressed blobs may be damaged. Check the warning and source
  offset printed by the script.
