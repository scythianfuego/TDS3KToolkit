from process import TekFileProcessor
from console import error, warning, success, notice, checksum_message
from strings import decode_table


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
    print("-- Next checksum calculation should includes some extra files (which?), ignore mismatch --")
    checksum_message("User firmware checksum", p.checksum(name="lzw/firmware.z"), p.value(name="disk3/fwdisk3.dat", at="0x0C"), 1 )


# available locales (scope order): en fr de it es br ru ja kr cn tw
# ja kr cn tw distinct is on best guess
locales = [
    "en", "it", "kr", "de", "es",
    "ja", "fr", "pt", "ru", "cn",
    "tw"]

disk34_filenames = ["firmware"] + [f"locale_{locale}" for locale in locales]

# 1 korean 5 chinsese 6 taiwanese
files_to_save = [
    "service.dat", "recovery.dat", "firmware.dat",
    "lzw/service.z", "lzw/recovery.z", "lzw/firmware.z"]

outputnames = ["lzw/service.z", "lzw/recovery.z", "tmp/disk34.data", "service.dat", "recovery.dat"]

for locale in locales:
    files_to_save.append(f"locale_{locale}.dat")
    files_to_save.append(f"lzw/locale_{locale}.z")
    files_to_save.append(f"locale/strings_{locale}.txt")
    outputnames.append(f"locale/strings_{locale}.txt")

p = TekFileProcessor()

input="tds3000_3.41_063354011_tek.zip"

p.zip_read( file=input, path="disk1/fwdisk1.dat")
p.zip_read( file=input, path="disk2/fwdisk2.dat")
p.zip_read( file=input, path="disk2/fwdisk2a.dat")
p.zip_read( file=input, path="disk3/fwdisk3.dat")
p.zip_read( file=input, path="disk4/fwdisk4.dat")

for name in outputnames:
    p.allocate(size=0, name=name)

p.append(src="disk1/fwdisk1.dat",  start="0x60", dest="lzw/service.z")
p.append(src="disk2/fwdisk2.dat",  start="0x60", dest="lzw/service.z")
p.append(src="disk2/fwdisk2a.dat", start="0x60", dest="lzw/recovery.z")
p.append(src="disk3/fwdisk3.dat",  start="0x60", dest="tmp/disk34.data")
p.append(src="disk4/fwdisk4.dat",  start="0x60", dest="tmp/disk34.data")

p.unlzw( src="lzw/service.z", dest="service.dat")
p.unlzw( src="lzw/recovery.z", dest="recovery.dat")
p.split_lzw( src="tmp/disk34.data", names=disk34_filenames)

test_checksums(p)

for locale in locales:
    results = decode_table(p.get(f"locale_{locale}.dat"))
    s = "";
    for i, (offset, string) in enumerate(results):
        s += f"{i:4d}\t0x{offset:04x}\t{string}\n"

    p.append(data=s.encode('utf-8'), dest=f"locale/strings_{locale}.txt")

print("\nSaving files...")
for name in files_to_save:
    p.print(name=name)

output = "output.tar"
p.tar_add( output=output, names=files_to_save)
p.tar_write( output=output)

print(f"--> {output}")
