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

processor = TekFileProcessor()
config = [
    {"do": "zip_read", "file": "tds3000_3.41_063354011_tek.zip", "path": "disk1/fwdisk1.dat"},
    {"do": "zip_read", "file": "tds3000_3.41_063354011_tek.zip", "path": "disk2/fwdisk2.dat"},
    {"do": "zip_read", "file": "tds3000_3.41_063354011_tek.zip", "path": "disk2/fwdisk2a.dat"},
    {"do": "zip_read", "file": "tds3000_3.41_063354011_tek.zip", "path": "disk3/fwdisk3.dat"},
    {"do": "zip_read", "file": "tds3000_3.41_063354011_tek.zip", "path": "disk4/fwdisk4.dat"},

    {"do": "allocate", "size": 0, "name": "lzw/updater.z"},
    {"do": "allocate", "size": 0, "name": "lzw/recovery.z"},
    {"do": "allocate", "size": 0, "name": "tmp/disk34.data"},
    {"do": "allocate", "size": 0, "name": "updater.dat"},
    {"do": "allocate", "size": 0, "name": "recovery.dat"},

    {"do": "append", "to": "lzw/updater.z", "from": "disk1/fwdisk1.dat", "start": "0x60"},
    {"do": "append", "to": "lzw/updater.z", "from": "disk2/fwdisk2.dat", "start": "0x60"},
    {"do": "append", "to": "lzw/recovery.z", "from": "disk2/fwdisk2a.dat", "start": "0x60"},
    {"do": "append", "to": "tmp/disk34.data", "from": "disk3/fwdisk3.dat", "start": "0x60"},
    {"do": "append", "to": "tmp/disk34.data", "from": "disk4/fwdisk4.dat", "start": "0x60"},

    {"do": "unlzw", "from": "lzw/updater.z", "to": "updater.dat"},
    {"do": "unlzw", "from": "lzw/recovery.z", "to": "recovery.dat"},
    {"do": "split_lzw", "from": "tmp/disk34.data", "names": disk34_filenames},

    {"do": "print", "name": "disk1/fwdisk1.dat"},
    {"do": "print_value", "text": "fwdisk1 checksum", "name": "disk1/fwdisk1.dat", "at": "0x0C"},
    {"do": "print", "name": "updater.dat"},
    {"do": "print", "name": "lzw/updater.z"},

    {"do": "tar_add", "output": "output.tar", "names": files_to_save},
    {"do": "tar_write", "output": "output.tar"}
]


processor.process(config)
