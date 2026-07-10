import struct
from .console import warning
from .uncompress import unlzw

def splitlzw(data_chunk, filenames):
    name_index = 0
    invalid_index = 0
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
            warning(
                f"LZW chunk at 0x{start_offset:08X}..0x{end_offset:08X} "
                f"could not be unpacked: {e}"
            )
            output = None

        if output is None:
            name = f"invalid_{invalid_index:02d}"
            invalid_index += 1
        else:
            name = filenames[name_index] if name_index < len(filenames) else f"buffer_{name_index}"
            name_index += 1
        files.append({
            "name": name,
            'compressed': buffer,
            'decompressed': output
        })
        start_offset = offset
        offset += 4

    return files
