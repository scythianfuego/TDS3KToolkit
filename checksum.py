import struct
import sys

def update_file_checksums(input_file: str, output_file: str):
    # Reads ROM sections at specific offsets in the input file,
    # calculates checksums for corresponding data sections, and updates the file.
    section_header_offsets = [0x30] #[0x20, 0x30, 0x40, 0x50]
    section_names = {
        0x20 : "Boot", 0x30: "Code", 0x40: "Decompressor", 0x50: "Recovery"
    }
    header_size = 16  # Each structure consists of four 4-byte fields
    word_size = 4  # Size of each word in bytes
    checksum_mask = 0xFFFFFFFF  # Mask to keep checksum within 32-bit limit

    with open(input_file, 'rb') as f:
        file_data = bytearray(f.read())

    for offset in section_header_offsets:
        # Read structure fields (big-endian)
        base_address, size, old_checksum, flags = struct.unpack('>IIII', file_data[offset:offset + header_size])
        base_address -= 0xFFC00000

        if (base_address == 0x40000):
            base_address += 0x10 # Tek skips compressed code header

        # Read data segment and calculate new checksum
        data = file_data[base_address:base_address + size]
        num_words = len(data) // word_size    # Number of full words
        aligned_size = num_words * word_size  # Aligned size to full words

        # checksum = sum(struct.unpack(f'>{num_words}I', data[:aligned_size]))
        checksum = 0
        for i in range(num_words):
            word = struct.unpack('>I', data[i * word_size: (i + 1) * word_size])[0]
            checksum += word
            accu =  (checksum & 0xFFFFFFFF) + 0x1234
            print(f"{i*4:08x} {word:08x} Accumulated checksum: {accu:#010x}")  # Print accumulator



        checksum += sum(data[aligned_size:])
        checksum += 0x1234  # Add constant offset
        print(f"{checksum:X}")
        checksum &= checksum_mask  # Ensure checksum stays within 32-bit range


        # checksum &= 0xFFFFFFFF

        # Update checksum field in file data
        # file_data[offset + 8:offset + 12] = struct.pack('>I', checksum)
        isCompressed = ", LZW-compressed" if flags == 1 else ""
        name = section_names[offset]
        print(f"{name} at {base_address:08X}{isCompressed}:")
        print(f"   Size {size:08X}   Checksum current {old_checksum:08X} -> {checksum:08X} new")

    # Save modified file data to a new file
    # with open(output_file, 'wb') as f:
    #     f.write(file_data)

def calculate_checksum(data: bytes) -> int:
    chunk_size = 4  # Size of each chunk in bytes
    num_chunks = len(data) // chunk_size # Number of full 4-byte chunks

    # Sum all full 4-byte chunks interpreted as unsigned integers
    full_chunks = struct.unpack(f'>{num_chunks}I', data[:num_chunks * chunk_size])
    checksum = sum(full_chunks)

    # Sum any remaining bytes (less than 4)
    remaining_bytes = data[num_chunks * chunk_size:]
    checksum += sum(remaining_bytes)
    checksum += 0x1234  # Add constant offset
    checksum &= 0xFFFFFFFF
    return checksum


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage:")
        print("   Patch firmware checksum:   python checksum.py <input_file> <output_file>")
        print("   Calculate file checksum:   python checksum.py <input>")
        sys.exit(1)


    if len(sys.argv) == 3:
      input_file = sys.argv[1]
      output_file = sys.argv[2]

      update_file_checksums(input_file, output_file)

    if len(sys.argv) == 2:
        input_file = sys.argv[1]
        with open(input_file, 'rb') as f:
          data = f.read()
          checksum = calculate_checksum(data);
          print(f"{checksum:08X}")