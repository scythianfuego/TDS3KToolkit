import binascii
import struct
import zlib


FULL_ROM_SIZE = 0x400000
FINAL_SECTOR_OFFSET = 0x3E0000
FINAL_SECTOR_SIZE = 0x20000
FLASH_BASE = 0xFFC00000
FINAL_SECTOR_FLASH_BASE = 0xFFFE0000

PALETTE_WORDS = 16
RLE_DATA_OFFSET = 0x44
KNOWN_RLE_COUNT_OFFSETS = [0x40, 0xA074, 0xBBDC, 0xEA4C, 0x14420, 0x192E4]

SPLASH_WIDTH = 640
SPLASH_HEIGHT = 480


def detect_splash_offset(data, requested="auto"):
    if requested != "auto":
        return int(requested, 0)

    if len(data) >= FULL_ROM_SIZE:
        return FINAL_SECTOR_OFFSET

    if len(data) >= FINAL_SECTOR_SIZE:
        return 0

    raise ValueError("input is smaller than a dispBmp image")


def rgb12_to_rgb8(word):
    value = word & 0x0FFF
    red = (value >> 8) & 0x0F
    green = (value >> 4) & 0x0F
    blue = value & 0x0F
    return red * 17, green * 17, blue * 17


def decode_rle(pairs):
    if len(pairs) % 2:
        raise ValueError(f"RLE pair byte count is odd: {len(pairs)}")

    output = bytearray()
    for i in range(0, len(pairs), 2):
        count = pairs[i]
        value = pairs[i + 1]
        output.extend([value] * count)
    return bytes(output)


def unpack_4bpp(framebuffer):
    pixels = bytearray(len(framebuffer) * 2)
    j = 0
    for byte in framebuffer:
        pixels[j] = byte >> 4
        pixels[j + 1] = byte & 0x0F
        j += 2
    return bytes(pixels)


def candidate_count_offsets(data, offset, scan_end):
    candidates = set()

    if len(data) >= FULL_ROM_SIZE:
        for pos in range(0, 0x20, 4):
            word = struct.unpack_from(">I", data, pos)[0]
            sector_end = FINAL_SECTOR_FLASH_BASE + FINAL_SECTOR_SIZE
            if FINAL_SECTOR_FLASH_BASE <= word < sector_end:
                candidates.add(word - FLASH_BASE)

    for relative in KNOWN_RLE_COUNT_OFFSETS:
        count_offset = offset + relative
        if count_offset + 4 <= scan_end:
            candidates.add(count_offset)

    return sorted(candidates)


def read_palette(data, offset):
    words = []
    palette = []
    for i in range(PALETTE_WORDS):
        word = struct.unpack_from(">I", data, offset + i * 4)[0]
        words.append(word)
        palette.append(rgb12_to_rgb8(word))
    return words, palette


def read_rle_blocks(data, offset, width=SPLASH_WIDTH, height=SPLASH_HEIGHT):
    if len(data) < offset + RLE_DATA_OFFSET:
        raise ValueError(f"input too short for splash data at offset 0x{offset:X}")

    scan_end = offset + FINAL_SECTOR_SIZE
    if scan_end > len(data):
        scan_end = len(data)

    framebuffer_size = width * height // 2
    blocks = []

    for count_offset in candidate_count_offsets(data, offset, scan_end):
        pair_byte_count = struct.unpack_from(">I", data, count_offset)[0]
        rle_start = count_offset + 4
        rle_end = rle_start + pair_byte_count

        if pair_byte_count == 0 or pair_byte_count % 2:
            continue

        if rle_end > scan_end:
            continue

        pairs = data[rle_start:rle_end]
        expanded = decode_rle(pairs)
        if len(expanded) < framebuffer_size:
            continue

        blocks.append({
            "index": len(blocks),
            "count_offset": count_offset,
            "rle_data_offset": rle_start,
            "rle_end_offset": rle_end,
            "pair_byte_count": pair_byte_count,
            "pairs": pairs,
            "expanded": expanded,
        })

    if not blocks:
        raise ValueError(f"no framebuffer-sized RLE blocks found at offset 0x{offset:X}")

    for i, block in enumerate(blocks):
        if i + 1 < len(blocks):
            block["source_gap_to_next_count_offset"] = (
                blocks[i + 1]["count_offset"] - block["rle_end_offset"]
            )
        else:
            block["source_gap_to_sector_end"] = scan_end - block["rle_end_offset"]

    return blocks


def png_chunk(kind, payload):
    crc = binascii.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def encode_rle(data):
    output = bytearray()
    if not data:
        return bytes(output)

    count = 1
    value = data[0]
    for byte in data[1:]:
        if byte == value and count < 255:
            count += 1
            continue

        output.extend([count, value])
        count = 1
        value = byte

    output.extend([count, value])
    return bytes(output)


def pack_rle_block(data):
    pairs = encode_rle(data)
    return struct.pack(">I", len(pairs)) + pairs


