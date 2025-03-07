# TDS3000 Toolkit

Scripts here work with Tektronix TDS 3000 series file formats.
It's a work in progress, not a complete toolset, but provides a framework
for creating your own scripts with useful examples included.

## Data formats

For a better understanding of oscilloscope data formats, refer to the following documents:

- [ROM and floppy disks](docs/bootloader.md)
- [Bootloader](docs/bootloader.md)
- [Flash Filesystem](docs/bootloader.md)

## Installation

This requires a working python 3 environment.  
Clone the repository and run scripts directly.

## Usage

> [!WARNING]
> Make a full ROM and NVRAM backup before you do any modifications to existing
> oscilloscope software, even if it looks completely broken. Check that backup
> data is not zero and not garbage. Factory calibration data and some data from
> filesystem is specific for individual device.

In order to create less clutter, example scripts are using tar archive as an output.

- unpack_fw.py

  This script takes a zip archive with oscilloscope software
  (eg.: tds3000_3.41_063354011.zip) and extracts useful bits.

- verify_rom.py

  This script checks consistency of ROM memory dump in order to detect data corruption.

- unpack_rom.py

  This script takes ROM memory dump and splits it into sections

- pack_rom.py

  This script takes section data (in a tar achive), and creates a complete 4MB ROM dump
  with correct checksums to write into oscilloscope.

  Note that in general you cannot use filesystem and/or factory calibration data
  from other device and assume it would work (although for some combination
  of software version and hardware it does, prefer older versions, they're doing less checks).
  Scope may not pass power-on self test correctly and/or power on calibration.

## Debug hardware and software

TODO: add simple BDM kicad board.
Please refer to Sicco BDM board for now (link eevblog).

## API

TBD.
