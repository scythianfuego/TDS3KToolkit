# TDS3000 Toolkit

Scripts here work with Tektronix TDS 3000 series file formats.
It's a work in progress, not a complete toolset, but provides a framework
for creating your own scripts with useful examples included.

No files authored or published by Tektronix are distributed in this
repository. In particular, it contains no ROM images, firmware archives,
manuals, locale resources, graphics, device-specific calibration dumps, or
extracted device logs. Users must supply their own input files.

The included schemas, format documentation, and default calibration references
are independently reconstructed descriptions of data structures and functional
values. They are provided to support inspection, interoperability, preservation,
and repair of equipment owned or otherwise lawfully handled by the user.

## License and responsibility

The toolkit is released under the [MIT License](LICENSE), except for source
files that carry their own license notice. In particular,
`teklib/uncompress.py` retains the notice for the work from which it was
adapted.

This software is provided without warranty or support. Modifying or flashing
firmware can make equipment unusable, erase calibration data, or cause other
damage. You are responsible for checking all output, keeping recoverable
backups, and deciding whether it is safe to use.

You are also responsible for ensuring that your use is lawful where you act.
Use the toolkit only with hardware and software you own or control, when you
have the owner's permission, or when you otherwise have a legal right to
inspect, repair, modify, copy, or redistribute it. Do not assume that a
permission or legal exception available in the author's jurisdiction also
applies in yours.

The MIT License covers only the original work contributed to this repository.
It does not grant rights to firmware, documentation, trademarks, or other
third-party material supplied by users. Tool output may contain material copied
or transformed from user-supplied input; that material is not relicensed under
MIT by this project.

This is an independent project and is not affiliated with or endorsed by
Tektronix. Tektronix names and marks are used only to identify compatible
equipment and belong to their respective owners.

## Data formats

For a better understanding of oscilloscope data formats, refer to the following documents:

- [ROM and floppy disks](docs/rom.md)
- [Bootloader](docs/bootloader.md)
- [Flash Filesystem](docs/filesystem.md)
- [Boot splash assets](docs/splash.md)

## Installation

This requires Python 3.9 or newer. Install the one dependency, then run the
scripts directly:

```bash
python -m pip install -r requirements.txt
```

## Usage

> [!WARNING]
> Make a full ROM and NVRAM backup before you do any modifications to existing
> oscilloscope software, even if it looks completely broken. Check that backup
> data is not zero and not garbage. Factory calibration data and some data from
> the filesystem are specific to the individual device.

In order to create less clutter, example scripts are using tar archive as an output.

- unpack_fw.py

  This script takes a zip archive with oscilloscope software
  (eg.: tds3000_3.41_063354011.zip) and extracts useful bits.

- verify_rom.py

  This script checks consistency of ROM memory dump in order to detect data corruption.

- unpack_rom.py

  This script takes a ROM memory dump and splits it into sections.
  Packable files are written at the tar root. Decompressed LZW helpers are
  written under `views/` and are not packed back. The project does not
  recompress them because the output would not be byte-identical to Tek's
  original stream.

- ftlfs.py

  This script extracts and rebuilds the flash filesystem inside a ROM dump or
  standalone `filesystem.bin`.

- unpack_tds3000c_fw.py

  This script extracts the firmware, bootstrap, and locale blocks from a
  TDS3000C firmware ZIP.

- extract_boot_splash.py

  This script extracts boot/update screen images from a full ROM dump or from
  the 128 KiB `dispbmp.bin` asset block.

- pack_boot_splash.py

  This script packs a 4bpp indexed PNG back into one Tek boot-splash RLE block.
  Tek's original RLE streams may contain extra tail bytes, so packed blocks are
  intended to be readable by the scope, not byte-identical to Tek output.

- pack_rom.py

  This script takes section data from a tar archive and creates a complete
  4 MB ROM image with updated checksums.

  Note that in general you cannot use filesystem and/or factory calibration data
  from another device and assume it will work. The scope may fail its power-on
  self-test or calibration.

## Debug hardware and software

TODO: add simple BDM kicad board.
Please refer to Sicco BDM board for now (link eevblog).

## API

TBD.
