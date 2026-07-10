import argparse
import struct
import sys
from pathlib import Path

from teklib.console import error
from teklib.splash import SPLASH_HEIGHT, SPLASH_WIDTH, extract_splash


def main(argv):
    parser = argparse.ArgumentParser(description="Extract TDS3000 boot splash images.")
    parser.add_argument("input", type=Path, help="Full ROM dump or 0x20000-byte dispBmp block")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("boot_splash_out"))
    parser.add_argument("--offset", default="auto", help="dispBmp offset, or auto")
    parser.add_argument("--width", type=int, default=SPLASH_WIDTH)
    parser.add_argument("--height", type=int, default=SPLASH_HEIGHT)
    args = parser.parse_args(argv)

    try:
        data = args.input.read_bytes()
        extract_splash(
            data,
            args.output_dir,
            offset=args.offset,
            width=args.width,
            height=args.height,
            input_name=str(args.input),
        )
        return 0
    except (OSError, ValueError, struct.error) as e:
        error(f"extract_boot_splash.py: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
