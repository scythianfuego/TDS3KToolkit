# TDS3000 filesystem structure

The flash wear-leveling filesystem lives in the ROM window `+0x280000..+0x3E0000`.
Use `ftlfs.py` to extract or pack it.

## Current model

The filesystem is made of 11 physical flash sectors, each `0x20000` bytes:

```text
+0x280000, +0x2A0000, +0x2C0000, ... +0x3C0000
```

Byte 0 of each physical sector is the current logical segment number. `0xFF`
means erased/spare. Do not assume logical segment `N` lives at file offset
`+0x280000 + N * 0x20000`; updater code resolves logical segments by scanning
byte 0 of all physical sectors.

Metadata records start at sector `+0x04`. There are 128 slots of 16 bytes:

```c
struct FtlfsRecord {
    uint8  key;            // numeric NV/file ID
    uint8  marker;         // often 0xFF
    uint16 ignored0;       // not used
    uint32 relativeOffset; // payload offset within this sector
    uint32 size;           // payload size
    uint16 checksum;       // sum(payload bytes) + 0x1234, modulo 16 bits
    uint16 ignored1;       // not used
};
```

Payload data starts at sector `+0x804`.
Later valid records for the same key in one logical segment replace earlier
slots. Physical sector order is just wear-leveling order.

## Tool behavior

`ftlfs.py extract` writes active records only:

- `raw/key_XX.bin` for the original record payload.
- `decoded/key_XX.json` when a matching cstruct schema exists.

`ftlfs.py pack` reads decoded JSON first when present, otherwise the raw blob.
It rebuilds a valid compact filesystem with new slots, offsets, and checksums.
It does not try to keep stale records or the original physical sector order.

## Logical segments

The updater key table groups keys by logical segment:

```text
seg 0x01: 0x00..0x09, 0x38..0x41, 0x4E, 0x4F
seg 0x02: 0x0A..0x0D
seg 0x03: 0x12..0x1B, 0x1F..0x22, 0x42..0x44
seg 0x04: 0x1C..0x1E, 0x23, 0x45..0x4D
seg 0x05: 0x24..0x27, 0x34..0x37
seg 0x06: 0x28..0x2B
seg 0x07: 0x2C..0x2F
seg 0x08: 0x30..0x33
seg 0x09: 0x0E, 0x0F
seg 0x0A: 0x10, 0x11
```

Some high-value record groups:

- `0x12`: model/config string.
- `0x13`: persistent error log.
- `0x17..0x1E`, `0x23..0x33`, `0x50`: calibration/SPC/acquisition-related records.
- `0x38..0x41`: diagnostic history slots.
- `0x42`: language, cal notify, RS-232, and GPIB settings.

Current schema-backed groups include saved setup slots `0x00..0x09`,
reference waveform headers `0x0A..0x0D`, model/config `0x12`, persistent error
log `0x13`, power-up/settings records `0x14..0x16`, calibration/SPC records
`0x17..0x1E` and `0x23..0x33`, password/PUD records `0x20..0x21`,
diagnostic-history records `0x38..0x41`, system settings `0x42`, Rev B
network/web records `0x43`, `0x44`, `0x4F`, mask-test records `0x45..0x4D`,
and FISO timing counters `0x50`.

Keys `0x0E..0x11` are reference waveform sample data and are normally kept as
raw payloads.

## Default calibration references

`teklib/default_calibration_blobs/` contains JSON views of default calibration
values reconstructed from firmware. They are format references, not
device-specific calibration backups, and `ftlfs.py` does not apply them
automatically.

Each filename states the record key and data structure name. The files are
independent, so this directory does not need a manifest.

## Old sample observations

The raw observations below are kept as examples of what sectors and records
look like in ROM dumps. Offsets are file offsets; interpret the records using
the field names above.

0x280000 - 0x280064 filesystem entries
0x280804 - 0x2968B4 big, dataish, includes at least 4 zero spans

