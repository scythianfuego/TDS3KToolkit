import time
import tarfile
import zipfile
import struct
from io import BytesIO
from .uncompress import unlzw
from .splitlzw import splitlzw
from .checksum import checksum

# Convert a string into an integer offset, detecting hex (0x) or decimal.
def readhex(value: str) -> int:
    return int(value, 16 if value.lower().startswith("0x") else 10)

def align(value):
    return (value + 3) & ~3

def localename(index):
    names = [ "en", "it", "kr", "de", "es", "ja", "fr", "pt", "ru", "cn", "tw"]
    suffix = f"{index:2}" if index >= len(names) else names[index]
    return f"locale_{suffix}"

# available locales (scope order): en fr de it es br ru ja kr cn tw
# ja kr cn tw distinct is on best guess
def known_locales(extension=""):
    return [localename(i) + extension for i in range(11)]

data_store = {}
tar_buffer = BytesIO()
directories_added = set()

class TekFileProcessor:
    # public API

    def read(self, file):
        data_store[file] = self.__read(file)

    def write(self, name):
        self.__write(name)

    def zip_read(self, *, file, path):
        data_store[path] = self.__zip_read(file, path)

    def tar_read(self, *, file, path):
        data_store[path] = self.__tar_read(file, path)

    def allocate(self, *, size, name, init=0):
        self.__allocate(name, size, init)

    def append(self, *, dest, src=None, data=None, start=0, end=None):
        start = int(start, 16) if isinstance(start, str) else start
        end = int(end, 16) if isinstance(end, str) else end
        source_data = data if src is None else data_store.get(src, b"")
        self.__append(dest, source_data, start, end)

    def replace(self, *, dest, src=None, data=None, at):
        if (src==None and data==None):
            return

        at = int(at, 16) if isinstance(at, str) else at
        source_data = data if src is None else data_store.get(src, b"")
        dest_data = data_store.get(dest, bytearray())

        if at + len(source_data) > len(dest_data):
            # error(f"Replace operation would exceed destination buffer size")
            return

        dest_data[at:at + len(source_data)] = source_data
        data_store[dest] = dest_data

    def unlzw(self, *, src, dest):
        data_store[dest] = bytearray(unlzw(data_store.get(src)))

    def split_lzw(self, *, src, names):
        self.__split_lzw(src, names)

    def print(self, *, name):
        self.__print_debug(name)

    def print_value(self, *, text, name, at):
        self.__print_value(text, name, int(at, 16))

    def value(self, *, name, at):
        at = int(at, 16) if isinstance(at, str) else at
        return self.__value(name, at)

    def size(self, *, name):
        return self.__size(name)

    def tar_add(self, *, output, names):
        self.__tar_add(names)

    def tar_write(self, *, output):
        self.__tar_write(output)

    def checksum(self, *, name, start=0, end=None):
        data = data_store.get(name, b"")
        start = int(start, 16) if isinstance(start, str) else start
        end = int(end, 16) if isinstance(end, str) else end
        data = data[start:] if end is None else data[start:end]
        return checksum(data)

    def get(self, name: str):
        return bytes(data_store.get(name, b""))


    # private methods

    def __allocate(self, name: str, size: int, init: int = 0):
        data_store[name] = bytearray(size)
        if init != 0:
            for i in range(size):
                data_store[name][i] = init

    def __append(self, to: str, from_data: bytes, start: int = 0, end: int = None):
        if to not in data_store:
            data_store[to] = bytearray()
            print(f"Implicitly allocated: {to}. Check naming!") # should we create it?

        data_to_append = from_data[start:] if end is None else from_data[start:end]
        data_store[to].extend(data_to_append)

    def __get(self, name: str):
        return bytes(data_store.get(name, b""))

    # Read a file from a zip archive at a given path.
    def __zip_read(self, zipfile_path: str, file_path: str) -> bytes:
        with zipfile.ZipFile(zipfile_path, 'r') as zipf:
            with zipf.open(file_path) as file:
                return file.read()

    # Read a file from tar archive at a given path.
    def __tar_read(self, tarfile_path: str, file_path: str) -> bytes:
        with tarfile.open(tarfile_path, 'r') as tarf:
            with tarf.extractfile(file_path) as file:
                return file.read()

    # Read a file from file system.
    def __read(self, file_path: str) -> bytes:
        with open(file_path, "rb") as f:
            return f.read()

    # Write file into filesystem
    def __write(self, name: str) -> None:
        with open(name, "wb") as f:
            f.write(data_store.get(name, b""))

    def __tar_add(self, names):
        global directories_added
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            for name in names:
                if '/' in name:
                    dir_name = name.rsplit('/', 1)[0]
                    if dir_name not in directories_added:
                        dir_info = tarfile.TarInfo(name=dir_name + '/')
                        dir_info.type = tarfile.DIRTYPE
                        dir_info.mtime = time.time()
                        tar.addfile(dir_info)
                        directories_added.add(dir_name)

                data_io = BytesIO(self.__get(name))
                tarinfo = tarfile.TarInfo(name=name)
                tarinfo.size = len(data_io.getbuffer())
                tarinfo.mtime = time.time()
                tar.addfile(tarinfo, data_io)

    def __tar_write(self, output_tar):
        with open(output_tar, "wb") as f:
            f.write(tar_buffer.getvalue())


    # takes LWZ compressed data from disk3 and disk4 and splits by magic number
    def __split_lzw(self, source, filenames):
        files = splitlzw(data_store[source], filenames)
        for file in files:
            name = file["name"]
            uname = name + ".dat"
            cname = "lzw/" + name + ".z"
            data_store[uname] = file["decompressed"]
            data_store[cname] = file["compressed"]

    def __size(self, name):
        data = data_store.get(name, b"")
        return len(data)

    def __value(self, name, at):
        data = data_store.get(name, b"")
        if at + 4 <= len(data):
            return struct.unpack_from(">I", data, at)[0]
        else:
            return None

    def __print_debug(self, name):
        data = data_store.get(name, b"")
        hex_first = data[:8].hex()
        hex_last = data[-8:].hex()
        print(f"{name.ljust(20)}  {str(len(data)).rjust(7)} bytes   {hex_first}...{hex_last}")

    def __print_value(self, text, name, at):
        data = data_store.get(name, b"")
        if at + 4 <= len(data):
            value = struct.unpack_from(">I", data, at)[0]
            print(f"{text}: {value:08X}")
        else:
            print(f"{text}: Offset out of range")

