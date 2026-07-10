# TDS3000 ROM and software disk structures - Raptor 14

## Floppy disk data

---

All data here is big-endian (Motorola PowerPC).

Each public update payload file starts with a 0x60-byte header. Updater code
checks the header before reading payload chunks:

    {
        u8[8] marker; // "TDS 3000"
        u32 filecheckSum;   // checksum for this dat file
        u32 dataChecksum;   // checksum for whole data block spanning multiple dat files
        u32 major;  // 0x3 = major version 4 bytes
        u32 minor;  // 0x29 = 41 = minor version
        u32 diskNumber; // 1 = current disk number (disk #x of y)
        u32 diskCount;  // 2 = disk total count
        u8[64] copyright_reserved;
    } DiskHeader;

Payload starts at file offset `0x60`. Some DAT payloads are one LZW stream
split across disks. Other firmware containers may carry multiple compressed
blocks one after another; ROM locale blocks use a 4-byte size word before each
compressed block:

    {
        u32 size;
        u8 data;   // LZW data starts with magic number 1F9D
    }

Files for v3.41 firmware are:

- fwdisk1.dat (1 of 2) + fwdisk2.dat (2 of 2) - 1 lzw file inside

  This is service firmware with unknown functions, around 1 MB. It boots a
  VxWorks environment, uses graphics, and by default runs the software updater
  code (insert disk 1 of x, and so on). It is copied to ROM at file offset
  `+0x40000` as-is instead of the normal user scope firmware.

  The update logic is to copy new recovery firmware (from fwdisk2a.dat), then copy user firmware from disks 3 and 4.
  After this, the filesystem is updated. For that reason, user firmware copied
  into ROM does not always boot.
  This step does not affect factory calibration data, or what looks like it.

  The code has a lot of device and data block setup with debug messages. It
  looks like it may have hidden or developer modes because the strings contain
  hardware test messages and CPU register printouts.
  It has PNG code and LZ77 inflate/deflate code.
  It has a floppy disk driver similar to fwdisk2a and some network code.

  Notable quotes:

        The background Pacman image is always the lowest priority.
        Unit Test is complete. Push FORCE TRIGGER to exit.

