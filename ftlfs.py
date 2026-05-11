import argparse
import struct
import sys

from teklib.console import error, success
from teklib.ftlfs import FS_SIZE, ROM_FS_OFFSET, extract_files, pack_filesystem


def write_packed_output(fs, output, rom_template=None):
    if rom_template is None:
        open(output, "wb").write(fs)
        success(f"wrote filesystem image to {output}")
        return

    rom = bytearray(open(rom_template, "rb").read())
    if len(rom) < ROM_FS_OFFSET + FS_SIZE:
        raise ValueError(f"{rom_template}: too short for filesystem replacement")
    rom[ROM_FS_OFFSET:ROM_FS_OFFSET + FS_SIZE] = fs
    open(output, "wb").write(rom)
    success(f"wrote ROM image to {output}")


def main(argv):
    parser = argparse.ArgumentParser(description="Extract and rebuild TDS3000 FTLFS")
    sub = parser.add_subparsers(dest="cmd", required=True)

    extract = sub.add_parser("extract")
    extract.add_argument("image")
    extract.add_argument("out_dir")
    extract.add_argument("--fs-only", action="store_true")

    pack = sub.add_parser("pack")
    pack.add_argument("extract_dir")
    pack.add_argument("output")
    pack.add_argument("--rom-template")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "extract":
            extract_files(args.image, args.out_dir, args.fs_only)
        else:
            write_packed_output(
                pack_filesystem(args.extract_dir),
                args.output,
                args.rom_template,
            )
        return 0
    except (OSError, ValueError, struct.error) as exc:
        error(f"ftlfs: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
