import struct
import sys
from pathlib import Path

def decode_string_table(input_file, output_file):
    with open(input_file, 'rb') as f:
        data = f.read()

    # Read offsets from start of file until we hit zero
    pos = 0
    offsets = []
    while pos < len(data):
      offset = struct.unpack('>I', data[pos:pos+4])[0]
      offsets.append(offset)
      pos += 4
      if offset == 0:
        string_data_start = pos
        break
    else:
      raise ValueError("Could not find string table end marker (zero offset)")


    # Process strings
    results = []
    for offset in reversed(offsets):
        str_pos = string_data_start + offset
        # Read until null terminator or end of file
        end_pos = str_pos
        while end_pos < len(data) and data[end_pos] != 0:
            end_pos += 1

        string_bytes = data[str_pos:end_pos]
        # Check alignment of the next string
        # if (end_pos + 1) % 4 != 0:
        #     padding = 4 - ((end_pos + 1) % 4)
        #     print(f"Warning: String at offset 0x{offset:08x} is not 4-byte aligned")

        # Convert to string, escape non-printable characters
        string = ''
        i = 0
        while i < len(string_bytes):
            # Check if string starts with 0x01
            if i == 0 and string_bytes[0] == 0x01:
              # Output all bytes as hex
              while i < len(string_bytes):
                string += f'\\x{string_bytes[i]:02X}'
                i += 1
              continue

            b = string_bytes[i]
            if b == 0x1b and i + 1 < len(string_bytes):  # ESC sequence
              next_byte = string_bytes[i + 1]
              string += f'\\e\\x{next_byte:02X}'
              i += 2
              continue
            elif 32 <= b <= 126:  # printable ASCII
              string += chr(b)
            elif b == 0x07:  # \a (bell)
              string += '\\a'
            elif b == 0x09:  # \t (tab)
              string += '\\t'
            elif b == 0x0A:  # \n (newline)
              string += '\\n'
            elif b > 0xA0 and b < 0xFF:  # extended ASCII (ISO-8859-1)
              string += bytes([b]).decode('iso-8859-1')
            else:  # other non-printable characters
              string += f'\\x{b:02X}'
            i += 1

        results.append((offset, string))

    # Write output
    with open(output_file, 'w') as f:
        for i, (offset, string) in enumerate(results):
            f.write(f'{i:4d}\t0x{offset:04x}\t{string}\n')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} input_file output_file")
        sys.exit(1)

    decode_string_table(sys.argv[1], sys.argv[2])
