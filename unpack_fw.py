from teklib.process import TekFileProcessor, known_locales
from teklib.console import checksum_message, error, warning
from teklib.strings import decode_table
import sys
import zipfile


def test_checksums(p):
    # disk contents
    checksum_message("fwdisk1.dat  checksum", p.checksum(name="disk1/fwdisk1.dat",  start="0x60"), p.value(name="disk1/fwdisk1.dat", at="0x08") )
    checksum_message("fwdisk2.dat  checksum", p.checksum(name="disk2/fwdisk2.dat",  start="0x60"), p.value(name="disk2/fwdisk2.dat", at="0x08") )
    checksum_message("fwdisk2a.dat checksum", p.checksum(name="disk2/fwdisk2a.dat", start="0x60"), p.value(name="disk2/fwdisk2a.dat",at="0x08") )
    checksum_message("fwdisk3.dat  checksum", p.checksum(name="disk3/fwdisk3.dat",  start="0x60"), p.value(name="disk3/fwdisk3.dat", at="0x08") )
    checksum_message("fwdisk4.dat  checksum", p.checksum(name="disk4/fwdisk4.dat",  start="0x60"), p.value(name="disk4/fwdisk4.dat", at="0x08") )
    #data
    checksum_message("Service firmware checksum ", p.checksum(name="lzw/service.z"), p.value(name="disk1/fwdisk1.dat", at="0x0C") )
    checksum_message("Recovery firmware checksum", p.checksum(name="lzw/recovery.z"), p.value(name="disk2/fwdisk2a.dat", at="0x0C") )
    print("-- The next checksum includes unknown extra files; ignore the mismatch --")
    checksum_message("User firmware checksum", p.checksum(name="lzw/firmware.z"), p.value(name="disk3/fwdisk3.dat", at="0x0C"), 1 )




def unpack_fw(input_file, output_tar):
    disk34_filenames = ["firmware"] + known_locales()

    # 1 korean 5 chinsese 6 taiwanese
    files_to_save = [
        "service.dat", "recovery.dat", "firmware.dat",
        "lzw/service.z", "lzw/recovery.z", "lzw/firmware.z"]

    outputnames = ["lzw/service.z", "lzw/recovery.z", "tmp/disk34.data", "service.dat", "recovery.dat"]

    p = TekFileProcessor()

    p.zip_read( file=input_file, path="disk1/fwdisk1.dat")
    p.zip_read( file=input_file, path="disk2/fwdisk2.dat")
    p.zip_read( file=input_file, path="disk2/fwdisk2a.dat")
    p.zip_read( file=input_file, path="disk3/fwdisk3.dat")
    p.zip_read( file=input_file, path="disk4/fwdisk4.dat")

    for name in outputnames:
        p.allocate(size=0, name=name)

    p.append(src="disk1/fwdisk1.dat",  start="0x60", dest="lzw/service.z")
    p.append(src="disk2/fwdisk2.dat",  start="0x60", dest="lzw/service.z")
    p.append(src="disk2/fwdisk2a.dat", start="0x60", dest="lzw/recovery.z")
    p.append(src="disk3/fwdisk3.dat",  start="0x60", dest="tmp/disk34.data")
    p.append(src="disk4/fwdisk4.dat",  start="0x60", dest="tmp/disk34.data")

    p.unlzw( src="lzw/service.z", dest="service.dat")
    p.unlzw( src="lzw/recovery.z", dest="recovery.dat")
    split_names = p.split_lzw(src="tmp/disk34.data", names=disk34_filenames)
    for name in split_names:
        data_name = f"{name}.dat"
        compressed_name = f"lzw/{name}.z"
        if p.has(data_name) and data_name not in files_to_save:
            files_to_save.append(data_name)
        if compressed_name not in files_to_save:
            files_to_save.append(compressed_name)

    test_checksums(p)

    for locale in known_locales():
        if not p.has(f"{locale}.dat"):
            continue
        try:
            results = decode_table(p.get(f"{locale}.dat"))
            s = []
            for i, (offset, string) in enumerate(results):
                s.append(f"{i:4d}\t0x{offset:04x}\t{string}\n")
            s = ''.join(s)

            p.allocate(size=0, name=f"locale/{locale}.txt")
            p.append(data=s.encode('utf-8'), dest=f"locale/{locale}.txt")
            files_to_save.append(f"locale/{locale}.txt")
        except Exception as e:
            warning(f"{locale}: could not decode string table view: {e}")

    print("\nSaving files...")
    for name in files_to_save:
        p.print(name=name)
    p.tar_add( output=output_tar, names=files_to_save)
    p.tar_write( output=output_tar)

    print(f"--> {output_tar}")


def main(argv):
    if len(argv) != 3:
        print("Usage: python unpack_fw.py <input_zip> <output.tar>")
        return 1

    try:
        unpack_fw(argv[1], argv[2])
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as e:
        error(f"unpack_fw.py: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
