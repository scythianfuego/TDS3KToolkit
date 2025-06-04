import struct
import sys

def checksum(data: bytes) -> int:
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
        print("Usage: python checksum.py <input>")
        sys.exit(1)

    if len(sys.argv) == 2:
        input_file = sys.argv[1]
        with open(input_file, 'rb') as f:
          data = f.read()
          sum = checksum(data);
          print(f"{sum:08X}")