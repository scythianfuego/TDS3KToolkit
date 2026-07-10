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
device-specific calibration backups, and `ftlfs.py` does not use them.
Each filename states the record key and data structure name.