Filesystem:
0x2A0000 - 0x2A0024 filesystem entries, 2kB size
0x2A0804 - 0x2AA444 patterns like ff 80, f8 00 etc
0x2C0000 - 0x2C04E4 filesystem entries
0x2C0804 - 0x2D1A64 ?B.J, many zeroes, some 16 byte blocks. "02/15/2021 StartUp". DB log file?
0x2E0000 - 0x2e0174 filesystem entries
0x2e0804 - 0x2E3B7C Zeroes, tons of them. XYZZY
0x300000 - 0x300034 filesystem entries
0x300804 - 0x30F264 huge chunk of 80 00 ("zero" u16 max range)
0x320000 - 0x320064 filesystem entries
0x320804 - 0x3368B4 huge chunk of zeroes
0x340000 - 0x340064 filesystem entries
0x340804 - 0x3568B4 huge chunk of zeroes
0x360000 - 0x360544 filesystem entries
0x360804 - 0x371944 ?PbM CH1+CH2 >LX pass--CPU fail--CPU
0x380000 - 0x380064 filesystem entries
0x380804 - 0x3968B4 data, multiple zero spans, at 0x394680 is 12 byte block file (red)
0x3C0000 - 0x3C0664 filesystem entries

Sample entries:

00 FF 8F 40 00 00 08 04 00 00 0A 14 FB 8D 32 B4
01 FF 8F 40 00 00 12 18 00 00 0A 14 FB 8D 32 B4
02 FF 8F 40 00 00 1C 2C 00 00 0A 14 FB 8D 32 B4
03 FF 8F 40 00 00 26 40 00 00 0A 14 FB 8D 32 B4
04 FF 8F 40 00 00 30 54 00 00 0A 14 FB 8D 32 B4
05 FF 8F 40 00 00 3A 68 00 00 0A 14 FB 8D 32 B4
..
38 FF 8F 40 00 00 6C CC 00 00 00 2C 18 38 32 B4
39 FF 8F 40 00 00 6C F8 00 00 00 2C 18 38 32 B4
3A FF 8F 40 00 00 6D 24 00 00 00 2C 18 38 32 B4
3C FF 8F 40 00 00 6D 50 00 00 00 2C 18 38 32 B4
3D FF 8F 40 00 00 6D 7C 00 00 00 2C 18 38 32 B4
3E FF 8F 40 00 00 6D A8 00 00 00 2C 18 38 32 B4
3F FF 8F 40 00 00 6D D4 00 00 00 2C 18 38 32 B4
40 FF 8F 40 00 00 6E 00 00 00 00 2C 18 38 32 B4
41 FF 8F 40 00 00 6E 2C 00 00 00 2C 18 38 32 B4
3B FF A6 00 00 00 6E 58 00 00 00 2C 18 38 FD B8
04 FF A6 48 00 00 6E 84 00 00 0A 14 FB 8D FD B8
3C FF A6 00 00 00 78 98 00 00 00 2C 18 38 FD B8

0A FF FF FF
11 FF 50 60 00 00 08 04 00 00 4E 20 9A 34 50 50
10 FF 50 70 00 00 56 24 00 00 4E 20 9A 34 FB E0
11 FF 50 70 00 00 A4 44 00 00 4E 20 9A 34 FB E0

07 FF FF FF
2C FF 68 B4 00 00 08 04 00 00 81 F0 12 34 38 24
2E FF 68 B4 00 00 89 F4 00 00 1E 2A 12 34 38 24
2F FF 68 B4 00 00 A8 1E 00 00 10 3E 12 34 38 24
2D FF D9 B0 00 00 B8 5C 00 00 81 F0 12 34 FD C8
2E FF D9 B0 00 01 3A 4C 00 00 1E 2A 12 34 FD C8
2F FF D9 B0 00 01 58 76 00 00 10 3E 12 34 FD C8

09 FF FF FF
0E FF 51 98 00 00 08 04 00 00 4E 20 27 3F 00 00
0F FF 51 A8 00 00 56 24 00 00 4E 20 1B ED FB E0

TDS 3000
12 FF AE 60 00 01 9B 3C 00 00 00 09 14 09 FD B8
12 FF 00 00 00 00 08 04 00 00 00 09 14 09 00 00

pass-cpu
38 FF 8F 40 00 00 6C CC 00 00 00 2C 18 38 32 B4
39 FF 8F 40 00 00 6C F8 00 00 00 2C 18 38 32 B4

38 FF A6 00 00 00 4E CC 00 00 00 2C 18 38 D2 EC
39 FF A6 00 00 00 4E F8 00 00 00 2C 18 38 D2 EC
3A FF A6 00 00 00 4F 24 00 00 00 2C 18 38 D2 EC
3B FF A6 00 00 00 4F 50 00 00 00 2C 18 38 D2 EC

41 FF A6 10 00 00 6E E4 00 00 00 2C 18 38 FB C0
