import json
from os.path import dirname, join

from teklib.compactjson import dumps_readable
from teklib.console import warning


STRUCTS = join(dirname(__file__), "ftlfs_structs")
_cstructs = {}
_warned_cstruct = False


def json_text(value):
    return dumps_readable(value)


def schema_file(key, size=None):
    names = []
    if size is not None:
        names.append(f"key_{key:02X}_0{size:03X}.cstruct")

    names.append(f"key_{key:02X}.cstruct")
    for name in names:
        path = join(STRUCTS, name)
        try:
            open(path, "rb").close()
            return path
        except OSError:
            pass
    return None


def cstruct_parser(path):
    global _warned_cstruct
    if path in _cstructs:
        return _cstructs[path]
    try:
        from dissect.cstruct import cstruct

        cs = cstruct(endian=">")
        with open(path, encoding="ascii") as fh:
            cs.load(fh.read())
        _cstructs[path] = cs
        return cs
    except Exception as exc:
        if not _warned_cstruct:
            warning(f"dissect.cstruct unavailable; decoded JSON skipped ({exc})")
            _warned_cstruct = True
        return None


def cstr(data):
    return data.split(b"\0", 1)[0].decode("ascii", errors="replace")


def json_default(obj):
    if hasattr(obj, "__values__"):
        return obj.__values__
    if hasattr(obj, "items"):
        return dict(obj.items())
    if isinstance(obj, bytes):
        return cstr(obj)
    raise TypeError(f"{type(obj).__name__} is not JSON serializable")


def plain(obj):
    return json.loads(json.dumps(obj, default=json_default))


def fill(value, template):
    if hasattr(template, "__values__"):
        for name, old in template.__values__.items():
            setattr(template, name, fill(value[name], old))
        return template
    if isinstance(template, bytes):
        if len(template) == 0:
            return str(value).encode("ascii")
        data = str(value).encode("ascii")
        return data[:len(template)].ljust(len(template), b"\0")
    if isinstance(template, list):
        if template and hasattr(template[0], "__values__"):
            return [fill(item, type(template[i])()) for i, item in enumerate(value)]
        return [fill(item, template[i]) for i, item in enumerate(value)]
    return value


def decode_payload(key, payload):
    path = schema_file(key, len(payload))
    if path is None:
        return None
    cs = cstruct_parser(path)
    if cs is None:
        return None
    return plain(cs.file(payload))


def encode_payload(key, data, size=None):
    path = schema_file(key, size)
    if path is None:
        raise ValueError(f"key 0x{key:02X}: no JSON encoder")
    cs = cstruct_parser(path)
    if cs is None:
        raise ValueError("dissect.cstruct is required to encode this JSON")
    return bytes(fill(data, cs.file()))
