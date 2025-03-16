import struct
import sys
from pathlib import Path

cyrillic_map = cyrillic_map = {
    0x88: "А", 0x89: "Б", 0x8A: "В", 0x8B: "Г", 0x8C: "Д", 0x8D: "Е",
    0x8E: "Ж", 0x8F: "З", 0x90: "И", 0x91: "Й", 0x92: "К", 0x93: "Л",
    0x94: "М", 0x95: "Н", 0x96: "О", 0x97: "П", 0x98: "Р", 0x99: "С",
    0x9A: "Т", 0x9B: "У", 0x9C: "Ф", 0x9D: "Х", 0x9E: "Ц", 0x9F: "Ч",
    0xA0: "Ш", 0xA1: "Щ", 0xA2: "Ъ", 0xA3: "Ы", 0xA4: "Ь", 0xA5: "Э",
    0xA6: "Ю", 0xA7: "Я",

    0xA8: "а", 0xA9: "б", 0xAA: "в", 0xAB: "г", 0xAC: "д", 0xAD: "е",
    0xAE: "ж", 0xAF: "з", 0xB0: "и", 0xB1: "й", 0xB2: "к", 0xB3: "л",
    0xB4: "м", 0xB5: "н", 0xB6: "о", 0xB7: "п", 0xB8: "р", 0xB9: "с",
    0xBA: "т", 0xBB: "у", 0xBC: "ф", 0xBD: "х", 0xBE: "ц", 0xBF: "ч",
    0xC0: "ш", 0xC1: "щ", 0xC2: "ъ", 0xC3: "ы", 0xC4: "ь", 0xC5: "э",
    0xC6: "ю", 0xC7: "я"
}

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
          b = string_bytes[i]
          if b == 0x1b and i + 1 < len(string_bytes):  # ESC sequence
              next_byte = string_bytes[i + 1]
              string += f'\\e\\x{next_byte:02X}'
              i += 2
              continue
          elif b == 0x01 and i + 2 < len(string_bytes) and string_bytes[i + 1] == 0x07:  # Cyrillic sequence
              lookup_byte = string_bytes[i + 2]
              if lookup_byte in cyrillic_map:
                  string += cyrillic_map[lookup_byte]
              else:
                  string += f'\\x01\\x07\\x{lookup_byte:02X}'
              i += 3
              continue
          elif 32 <= b <= 126:  # printable ASCII
              string += chr(b)
          elif b == 0x07:  # \a (bell)
              string += '\\a'
          elif b == 0x09:  # \t (tab)
              string += '\\t'
          elif b == 0x0A:  # \n (newline)
              string += '\\n'
          # elif b > 0xA0 and b < 0xFF:  # extended ASCII (ISO-8859-1)
          #     string += bytes([b]).decode('iso-8859-1')
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
