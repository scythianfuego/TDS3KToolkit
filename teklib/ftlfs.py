import struct
import csv
import re

def parse_records(data, base_offset=0):
    record_size = 16
    max_records = 128
    records = []
    file_data = {}

    # Read block header
    block_header = data[:4]
    block_id, _, _ = struct.unpack(">BBH", block_header)

    count = min(len(data), record_size * max_records)
    for i in range(0, count, record_size):
        record = data[i+4:i + record_size+4]
        if len(record) < record_size:
            break

        # Stop reading if the record is filled with 0xFF (clean flash)
        if record == b'\xFF' * record_size:
            break

        record_number, unk0, unk1, relative_offset, size, filename, unk3 = struct.unpack(">BBH I I H H", record)

        if relative_offset == 0 or size == 0:
            continue  # Likely an invalid or unused record

        absolute_offset = base_offset + relative_offset
        unique_id = f"{block_id:02X}_{i//record_size:02X}"  # Unique per block and index

        file_content = data[relative_offset:relative_offset + size]
        printable_content = "".join(chr(b) for b in file_content if re.match(r'[A-Za-z0-9]', chr(b)))
        print(printable_content)

        records.append({
            "unique_id": unique_id,
            "block_id": block_id,
            "record_number": record_number,
            "unk0": unk0, # always 0xff
            "unk1": unk1,
            "relative_offset": relative_offset,
            "absolute_offset": absolute_offset,
            "size": size,
            "filename": filename,
            "unk3": unk3,
            "printable_content": printable_content
        })
        #debug
        print(f"record {record.hex()}")
        print(f"Record {unique_id}: {filename:04X} @ {relative_offset:08X}={absolute_offset:08X} size {size:08X}")

        file_data[unique_id] = file_content

        #start = file_content[:8].hex()
        #end = file_content[-8:].hex()
        #print(f"Data: {start}...{end}")

    return records, file_data


def extract_files(data, output_folder, base_offsets):
    import os
    os.makedirs(output_folder, exist_ok=True)

    all_records = []
    all_file_data = {}

    for base_offset in base_offsets:
        records, file_data = parse_records(data[base_offset:], base_offset)
        all_records.extend(records)
        all_file_data.update(file_data)

    for record in all_records:
        unique_id = record['unique_id']
        file = record['filename']
        filename = f"{output_folder}/{file}_{unique_id}.bin"

        with open(filename, "wb") as f:
            f.write(all_file_data.get(unique_id, b""))

        print(f"Extracted: {filename}")

    # Export all records to CSV
    csv_filename = f"{output_folder}/records.csv"
    with open(csv_filename, "w", newline="") as csvfile:
        fieldnames = ["unique_id", "block_id", "record_number", "unk0", "unk1", "relative_offset", "absolute_offset", "size", "filename", "unk3", "printable_content"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)
    print(f"Exported records to {csv_filename}")

# Example usage
with open("roms/tekrom341.bin", "rb") as f:
    data = f.read()
    base_offsets = [0x280000, 0x2A0000, 0x2C0000, 0x2E0000, 0x300000, 0x320000, 0x340000, 0x360000, 0x380000, 0x3C0000]
    extract_files(data, "ftlfs", base_offsets)
