"""
Минимальный pure-Python protobuf парсер.
Поддерживает только wire types, используемые в CEconItemPreviewDataBlock.
Без внешних зависимостей.
"""

from typing import Any, List, Tuple

VARINT = 0
FIXED64 = 1
LENGTH_DELIMITED = 2
FIXED32 = 5

_MAX_FIELDS = 100


def read_varint(data: bytes, offset: int) -> Tuple[int, int]:
    """Читает varint из data начиная с offset. Возвращает (value, new_offset)."""
    result = 0
    shift = 0
    while offset < len(data):
        b = data[offset]
        offset += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, offset
        shift += 7
        if shift > 63:
            raise ValueError("Varint overflow")
    raise ValueError("Truncated varint")


def write_varint(value: int) -> bytes:
    """Кодирует целое число в varint."""
    if value == 0:
        return b'\x00'
    buf = bytearray()
    while value > 0:
        byte = value & 0x7F
        value >>= 7
        if value > 0:
            byte |= 0x80
        buf.append(byte)
    return bytes(buf)


def parse_fields(data: bytes) -> List[Tuple[int, int, Any]]:
    """
    Парсит protobuf-данные в список (field_number, wire_type, value).
    Для varint: value = int.
    Для fixed32/fixed64: value = bytes.
    Для length-delimited: value = bytes.
    """
    fields: List[Tuple[int, int, Any]] = []
    offset = 0
    for _ in range(_MAX_FIELDS):
        if offset >= len(data):
            break
        tag, offset = read_varint(data, offset)
        field_num = tag >> 3
        wire_type = tag & 0x07

        if wire_type == VARINT:
            value, offset = read_varint(data, offset)
        elif wire_type == FIXED64:
            if offset + 8 > len(data):
                raise ValueError("Truncated fixed64")
            value = data[offset:offset + 8]
            offset += 8
        elif wire_type == LENGTH_DELIMITED:
            length, offset = read_varint(data, offset)
            if offset + length > len(data):
                raise ValueError("Truncated length-delimited")
            value = data[offset:offset + length]
            offset += length
        elif wire_type == FIXED32:
            if offset + 4 > len(data):
                raise ValueError("Truncated fixed32")
            value = data[offset:offset + 4]
            offset += 4
        else:
            raise ValueError(f"Unsupported wire type {wire_type}")

        fields.append((field_num, wire_type, value))
    else:
        if offset < len(data):
            raise ValueError("Too many protobuf fields")

    return fields


def encode_field(field_num: int, wire_type: int, value: Any) -> bytes:
    """Кодирует одно protobuf-поле."""
    tag = write_varint((field_num << 3) | wire_type)
    if wire_type == VARINT:
        return tag + write_varint(value)
    elif wire_type == LENGTH_DELIMITED:
        return tag + write_varint(len(value)) + value
    elif wire_type == FIXED32:
        return tag + value
    elif wire_type == FIXED64:
        return tag + value
    raise ValueError(f"Cannot encode wire type {wire_type}")