def write_png(path, width, height, bit_depth, color_type, rows, palette=None):
    header = struct.pack(">IIBBBBB", width, height, bit_depth, color_type, 0, 0, 0)
    data = PNG_SIGNATURE + png_chunk(b"IHDR", header)
    if palette is not None:
        plte = bytearray()
        for red, green, blue in palette:
            plte.extend([red, green, blue])
        data += png_chunk(b"PLTE", bytes(plte))
    data += png_chunk(b"IDAT", zlib.compress(rows, level=9))
    data += png_chunk(b"IEND", b"")
    path.write_bytes(data)


def write_indexed_png(path, framebuffer, palette, width, height):
    row_size = (width + 1) // 2
    rows = bytearray()
    for y in range(height):
        start = y * row_size
        rows.append(0)
        rows.extend(framebuffer[start:start + row_size])
    write_png(path, width, height, 4, 3, bytes(rows), palette=palette)


def read_png_chunks(data):
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("PNG signature not found")

    pos = 8
    chunks = []
    while pos + 8 <= len(data):
        size = struct.unpack_from(">I", data, pos)[0]
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + size]
        chunks.append((kind, payload))
        pos += 12 + size
        if kind == b"IEND":
            break
    return chunks


def read_indexed_png_4bpp(data):
    width = None
    height = None
    palette = None
    compressed = bytearray()

    for kind, payload in read_png_chunks(data):
        if kind == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_type, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if bit_depth != 4 or color_type != 3:
                raise ValueError("input PNG must be indexed color, 4 bits per pixel")
            if compression != 0 or filter_type != 0 or interlace != 0:
                raise ValueError("input PNG must be non-interlaced with standard PNG compression/filter")
        elif kind == b"PLTE":
            if len(payload) % 3:
                raise ValueError("PNG palette length is not divisible by 3")
            palette = [
                tuple(payload[i:i + 3])
                for i in range(0, len(payload), 3)
            ]
        elif kind == b"IDAT":
            compressed.extend(payload)

    if width is None or height is None:
        raise ValueError("PNG IHDR not found")
    if palette is None or len(palette) > 16:
        raise ValueError("input PNG must have a 16-color-or-smaller palette")

    rows = zlib.decompress(bytes(compressed))
    row_size = (width + 1) // 2
    expected = (row_size + 1) * height
    if len(rows) != expected:
        raise ValueError("PNG data size does not match 4bpp dimensions")

    framebuffer = bytearray()
    pos = 0
    for _y in range(height):
        filter_byte = rows[pos]
        if filter_byte != 0:
            raise ValueError("input PNG must use filter type 0 on every row")
        pos += 1
        framebuffer.extend(rows[pos:pos + row_size])
        pos += row_size

    return width, height, palette, bytes(framebuffer)


def write_palette_outputs(out_dir, words, palette):
    lines = ["index word rgb_hex r g b"]
    for i, (word, color) in enumerate(zip(words, palette)):
        red, green, blue = color
        lines.append(
            f"{i:02d} 0x{word:08X} "
            f"#{red:02X}{green:02X}{blue:02X} "
            f"{red:3d} {green:3d} {blue:3d}"
        )
    out_dir.joinpath("palette.txt").write_text(
        "\n".join(lines) + "\n", encoding="ascii"
    )

    rows = bytearray()
    for _y in range(32):
        rows.append(0)
        for color in palette:
            for _x in range(32):
                rows.extend(color)
    write_png(out_dir / "palette.png", 512, 32, 8, 2, bytes(rows))


def write_block_outputs(out_dir, block, palette, width, height):
    name = f"block_{block['index']:02d}"
    framebuffer_size = width * height // 2
    framebuffer = block["expanded"][:framebuffer_size]
    tail = block["expanded"][framebuffer_size:]
    output = out_dir / f"{name}_splash.png"

    write_indexed_png(output, framebuffer, palette, width, height)

    if "source_gap_to_next_count_offset" in block:
        gap_name = "gap to next block"
        gap_size = block["source_gap_to_next_count_offset"]
    else:
        gap_name = "gap to sector end"
        gap_size = block["source_gap_to_sector_end"]

    print(f"block {block['index']:02d}    {output}")
    print(f"  count word  0x{block['count_offset']:X}")
    print(f"  RLE bytes   {block['pair_byte_count']}")
    print(f"  tail bytes  {len(tail)}")
    print(f"  {gap_name:<12} {gap_size}")


def extract_splash(
    data,
    out_dir,
    offset="auto",
    width=SPLASH_WIDTH,
    height=SPLASH_HEIGHT,
    input_name=None,
):
    offset = detect_splash_offset(data, offset)
    out_dir.mkdir(parents=True, exist_ok=True)

    palette_words, palette = read_palette(data, offset)
    blocks = read_rle_blocks(data, offset, width, height)

    write_palette_outputs(out_dir, palette_words, palette)

    if input_name is not None:
        print(f"input       {input_name}")
    print(f"dispBmp     0x{offset:X}")
    print(f"size        {width} x {height}")
    print(f"palette     {out_dir / 'palette.txt'}")

    for block in blocks:
        write_block_outputs(out_dir, block, palette, width, height)
