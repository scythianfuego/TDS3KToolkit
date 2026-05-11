import json

_PRIMITIVES = (str, int, float, bool, type(None))


def _is_shallow(value):
    if isinstance(value, _PRIMITIVES):
        return True

    if isinstance(value, list):
        return all(isinstance(x, _PRIMITIVES) for x in value)

    if isinstance(value, dict):
        return all(
            isinstance(k, str) and isinstance(v, _PRIMITIVES)
            for k, v in value.items()
        )

    return False


def dumps_readable(value, level=0):
    indent = 2
    pad = " " * (indent * level)
    child_pad = " " * (indent * (level + 1))

    if _is_shallow(value):
        return json.dumps(value)

    if isinstance(value, dict):
        if not value:
            return "{}"

        lines = ["{"]
        items = list(value.items())

        for i, (key, item) in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            key_text = json.dumps(key)
            item_text = dumps_readable(item, level + 1)

            if "\n" not in item_text:
                lines.append(f"{child_pad}{key_text}: {item_text}{comma}")
            else:
                item_lines = item_text.splitlines()
                lines.append(f"{child_pad}{key_text}: {item_lines[0]}")
                lines.extend(item_lines[1:-1])
                lines.append(f"{item_lines[-1]}{comma}")

        lines.append(f"{pad}}}")
        return "\n".join(lines)

    if isinstance(value, list):
        if not value:
            return "[]"

        lines = ["["]

        for i, item in enumerate(value):
            comma = "," if i < len(value) - 1 else ""
            item_text = dumps_readable(item, level + 1)

            if "\n" not in item_text:
                lines.append(f"{child_pad}{item_text}{comma}")
            else:
                item_lines = item_text.splitlines()
                lines.append(f"{child_pad}{item_lines[0]}")
                lines.extend(item_lines[1:-1])
                lines.append(f"{item_lines[-1]}{comma}")

        lines.append(f"{pad}]")
        return "\n".join(lines)

    return json.dumps(value)