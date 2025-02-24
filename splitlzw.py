import struct
from uncompress import unlzw



def splitlzw(data_chunk, filenames):
    index = 0
    files = []
    start_offset = 0
    offset = 4

    while offset < len(data_chunk):

        while True:
            if offset + 4 > len(data_chunk):
                end_offset = len(data_chunk)
                break

            magic = struct.unpack('>H', data_chunk[offset:offset + 2])[0]
            if magic == 0x1F9D:
                # sanity check - if byte at start_offset - 4 is not 0x00 - ignore this occurence
                # uncompressed size before is always less than 16MB
                if data_chunk[offset-4] == 0:
                    end_offset = offset - 4 # skip last four bytes, they contain unpacked size for next chunk
                    break

            offset += 1

        size = end_offset - start_offset
        buffer = data_chunk[start_offset:end_offset]
        if not buffer:
            break

        #print(f"Found LZW chunk at {start_offset:08X} size {size:08X} {buffer[0:8].hex()}...{buffer[-8:].hex()}")
        try:
            output = unlzw(buffer)
        except Exception as e:
            print(f"Error decompressing chunk at {start_offset:08X}-{end_offset:08x}: {e}")
            output = b''

        name = filenames[index] if index < len(filenames) else f"buffer_{index}"
        index += 1
        files.append({
            "name": name,
            'compressed': buffer,
            'decompressed': output
        })
        start_offset = offset
        offset += 4

    return files
