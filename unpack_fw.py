from process import TekFileProcessor

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

p.zip_read( file="tds3000_3.41_063354011_tek.zip", path="disk1/fwdisk1.dat")
p.zip_read( file="tds3000_3.41_063354011_tek.zip", path="disk2/fwdisk2.dat")
p.zip_read( file="tds3000_3.41_063354011_tek.zip", path="disk2/fwdisk2a.dat")
p.zip_read( file="tds3000_3.41_063354011_tek.zip", path="disk3/fwdisk3.dat")
p.zip_read( file="tds3000_3.41_063354011_tek.zip", path="disk4/fwdisk4.dat")

p.allocate( size=0, name="lzw/updater.z")
p.allocate( size=0, name="lzw/recovery.z")
p.allocate( size=0, name="tmp/disk34.data")
p.allocate( size=0, name="updater.dat")
p.allocate( size=0, name="recovery.dat")

p.append( dest="lzw/updater.z", src="disk1/fwdisk1.dat", start="0x60")
p.append( dest="lzw/updater.z", src="disk2/fwdisk2.dat", start="0x60")
p.append( dest="lzw/recovery.z", src="disk2/fwdisk2a.dat", start="0x60")
p.append( dest="tmp/disk34.data", src="disk3/fwdisk3.dat", start="0x60")
p.append( dest="tmp/disk34.data", src="disk4/fwdisk4.dat", start="0x60")

p.unlzw( src="lzw/updater.z", dest="updater.dat")
p.unlzw( src="lzw/recovery.z", dest="recovery.dat")
p.split_lzw( src="tmp/disk34.data", names=disk34_filenames)

p.print( name="disk1/fwdisk1.dat")
p.print_value( text="fwdisk1 checksum", name="disk1/fwdisk1.dat", at="0x0C")
p.print( name="updater.dat")
p.print( name="lzw/updater.z")

p.tar_add( output="output.tar", names=files_to_save)
p.tar_write( output="output.tar")


