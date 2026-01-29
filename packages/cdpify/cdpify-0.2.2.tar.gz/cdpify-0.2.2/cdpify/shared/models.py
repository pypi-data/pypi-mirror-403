import re
from dataclasses import asdict, dataclass, fields, is_dataclass
from typing import Any, Self, get_args, get_origin


@dataclass
class CDPModel:
    def to_cdp_params(self) -> dict[str, Any]:
        return {_to_camel(k): v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_cdp(cls, data: dict) -> Self:
        snake_data = {_to_snake(k): v for k, v in data.items()}
        field_types = {f.name: f.type for f in fields(cls)}

        converted = {}
        for field_name, value in snake_data.items():
            if field_name not in field_types:
                continue

            field_type = field_types[field_name]
            converted[field_name] = _deserialize_field(value, field_type)

        return cls(**converted)


_ACRONYMS = frozenset(
    {
        "api",
        "css",
        "dom",
        "html",
        "json",
        "pdf",
        "spc",
        "ssl",
        "url",
        "uuid",
        "xml",
        "xhr",
        "ax",
        "cpu",
        "gpu",
        "io",
        "js",
        "os",
        "ui",
        "uri",
        "usb",
        "wasm",
        "http",
        "https",
    }
)


def _to_camel(s: str) -> str:
    parts = s.split("_")

    if not parts:
        return s

    result = [parts[0].lower()]

    for part in parts[1:]:
        lower = part.lower()
        result.append(part.upper() if lower in _ACRONYMS else part.capitalize())

    return "".join(result)


def _to_snake(s: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()


def _deserialize_field(value: Any, field_type: type) -> Any:
    if value is None:
        return None

    origin = get_origin(field_type)
    if origin is not None:
        args = get_args(field_type)

        if origin is type(None) or (len(args) == 2 and type(None) in args):
            actual_type = args[0] if args[1] is type(None) else args[1]
            return _deserialize_field(value, actual_type)

        if origin is list:
            item_type = args[0]
            return [_deserialize_field(item, item_type) for item in value]

    if (
        isinstance(value, dict)
        and is_dataclass(field_type)
        and issubclass(field_type, CDPModel)
    ):
        return field_type.from_cdp(value)

    return value
