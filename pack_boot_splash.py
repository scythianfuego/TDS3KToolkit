import argparse
import struct
import sys
import zlib
from pathlib import Path

from teklib.console import error
from teklib.splash import pack_rle_block, read_indexed_png_4bpp


def pack_boot_splash(input_png, output_block):
    width, height, palette, framebuffer = read_indexed_png_4bpp(input_png.read_bytes())
    output_block.write_bytes(pack_rle_block(framebuffer))

    print(f"input        {input_png}")
    print(f"size         {width} x {height}")
    print(f"palette      {len(palette)} colors")
    print(f"framebuffer  {len(framebuffer)} bytes")
    print(f"output       {output_block}")


def main(argv):
    parser = argparse.ArgumentParser(description="Pack one TDS3000 boot splash RLE block.")
    parser.add_argument("input_png", type=Path, help="4bpp indexed PNG image")
    parser.add_argument("output_block", type=Path, help="output RLE block")
    args = parser.parse_args(argv)

    try:
        pack_boot_splash(args.input_png, args.output_block)
        return 0
    except (OSError, ValueError, struct.error, zlib.error) as e:
        error(f"pack_boot_splash.py: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
