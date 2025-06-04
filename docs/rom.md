# TDS3000 ROM and Software disks Structures - Raptor 14

## Floppy disk data

---

All data here and everywhere else is Big Endian (Motorola PowerPC).

Each floppy disk \*.dat file starts with the following header, size=0x56:

    {
        u8[8] TDS3000; // "TDS3000"
        u32 filecheckSum;   // checksum for this dat file
        u32 dataChecksum;   // checksum for whole data block spanning multiple dat files
        u32 major;  // 0x3 = major version 4 bytes
        u32 minor;  // 0x29 = 41 = minor version
        u32 diskNumber; // 1 = current disk number (disk #x of y)
        u32 diskCount;  // 2 = disk total count
        u8[56] copyright; // Copyright..reserved = 58 bytes
        u16 unk;   // always 0x08, is it just padding? same for all disks
    } DiskHeader;

Which is followed by one or multiple blocks of compressed data, that are not separated by any means:

    {
        u32 size;  // can be either compressed size or zero
        u8 data;   // starts with lzw magic number 1F9D
    }

Files for v3.41 firmware are:

- fwdisk1.dat (1 of 2) + fwdisk2.dat (2 of 2) - 1 lzw file inside

  This is a service firmware with unknown functions. Around 1Mb. sIt boots VxWorks environment, uses graphics and by default runs a software updater code (insert disk 1 of x etc). It is copied to ROM at address 0x40000 intact instead of usual user scope firmware.

  The update logic is to copy new recovery firmware (from fwdisk2a.dat), then copy user firmware from disks 3 and 4.
  After this is done, filesystem is being updated. For that reason, user firmware copied into ROM doesn't always boot.
  This step doesn't affect factory calibration data (or what is presumed to be it)

  The code has a lot of device and data block initializations with debug messages. Looks like it should have hidden/developer modes as strings contain hardware test messages and CPU register printouts.
  Has PNG code and its LZ77 inflate/deflate.
  Has same floppy disk driver similar to fwdisk2a and some network code.

  Noteable quotes:

        The background Pacman image is always the lowest priority.
        Unit Test is complete. Push FORCE TRIGGER to exit.

- fwdisk2a.dat (1 of 1) - 1 lzw file inside

  According to disk1 it is a "fd0:/fwdisk2a.dat recovery"
  This is a stripped recovery firmware that lives at 0x4000 and boots when main firmware is damaged (eg. failed update).

  When runs, outputs each and every step into debug serial port. Doesn't have advanced graphics.
  Has a floppy driver and VxWorks Dos FS (VXEXT1.0 extended DOS filesystem) with a lot of debuggind messages
  (see also https://github.com/x2c3z4/elf_insert/blob/master/samples/exp7/hook_src/dosFsLib.c)
  I2C driver is present. There seems to be a code to deal with all 4 update disks, however by default it loads only service software and boots into it afterwards.

  Noteable quotes:

        It's a Soar... it's a Raptor...

- fwdisk3.dat (3 of 4) + fwdisk4.dat (4 of 4) - 12 lzw files.
  This is user scope firmware copied into ROM at 0x40000 intact - size 1968424 bytes (0x1e0927)  
  (Which specifially means it is not being decompressed, but copied as is).
  fdisk4 contains more files, containing locales, copied after the software (as is)

  Translation files are a database of offsets generally in reverse order,
  followed by a set zero-terminated strings.  
  Offsets are relative to start of the string data.

## FLASH ROM

### Firmware

Generally, executable code blocks have data section and strings at the end of the block.  
When looking for executable code, search for following signature (common for all software):

    7C 60 00 A6 54 64 04 5E    |`   Td ^
    7C ?0 01 24 3C ?0 ?? ??    |` $<

Startup is located at 0x0, code entry point is at 0x100 which jumps to 0xB00 where actual code starts.  
Oscillscope calls this section "Boot", this document will refer to is as bootloader.

Data before 0x20 has unknown meaning. 0x60 to 0x100 is empty.
At 0x20 there is software lookup table, each line has a following structure:

    {
        u32 baseAddress; // in memory, starting with 0xFFC0
        u32 size;
        u32 checksum;
        u32 flags;      // 1 = compressed
    } HeaderLine;

Lines are

- 0x20 bootloader
- 0x30 firmware
- 0x40 decompressor
- 0x50 recovery

Bootloader behaviour [is described here](bootloader.md)

- You can break firmware checksum, making scope to boot into recovery.
- Neither recovery, nor service software checks what it loads from

LZW compressed recovery software is located at 0x4000, followed by LZW decompressor around 0x3E43C-0x40000.
Uncompressed contents get copied by decompressor into DRAM at 0x00600000.
Decompressor ends by the following sequence: 0x00 2092 times, then 0x01020304

The data after decompressor (as referenced in header) and before 0x40000 is non-zero, is it leftover junk or some unreferenced data? Oscilloscope works without it.

Compressed software always has its own HeaderLine at 0x4000 and 0x40000.
Actual LZW packed data starts at 0x40010, ends on or before 0x26EB60

Main oscilloscope software is followed by compressed locales, total of 11,
in the same format as on floppy disks: 4 byte size, aligned to 4 bytes, then
compressed data

# Filesystem

0x26EB60 - 0x280000 Contains PNG with Raptor team photoshoot

After that there is a wear-leveling flash filesystem, presumably custom.

File entry blocks are located at

- 0x280000, 0x2A0000, 0x2C0000, ... 0x380000, 0x3C0000

        struct FileRecord {
            u8 record_number; // may be some sort of file version
            u8 unk0; // always 0xFF
            u16 unk1; // 8F 40 some flags?
            u32 relativeOffset; // file data offset, ex.: +0x00000804
            u32 size; // file size, ex.: 0x00000A14
            u16 filename; // numeric, so more a record type than an actual name
            u16 unk3; //ex.: 0x32B4
        };

File contents is located at

- 0x280804, 0x2A0804, 0x2C0804, ... 0x380804, 0x3C0804

0x280800, 0x2A0800 etc is always zero

Note: Old FS empty space is sometimes filled with 0xEE instead of 0xFF (empty flash)
0x00 is actual zeroes in file data

Notable quotes:

    @XYZZY
    TDS 3012

Everything after is assumed to be data:
Where's first filesystem header? (when "empty"?)

0x26EB60 - 0x280060 PNG team photoshoot at next block at 0x00280804

    {
        u8 fixed0;
        u8 increasing; // this number is increasing. looks like this could be the file version when it is erased and overwritten
        u8 fixed2;
        u8 fixed3;
        u32 unk; // 0x1fff???? could be an address mask, partition boundary, or a special flag.
        u32 file_offset; // file position offset
        u32 mostly_zero_bits; // looks like flags
    } FSRecord;

0x3C0804 - 0x3D9B48 blue/white/zeroes, 40 byte records? Ends up with tons of strings,
including full "alphabet" (00 00 03 a, 00 00 03 b), @XYZZY and TDS 3052. end is unaligned

# Device data

0x3E0000 - 0x3FFFFF huge chunk of structured data.
Assumption is factory calibration data is stored here. Surprisingly consistent between different scopes,
two devices have a different single u32 value (todo: check new scope)/

According to bootlader code it is hardware device data, written directly at HW addresses (ex. 0x30100C00)  
Lots of ascii symbols. No zeroes. 16 bit numbers are between ~270 and 600

See [bootloader description](bootloader.md) on how it is used.
