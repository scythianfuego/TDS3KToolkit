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
    suffix = f"{index:02d}" if index >= len(names) else names[index]
    return f"locale_{suffix}"

# physical locale block order; saved language settings are remapped by firmware
def known_locales(extension=""):
    return [localename(i) + extension for i in range(11)]

class TekFileProcessor:
    # public API

    def __init__(self):
        self.data_store = {}
        self.tar_buffer = BytesIO()

    def read(self, file):
        self.data_store[file] = self.__read(file)

    def write(self, name, src=None):
        self.__write(name, src if src is not None else name)

    def zip_read(self, *, file, path):
        self.data_store[path] = self.__zip_read(file, path)

    def tar_read(self, *, file, path):
        self.data_store[path] = self.__tar_read(file, path)

    def allocate(self, *, size, name, init=0):
        self.__allocate(name, size, init)

    def append(self, *, dest, src=None, data=None, start=0, end=None):
        start = int(start, 16) if isinstance(start, str) else start
        end = int(end, 16) if isinstance(end, str) else end
        if src is None and data is None:
            raise ValueError("append needs src or data")
        source_data = data if src is None else self.get(src)
        self.__append(dest, source_data, start, end)

    def replace(self, *, dest, src=None, data=None, at):
        if (src==None and data==None):
            raise ValueError("replace needs src or data")

        at = int(at, 16) if isinstance(at, str) else at
        source_data = data if src is None else self.data_store.get(src, None)
        if source_data is None:
            raise ValueError(f"{src}: no such input data")
        dest_data = self.data_store.get(dest, None)
        if dest_data is None:
            raise ValueError(f"{dest}: no such destination data")

        if at + len(source_data) > len(dest_data):
            raise ValueError(f"{src}: replace would exceed {dest} at 0x{at:X}")

        dest_data[at:at + len(source_data)] = source_data
        self.data_store[dest] = dest_data

    def unlzw(self, *, src, dest):
        self.data_store[dest] = bytearray(unlzw(self.get(src)))

    def split_lzw(self, *, src, names):
        return self.__split_lzw(src, names)

    def has(self, name):
        return name in self.data_store

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
        data = self.get(name)
        start = int(start, 16) if isinstance(start, str) else start
        end = int(end, 16) if isinstance(end, str) else end
        data = data[start:] if end is None else data[start:end]
        return checksum(data)

    def get(self, name: str):
        data = self.data_store.get(name, None)
        if data is None:
            raise ValueError(f"{name}: no such input data")
        return bytes(data)


    # private methods

    def __allocate(self, name: str, size: int, init: int = 0):
        self.data_store[name] = bytearray(size)
        if init != 0:
            for i in range(size):
                self.data_store[name][i] = init

    def __append(self, to: str, from_data: bytes, start: int = 0, end: int = None):
        if to not in self.data_store:
            raise ValueError(f"{to}: no such destination data")

        data_to_append = from_data[start:] if end is None else from_data[start:end]
        self.data_store[to].extend(data_to_append)

    def __get(self, name: str):
        return self.get(name)

    # Read a file from a zip archive at a given path.
    def __zip_read(self, zipfile_path: str, file_path: str) -> bytes:
        with zipfile.ZipFile(zipfile_path, 'r') as zipf:
            path = file_path
            if path not in zipf.namelist():
                suffix = "/" + file_path
                matches = [
                    name for name in zipf.namelist()
                    if not name.startswith("__MACOSX/") and name.endswith(suffix)
                ]
                if len(matches) != 1:
                    raise ValueError(f"{file_path}: not found in {zipfile_path}")
                path = matches[0]
            with zipf.open(path) as file:
                return file.read()

    # Read a file from tar archive at a given path.
    def __tar_read(self, tarfile_path: str, file_path: str) -> bytes:
        with tarfile.open(tarfile_path, 'r') as tarf:
            try:
                file = tarf.extractfile(file_path)
            except KeyError:
                raise ValueError(f"{file_path}: not found in {tarfile_path}") from None
            if file is None:
                raise ValueError(f"{file_path}: not a regular file in {tarfile_path}")
            with file:
                return file.read()

    # Read a file from file system.
    def __read(self, file_path: str) -> bytes:
        with open(file_path, "rb") as f:
            return f.read()

    # Write file into filesystem
    def __write(self, path: str, name: str) -> None:
        data = self.data_store.get(name, None)
        if data is None:
            raise ValueError(f"{name}: no such output data")
        with open(path, "wb") as f:
            f.write(data)

    def __tar_add(self, names):
        directories_added = set()
        self.tar_buffer.seek(0)
        self.tar_buffer.truncate()
        with tarfile.open(fileobj=self.tar_buffer, mode="w") as tar:
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
            f.write(self.tar_buffer.getvalue())


    # takes LZW compressed data from disk3 and disk4 and splits by magic number
    def __split_lzw(self, source, filenames):
        files = splitlzw(self.get(source), filenames)
        names = []
        for file in files:
            name = file["name"]
            uname = name + ".dat"
            cname = "lzw/" + name + ".z"
            self.data_store[cname] = file["compressed"]
            if file["decompressed"] is not None:
                self.data_store[uname] = file["decompressed"]
            names.append(name)
        return names

    def __size(self, name):
        return len(self.get(name))

    def __value(self, name, at):
        data = self.get(name)
        if at + 4 <= len(data):
            return struct.unpack_from(">I", data, at)[0]
        else:
            return None

    def __print_debug(self, name):
        data = self.get(name)
        hex_first = data[:8].hex()
        hex_last = data[-8:].hex()
        print(f"{name.ljust(20)}  {str(len(data)).rjust(7)} bytes   {hex_first}...{hex_last}")

    def __print_value(self, text, name, at):
        data = self.get(name)
        if at + 4 <= len(data):
            value = struct.unpack_from(">I", data, at)[0]
            print(f"{text}: {value:08X}")
        else:
            print(f"{text}: Offset out of range")
