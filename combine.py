import json
import sys

def parse_hex(value):
    if isinstance(value, str) and value.startswith("0x"):
        return int(value, 16)
    return value

if len(sys.argv) < 2:
    print("Usage: python combine.py <json_file>")
    sys.exit(1)

json_file_path = sys.argv[1]

with open(json_file_path, "r") as json_file:
    file_sets = json.load(json_file)

def extract_and_join(file_sets):
    for file_set in file_sets:
        with open(file_set["output"], "wb") as out_f:
            buffer = bytearray()
            for file in file_set["files"]:
                if "path" in file:
                    with open(file["path"], "rb") as f:
                        start = parse_hex(file["start"])
                        end = file["end"]
                        f.seek(start)
                        if end == "eof":
                            data = f.read()
                        else:
                            end = parse_hex(end)
                            data = f.read(end - start)
                        buffer.extend(data)
                elif "size" in file:
                    size = parse_hex(file["size"])
                    fill_byte = parse_hex(file.get("fill_byte", "0x00"))
                    if len(buffer) < size:
                        buffer.extend(bytes([fill_byte]) * (size - len(buffer)))
            out_f.write(buffer)

extract_and_join(file_sets)
