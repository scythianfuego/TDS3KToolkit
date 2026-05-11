"""Extract and rebuild the TDS3000 flash filesystem."""

import json
import os
import struct
from os.path import dirname, join

from teklib import ftlfs_decode
from teklib.console import success


ROM_FS_OFFSET = 0x280000
FS_SIZE = 0x160000
SEGMENT_SIZE = 0x20000
DATA_START = 0x804
RECORD_BASE = 0x04
RECORD_SIZE = 0x10
MAX_RECORDS = 0x80
STRUCTS = join(dirname(__file__), "ftlfs_structs")
PHYSICAL_SEGMENTS = range(ROM_FS_OFFSET, ROM_FS_OFFSET + FS_SIZE, SEGMENT_SIZE)

KEY_LOGICAL_SEGMENTS = {
    int(k, 16): v
    for k, v in json.load(open(join(STRUCTS, "key_logical_segments.json"))).items()
}
LOGICAL_SEGMENT_WORDS = {
    int(k, 16): [int(x, 16) for x in v]
    for k, v in json.load(open(join(STRUCTS, "logical_segment_words.json"))).items()
}


def checksum16(data):
    return (sum(data) + 0x1234) & 0xFFFF


def load_fs(path, fs_only=False, fs_offset=ROM_FS_OFFSET):
    data = open(path, "rb").read()
    if fs_only or len(data) == FS_SIZE:
        if len(data) < FS_SIZE:
            raise ValueError(f"{path}: filesystem image is shorter than 0x{FS_SIZE:X}")

        return data[:FS_SIZE]

    if len(data) < fs_offset + FS_SIZE:
        raise ValueError(f"{path}: ROM is too short for filesystem")

    return data[fs_offset:fs_offset + FS_SIZE]


def parse_records(fs):
    if len(fs) != FS_SIZE:
        raise ValueError(f"filesystem must be exactly 0x{FS_SIZE:X} bytes")

    records = []
    seen = set()

    for physical in PHYSICAL_SEGMENTS:
        base = physical - ROM_FS_OFFSET
        segment = fs[base:base + SEGMENT_SIZE]
        logical = segment[0]
        if logical == 0xFF:
            continue

        if logical in seen:
            raise ValueError(f"logical segment 0x{logical:02X} appears more than once")

        seen.add(logical)

        live = {}
        for slot in range(MAX_RECORDS):
            pos = RECORD_BASE + slot * RECORD_SIZE
            raw = segment[pos:pos + RECORD_SIZE]
            if raw == b"\xFF" * RECORD_SIZE:
                continue
            key, _, _, offset, size, stored, _ = struct.unpack(">BBHIIHH", raw)
            if offset == 0xFFFFFFFF and size == 0xFFFFFFFF:
                continue
            expected = KEY_LOGICAL_SEGMENTS.get(key)
            if expected is None:
                raise ValueError(f"key 0x{key:02X}: no logical segment mapping")
            if size == 0 or expected != logical:
                continue
            if offset < DATA_START or offset + size > SEGMENT_SIZE:
                raise ValueError(f"key 0x{key:02X}: payload points outside segment")
            payload = segment[offset:offset + size]
            if checksum16(payload) != stored:
                raise ValueError(f"key 0x{key:02X}: bad checksum")
            live[key] = {"key": key, "size": size, "payload": payload}

        records.extend(live.values())

    return sorted(records, key=lambda r: r["key"])


def record_name(key, ext):
    return f"key_{key:02X}.{ext}"


def record_key(name, ext):
    if not name.startswith("key_") or not name.endswith("." + ext):
        return None
    return int(name[4:6], 16)


def extract_files(image, out_dir, fs_only=False, fs_offset=ROM_FS_OFFSET):
    records = parse_records(load_fs(image, fs_only, fs_offset))
    raw_dir = join(out_dir, "raw")
    decoded_dir = join(out_dir, "decoded")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(decoded_dir, exist_ok=True)

    for record in records:
        key = record["key"]
        payload = record["payload"]
        open(join(raw_dir, record_name(key, "bin")), "wb").write(payload)
        decoded = ftlfs_decode.decode_payload(key, payload)
        if decoded is not None:
            open(join(decoded_dir, record_name(key, "json")), "w").write(
                ftlfs_decode.json_text(decoded)
            )

    success(f"extracted {len(records)} active records to {out_dir}")


def keys_in_dir(path, ext):
    try:
        names = os.listdir(path)
    except OSError:
        return set()
    return {key for key in (record_key(name, ext) for name in names) if key is not None}


def record_payload(extract_dir, key):
    raw_path = join(extract_dir, "raw", record_name(key, "bin"))
    decoded_path = join(extract_dir, "decoded", record_name(key, "json"))
    try:
        data = json.load(open(decoded_path))
        try:
            size = len(open(raw_path, "rb").read())
        except OSError:
            size = None
        return ftlfs_decode.encode_payload(key, data, size)
    except OSError:
        return open(raw_path, "rb").read()


def pack_filesystem(extract_dir):
    fs = bytearray(b"\xFF" * FS_SIZE)
    by_logical = {}
    keys = keys_in_dir(join(extract_dir, "raw"), "bin")
    keys |= keys_in_dir(join(extract_dir, "decoded"), "json")
    for key in keys:
        logical = KEY_LOGICAL_SEGMENTS.get(key)
        if logical is None:
            raise ValueError(f"key 0x{key:02X}: no logical segment mapping")
        by_logical.setdefault(logical, []).append(key)

    for logical in range(1, 0x0B):
        base = (logical - 1) * SEGMENT_SIZE
        fs[base] = logical
        offset = DATA_START
        word1, word2 = LOGICAL_SEGMENT_WORDS[logical]
        for slot, key in enumerate(sorted(by_logical.get(logical, []))):
            payload = record_payload(extract_dir, key)
            end = offset + len(payload)
            if end > SEGMENT_SIZE or slot >= MAX_RECORDS:
                raise ValueError(f"logical segment 0x{logical:02X}: records do not fit")

            record = struct.pack(
                ">BBHIIHH", key, 0xFF, word1, offset, len(payload),
                checksum16(payload), word2,
            )
            pos = base + RECORD_BASE + slot * RECORD_SIZE
            fs[pos:pos + RECORD_SIZE] = record
            fs[base + offset:base + end] = payload
            offset = end

    return bytes(fs)