- fwdisk2a.dat (1 of 1) - 1 lzw file inside

  According to disk1 it is a "fd0:/fwdisk2a.dat recovery"
  This is stripped-down recovery firmware that lives at file offset `+0x4000`
  and boots when the main firmware is damaged, such as after a failed update.

  When it runs, it prints each step to the debug serial port. It does not have
  advanced graphics.
  It has a floppy driver and VxWorks Dos FS (VXEXT1.0 extended DOS filesystem)
  with a lot of debugging messages
  (see also https://github.com/x2c3z4/elf_insert/blob/master/samples/exp7/hook_src/dosFsLib.c)
  An I2C driver is present. There seems to be code for all 4 update disks, but
  by default it only loads the service software and then boots into it.

  Notable quotes:

        It's a Soar... it's a Raptor...

- fwdisk3.dat (3 of 4) + fwdisk4.dat (4 of 4) - 12 LZW files.
  This is user scope firmware copied into ROM at file offset `+0x40000` as-is.
  Its size is 1968424 bytes (`0x1e0927`). This means it is copied, not
  decompressed.
  fwdisk4 contains more files with locales. They are copied after the software.

  Locale files start with a table of 32-bit offsets followed by
  zero-terminated byte strings. Offsets are relative to the string data.
  Runtime message IDs are the raw table indexes, not the sorted line numbers
  printed by `teklib.strings.decode_table()`.

  Firmware decompresses the selected locale block to RAM at `0x003473BC`, then
  rewrites `0x6E9` offsets into absolute string pointers. Message IDs therefore
  run from `0` through `0x6E8`, even when multiple IDs point at the same string.

  The physical locale order in v3.41 is:

        en, it, kr, de, es, ja, fr, pt, ru, cn, tw

  The saved language setting is remapped at runtime before loading a physical
  locale block:

        0/default -> en
        1 -> fr, 2 -> de, 3 -> it, 4 -> es, 5 -> pt, 6 -> ru
        7 -> ja, 8 -> kr, 9 -> tw, 10 -> cn

  Locale byte strings also contain display escapes. Known families are
  `0x1B xx` style/color escapes and `0x01 page byte` glyph-page references for
  Korean, Chinese, Japanese, and Russian text.

## FLASH ROM

### Firmware

Executable code blocks usually have a data section and strings at the end of
the block. When looking for executable code, search for this signature, which
is common to all software:

    7C 60 00 A6 54 64 04 5E    |`   Td ^
    7C ?0 01 24 3C ?0 ?? ??    |` $<

Startup is at file offset `+0x0`. The code entry point is at `+0x100`, which
jumps to `+0xB00`, where the main code starts.
The oscilloscope calls this section "Boot"; this document calls it the
bootloader.

The first `0x20` bytes are ROM metadata used by the bootloader/updater. In the
known v3.15/v3.41 ROMs the first word is `0x00000004`, and following words
point into the dispBmp asset block at file offsets such as `+0x3EBBDC`,
`+0x3EEA4C`, `+0x3EA074`, `+0x3E0040`, `+0x3F4420`, and `+0x3F92E4`.
`0x60` to `0x100` is erased padding in the standard ROM images checked so far.

At `0x20` there is a software lookup table. Each line has this structure:

    {
        u32 baseAddress; // bootloader memory address; subtract 0xFFC00000 for file offset
        u32 size;
        u32 checksum;
        u32 flags;      // 1 = compressed
    } HeaderLine;

Lines are

- 0x20 bootloader
- 0x30 firmware
- 0x40 decompressor
- 0x50 recovery

Bootloader behavior is described in [bootloader.md](bootloader.md).

- You can break the firmware checksum to make the scope boot into recovery.
- Recovery and service software do not check what they load from.

LZW-compressed recovery software is at `+0x4000`, followed by the LZW
decompressor around `+0x3E43C..+0x40000`.
The bootloader copies the decompressor itself to RAM. Compressed main/updater
firmware is unpacked to that firmware's RAM load and entry layout by the
decompressor.
The decompressor ends with this sequence: `0x00` 2092 times, then
`0x01020304`.
The scope LZW decompressor seems to ignore unpack errors.

The data after the decompressor, as named in the header, and before `+0x40000`
is non-zero. It may be leftover data or unreferenced data. The oscilloscope
works without it.

Compressed software always has its own HeaderLine at `+0x4000` and `+0x40000`.
Actual LZW packed data starts at `+0x40010`, ends on or before `+0x26EB60`.
`unpack_rom.py` saves these byte streams as `recovery.z` and `firmware.z`.
The decompressed `views/recovery.bin` and `views/firmware.bin` files are
analysis views only. The toolkit does not pack from them because a recompressor
would not produce Tek's original byte-identical LZW stream.

Main oscilloscope software is followed by 11 compressed locale blocks. Each
block has a big-endian 4-byte size word, then compressed data, padded to a
4-byte boundary.

# Filesystem

`+0x26EB60..+0x280000` contains a PNG with a Raptor team photoshoot.

After that there is a wear-leveling flash filesystem in `+0x280000..+0x3E0000`.
Logical segment IDs are stored in byte 0 of each physical sector; record slots
start at sector `+0x04`, and payload data starts at sector `+0x804`.

See [flash filesystem](filesystem.md) for the current record fields, logical
segment mapping, and sample records.

# dispBmp display assets

`+0x3E0000..+0x3FFFFF` contains bootloader/updater display assets.

The first `0x40` bytes are 16 big-endian RGB444 palette words copied to the
display palette/LUT register area. The rest contains several
RLE streams for packed 4bpp 640x480 framebuffers. The bootloader expands the
first stream to the display framebuffer; updater code can use the later streams
for firmware-update prompts.

See [boot splash assets](splash.md) for the decoded format and extractor.
