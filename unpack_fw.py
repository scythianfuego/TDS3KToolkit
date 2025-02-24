from process import TekFileProcessor

def checksum_message(text, calculated, expected):
    if (calculated == expected):
        print(f"{text} OK: {calculated:08X}")
    else:
        print(f"{text} failed: calculated {calculated:08X} expected {expected:08X}")


def test_checksums(p):
    # disk contents
    checksum_message("fwdisk1.dat  checksum", p.checksum(name="disk1/fwdisk1.dat",  start="0x60"), p.value(name="disk1/fwdisk1.dat", at="0x08") )
    checksum_message("fwdisk2.dat  checksum", p.checksum(name="disk2/fwdisk2.dat",  start="0x60"), p.value(name="disk2/fwdisk2.dat", at="0x08") )
    checksum_message("fwdisk2a.dat checksum", p.checksum(name="disk2/fwdisk2a.dat", start="0x60"), p.value(name="disk2/fwdisk2a.dat",at="0x08") )
    checksum_message("fwdisk3.dat  checksum", p.checksum(name="disk3/fwdisk3.dat",  start="0x60"), p.value(name="disk3/fwdisk3.dat", at="0x08") )
    checksum_message("fwdisk4.dat  checksum", p.checksum(name="disk4/fwdisk4.dat",  start="0x60"), p.value(name="disk4/fwdisk4.dat", at="0x08") )
    #data
    checksum_message("Updater checksum ", p.checksum(name="lzw/updater.z"), p.value(name="disk1/fwdisk1.dat", at="0x0C") )
    checksum_message("Recovery checksum", p.checksum(name="lzw/recovery.z"), p.value(name="disk2/fwdisk2a.dat", at="0x0C") )
    print("-- Next checksum should includes some extra files (which?), ignore mismatch --")
    checksum_message("Firmware checksum", p.checksum(name="lzw/firmware.z"), p.value(name="disk3/fwdisk3.dat", at="0x0C") )


disk34_filenames = [
    "firmware",
    "strings_en", "strings_it", "module_1", "strings_de", "module_2",
    "module_3", "strings_fr", "strings_pt", "module_4", "module_5", "module_6"
]

files_to_save = [
    "updater.dat", "recovery.dat", "firmware.dat",
    "lzw/updater.z", "lzw/recovery.z", "lzw/firmware.z",

    "strings_en.dat",
    "strings_it.dat",
    "strings_de.dat",
    "strings_fr.dat",
    "strings_pt.dat",
    "module_1.dat",
    "module_2.dat",
    "module_3.dat",
    "module_4.dat",
    "module_5.dat",
    "module_6.dat",

    "lzw/strings_en.z",
    "lzw/strings_it.z",
    "lzw/strings_de.z",
    "lzw/strings_fr.z",
    "lzw/strings_pt.z",
    "lzw/module_1.z",
    "lzw/module_2.z",
    "lzw/module_3.z",
    "lzw/module_4.z",
    "lzw/module_5.z",
    "lzw/module_6.z",
];

p = TekFileProcessor()

input="tds3000_3.41_063354011_tek.zip"

p.zip_read( file=input, path="disk1/fwdisk1.dat")
p.zip_read( file=input, path="disk2/fwdisk2.dat")
p.zip_read( file=input, path="disk2/fwdisk2a.dat")
p.zip_read( file=input, path="disk3/fwdisk3.dat")
p.zip_read( file=input, path="disk4/fwdisk4.dat")

outputnames = ["lzw/updater.z", "lzw/recovery.z", "tmp/disk34.data", "updater.dat", "recovery.dat"]
for name in outputnames:
    p.allocate(size=0, name=name)

p.append(src="disk1/fwdisk1.dat",  start="0x60", dest="lzw/updater.z")
p.append(src="disk2/fwdisk2.dat",  start="0x60", dest="lzw/updater.z")
p.append(src="disk2/fwdisk2a.dat", start="0x60", dest="lzw/recovery.z")
p.append(src="disk3/fwdisk3.dat",  start="0x60", dest="tmp/disk34.data")
p.append(src="disk4/fwdisk4.dat",  start="0x60", dest="tmp/disk34.data")

p.unlzw( src="lzw/updater.z", dest="updater.dat")
p.unlzw( src="lzw/recovery.z", dest="recovery.dat")
p.split_lzw( src="tmp/disk34.data", names=disk34_filenames)

test_checksums(p)

print("\nSaving files...")
for name in files_to_save:
    p.print(name=name)

output = "output.tar"
p.tar_add( output=output, names=files_to_save)
p.tar_write( output=output)

print(f"--> {output}")
