# TDS3000 Bootloader behaviour

TODO: describe code behaviour from dissassembly


compressed/uncompressed image selection:

ROM:FFC00B50                 bne       isCompressed  # flag = 1 -> code is compressed, decompress
ROM:FFC00B50                                         # otherwise load as is
ROM:FFC00B50 #cdx: Direct path: r7 = image_header[0] + 0x10. If FFC40000 contains FFC40000,
ROM:FFC00B50 #cdx: the direct entry is FFC40010. This is only used when image_header[0xC] == 0.

BB0 #cdx: Compressed path initially sets r7=FFC40010 and r8=image_header[4] for logging.
ROM:FFC00BB0 #cdx: Those registers are later reused for copying the decompressor, so the decompressor probably
ROM:FFC00BB0 #cdx: re-reads the image header or uses known Flash addresses rather than receiving r7/r8 intact.

ROM:FFC00BD4 #cdx: Recovery path mirrors the compressed image path but uses descriptor/image at FFC04000.


C00C48 #cdx: Relocate decompressor from Flash FFC3E43C to DRAM 00600000, length 0x1004 bytes.
ROM:FFC00C48 #cdx: Because CS3 maps 00000000-007FFFFF DRAM, 00600000 is valid RAM at this point.
