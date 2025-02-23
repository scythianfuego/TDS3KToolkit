from process import process_steps


# read fw1 from zip tds3000_3.41_063354011_tek.zip -> disk1/fwdisk1.dat
# (store actual size, do not allocate, how?)

config = [
    {"action": "read_tar", "tarfile": "input.tar", "path": "file_a"},
    {"action": "read_tar", "tarfile": "input.tar", "path": "file_b"},
    {"action": "allocate", "size": "0x400000", "init_value": "0xFF"},
    {"action": "write", "source": "file_a", "offset": "0xB00"},
    {"action": "write", "source": "file_b", "offset": "0x4000"},
    {"action": "crc"},
    {"action": "write_crc", "offsets": ["0x16", "0x20"]},
    {"action": "write_tar", "output": "output.tar", "path_name": "final_block.bin"}
]

process_steps(config)