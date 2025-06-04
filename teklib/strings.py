import struct
import sys

# File format: a number of 4-byte offsets generally in reverse order,
# ending by a zero offset, offsets are relative to the start of the string data,
# Then there is a series of null-terminated (?) strings, aligned to 4 bytes
# (padded with up to 4 zeroes)

# Some offsets are duplicate.
# Some strings contain null character (or not addressed?).
# It is unclear how strings are addressed in software, table indices
# for same messages seem to vary between locales.

# 1B XX - escape character: color, style, etc.
#   21 - CH1 Yellow
#   22 - CH2 Blue
#   23 - CH3 Magenta
#   24 - CH4 Green
#   25 - Math Red
#   10 - Clear color
# 01 00 XX, 01 01 XX - Korean (Hangul syllables)
# 01 02 XX - Chinese (Simplified)
# 01 03 XX, 01 04 XX - Chinese (Traditional)
# 01 05 XX, 01 06 XX - Japanese (Kanji + Kana)
# 01 07 XX - Russian (Cyrillic alphabet)

cyrillic_charset = {
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


def decode_table(data):

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
      raise ValueError("Could not find string table zero offset")


    # Process strings
    offsets = sorted(set(offsets))  # Sort unique offsets, excluding the final zero
    results = []
    for offset_idx in range(len(offsets)):  # Process all offsets except the last (zero) offset
      offset = offsets[offset_idx]
      if offset_idx + 1 < len(offsets):
        next_offset = offsets[offset_idx + 1]
      else:
        next_offset = len(data) - string_data_start

      str_pos = string_data_start + offset
      end_pos = string_data_start + next_offset
      string_bytes = data[str_pos:end_pos]

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
        elif b == 0x01 and i + 2 < len(string_bytes): # Multibyte character
          b1 = string_bytes[i + 1]
          b2 = string_bytes[i + 2]
          if b1 == 0x07 and b2 in cyrillic_charset:
            string += cyrillic_charset[b2]
          else:
            string += f'\\x01\\x{b1:02X}\\x{b2:02X}' # kr ja ch tw
          i += 3
          continue
        elif 32 <= b <= 126:  # printable ASCII
          string += chr(b)
        elif b == 0x09:  # \t (tab)
          string += '\\t'
        elif b == 0x0D:  # \r (carriage return)
          string += '\\r'
        elif b == 0x0A:  # \n (newline)
          string += '\\n'
        # elif b > 0xA0 and b < 0xFF:  # extended ASCII (ISO-8859-1)
        #   string += bytes([b]).decode('iso-8859-1')
        elif b == 0x00:
          # Null terminator outside of escape sequence, end of string
          # if (len(string_bytes) - i > 4):
          #   position = str_pos + i
          #   print(f"Warning: Null terminator at 0x{position:04X} is not at the end of the string, {len(string_bytes) - i} bytes remaining")
          #   break
          string += ' ';
        else:  # other non-printable characters
          string += f'\\x{b:02X}'

        i += 1

      results.append((offset, string))

    # Write output
    return results

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} input_file output_file")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    with open(input_file, 'rb') as f:
        data = f.read()

    results = decode_table(data)

    with open(output_file, 'w', encoding='utf-8') as f:
        for i, (offset, string) in enumerate(results):
          f.write(f'{i:4d}\t0x{offset:04x}\t{string}\n')