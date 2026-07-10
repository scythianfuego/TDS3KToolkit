# TDS3000 bootloader behavior

The tools use ROM file offsets. The bootloader runs on an MPC860 with physical
addressing and maps the 4 MiB flash at
`0xFFC00000..0xFFFFFFFF`, so bootloader flash addresses are file offsets plus
`0xFFC00000`.

## Header and descriptors

The first `0x20` bytes of flash are Tek metadata and dispBmp asset pointers.
They are not PowerPC vector code.

The image descriptors start at file offset `0x20`:

```c
struct HeaderLine {
    uint32 baseAddress;
    uint32 size;
    uint32 checksum;
    uint32 flags;      // 1 = compressed
};
```

Known locations in v3.15/v3.41 ROMs:

```text
+0x20  boot image descriptor, base +0x100
+0x30  main image descriptor pointer/base, normally +0x40000
+0x40  decompressor descriptor, source +0x3E43C, size 0x1004
+0x50  recovery image descriptor pointer/base, normally +0x4000
```

The code at `+0x100` is the reset entry. It jumps into the rest of the
bootloader near `+0xB00` after early setup.

## Compressed main image

If the main image header flag is non-zero, the bootloader uses the compressed
path:

1. It checks checksums and runs hardware tests.
2. It copies `0x1004` bytes from file offset `+0x3E43C` to decompressor RAM.
3. It sets up the decompressor stack and mode argument.
4. It branches to the decompressor RAM copy.

The decompressor does the final jump into the unpacked image. Main and updater
firmware load low in DRAM because the first RAM pages are used for VxWorks
vectors and early state.

## Uncompressed main image

If the main image header flag at file offset `+0x4000C` is zero, the
bootloader branches directly to:

```text
image_header_word0 + 0x10
```

For a normal main image header pointing at `+0x40000`, the direct entry is
`+0x40010` in the flash image. This path does not use the decompressor's RAM
output layout.

## Recovery image

The recovery path is like the compressed main-image path, but it uses the
recovery descriptor and image at `+0x4000`. Breaking the main firmware checksum
is enough to make the scope boot recovery.

## dispBmp display setup

Before handoff, the bootloader uses the dispBmp asset block in the final flash
sector:

- `+0x3E0000..+0x3E003F`: 16 RGB444 palette words copied to the display palette register area.
- `+0x3E0040`: RLE pair-byte count for the boot splash.
- `+0x3E0044...`: count/value byte pairs expanded to the packed 4bpp display
  framebuffer.

The first `0x20` bytes of the ROM also point at later dispBmp RLE assets used
by the updater. See [boot splash assets](splash.md).
