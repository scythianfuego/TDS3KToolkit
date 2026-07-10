# TDS3000 boot splash assets

The final 128 KiB flash sector at ROM file offset `+0x3E0000..+0x3FFFFF`
contains dispBmp display/update UI assets. In archives this block is
`dispbmp.bin`. The bootloader sees the same flash range by adding its
`0xFFC00000` flash mapping base.

This area is not factory calibration data.

## Palette

The first `0x40` bytes are 16 big-endian palette words. The low 12 bits are
RGB444:

```text
0x0000  16 * u32 palette words
```

The bootloader copies those words to the display palette/LUT register area.

## Framebuffer RLE

Framebuffer assets are run-length encoded byte pairs:

```text
u32 pair_byte_count
repeat pair_byte_count / 2 times:
    u8 count
    u8 value
```

The expanded framebuffer is packed 4bpp, 640 x 480 pixels. Each byte holds two
palette indexes: high nibble first, then low nibble. A visible framebuffer is
`640 * 480 / 2 = 0x25800` bytes.

Known 3.15/3.41 asset count-word file offsets:

```text
+0x3E0040  Tektronix boot splash
+0x3EA074  firmware upgrade completed
+0x3EBBDC  insert disk 1
+0x3EEA4C  problem loading firmware
+0x3F4420  replace firmware warning
+0x3F92E4  insert disk 2
```

The extractor writes one indexed-color 4bpp PNG per block, plus
`palette.txt` and `palette.png`:

```bash
python extract_boot_splash.py roms/tekrom341.bin -o /tmp/boot_splash
```

One PNG can be packed back into a count-prefixed Tek RLE block:

```bash
python pack_boot_splash.py /tmp/boot_splash/block_00_splash.png /tmp/block_00.bin
```

Packing needs a non-interlaced indexed PNG with 4 bits per pixel. The PNG
scanlines use the same high-nibble-first pixel order as the scope framebuffer
bytes.

The PNG is the visible framebuffer only. Some Tek-produced ROM streams expand
past `640 * 480 / 2` bytes or overlap the following count word by a small
amount. The extractor prints the extra tail size and the gap to the next block
on screen. These values describe the source stream and are not needed to use
the PNG. The packer does not try to make the original stream byte for byte.
