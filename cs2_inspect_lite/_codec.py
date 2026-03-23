"""
Кодирование/декодирование CS2 inspect-ссылок и propid:6.

Бинарный формат:
  [key_byte] [proto_bytes XOR key] [4-byte checksum XOR key]

Три формата URL:
  1. Masked:  steam://run/730//+csgo_econ_action_preview%20<hex>
  2. Hybrid:  ...S<steamid>A<assetid>D<hex_proto>
  3. Classic: ...S<steamid>A<assetid>D<decimal>  (не декодируется offline)
"""

import re
import struct
import zlib
from typing import Optional
from urllib.parse import unquote

from ._proto import (
    FIXED32, LENGTH_DELIMITED, VARINT,
    encode_field, parse_fields, write_varint,
)
from .models import ItemInfo, Sticker

_MAX_HEX_LEN = 4096

_INSPECT_RE = re.compile(r'csgo_econ_action_preview\s+(.+?)$', re.IGNORECASE)
_CLASSIC_RE = re.compile(r'^S\d+A\d+D\d+$')
_HYBRID_RE = re.compile(r'^S\d+A\d+D(.+)$')


# ── XOR + checksum ───────────────────────────────────────

def _xor_bytes(data: bytes) -> bytes:
    key = data[0]
    if key == 0:
        return data
    return bytes(b ^ key for b in data)


def _compute_checksum(proto_bytes: bytes) -> bytes:
    buf = b'\x00' + proto_bytes
    crc = zlib.crc32(buf) & 0xFFFFFFFF
    xored = ((crc & 0xFFFF) ^ (len(proto_bytes) * crc)) & 0xFFFFFFFF
    return struct.pack('>I', xored)


# ── Protobuf → модели ────────────────────────────────────

def _parse_sticker(data: bytes) -> Sticker:
    s = Sticker()
    for fn, wt, val in parse_fields(data):
        if   fn == 1  and wt == VARINT:  s.slot = val
        elif fn == 2  and wt == VARINT:  s.sticker_id = val
        elif fn == 3  and wt == FIXED32: s.wear = struct.unpack('<f', val)[0]
        elif fn == 4  and wt == FIXED32: s.scale = struct.unpack('<f', val)[0]
        elif fn == 5  and wt == FIXED32: s.rotation = struct.unpack('<f', val)[0]
        elif fn == 6  and wt == VARINT:  s.tint_id = val
        elif fn == 7  and wt == FIXED32: s.offset_x = struct.unpack('<f', val)[0]
        elif fn == 8  and wt == FIXED32: s.offset_y = struct.unpack('<f', val)[0]
        elif fn == 9  and wt == FIXED32: s.offset_z = struct.unpack('<f', val)[0]
        elif fn == 10 and wt == VARINT:  s.pattern = val
    return s


def _parse_item_proto(data: bytes) -> ItemInfo:
    item = ItemInfo()
    for fn, wt, val in parse_fields(data):
        if   fn == 1  and wt == VARINT:            item.accountid = val
        elif fn == 2  and wt == VARINT:            item.itemid = val
        elif fn == 3  and wt == VARINT:            item.defindex = val
        elif fn == 4  and wt == VARINT:            item.paintindex = val
        elif fn == 5  and wt == VARINT:            item.rarity = val
        elif fn == 6  and wt == VARINT:            item.quality = val
        elif fn == 7  and wt == VARINT:
            item.paintwear = struct.unpack('f', struct.pack('I', val))[0]
        elif fn == 8  and wt == VARINT:            item.paintseed = val
        elif fn == 9  and wt == VARINT:            item.killeaterscoretype = val
        elif fn == 10 and wt == VARINT:            item.killeatervalue = val
        elif fn == 11 and wt == LENGTH_DELIMITED:  item.customname = val.decode('utf-8', errors='replace')
        elif fn == 12 and wt == LENGTH_DELIMITED:  item.stickers.append(_parse_sticker(val))
        elif fn == 13 and wt == VARINT:            item.inventory = val
        elif fn == 14 and wt == VARINT:            item.origin = val
        elif fn == 15 and wt == VARINT:            item.questid = val
        elif fn == 16 and wt == VARINT:            item.dropreason = val
        elif fn == 17 and wt == VARINT:            item.musicindex = val
        elif fn == 18 and wt == VARINT:            item.entindex = val
        elif fn == 19 and wt == VARINT:            item.petindex = val
        elif fn == 20 and wt == LENGTH_DELIMITED:  item.keychains.append(_parse_sticker(val))
    return item


# ── Модели → protobuf ────────────────────────────────────

def _encode_sticker(s: Sticker) -> bytes:
    parts = []
    if s.slot:       parts.append(encode_field(1, VARINT, s.slot))
    if s.sticker_id: parts.append(encode_field(2, VARINT, s.sticker_id))
    if s.wear is not None:     parts.append(encode_field(3, FIXED32, struct.pack('<f', s.wear)))
    if s.scale is not None:    parts.append(encode_field(4, FIXED32, struct.pack('<f', s.scale)))
    if s.rotation is not None: parts.append(encode_field(5, FIXED32, struct.pack('<f', s.rotation)))
    if s.tint_id:    parts.append(encode_field(6, VARINT, s.tint_id))
    if s.offset_x is not None: parts.append(encode_field(7, FIXED32, struct.pack('<f', s.offset_x)))
    if s.offset_y is not None: parts.append(encode_field(8, FIXED32, struct.pack('<f', s.offset_y)))
    if s.offset_z is not None: parts.append(encode_field(9, FIXED32, struct.pack('<f', s.offset_z)))
    if s.pattern:    parts.append(encode_field(10, VARINT, s.pattern))
    return b''.join(parts)


def _encode_item_proto(item: ItemInfo) -> bytes:
    parts = []
    if item.accountid:          parts.append(encode_field(1, VARINT, item.accountid))
    if item.itemid:             parts.append(encode_field(2, VARINT, item.itemid))
    if item.defindex:           parts.append(encode_field(3, VARINT, item.defindex))
    if item.paintindex:         parts.append(encode_field(4, VARINT, item.paintindex))
    if item.rarity:             parts.append(encode_field(5, VARINT, item.rarity))
    if item.quality:            parts.append(encode_field(6, VARINT, item.quality))
    if item.paintwear:
        wear_uint = struct.unpack('I', struct.pack('f', item.paintwear))[0]
        parts.append(encode_field(7, VARINT, wear_uint))
    if item.paintseed:          parts.append(encode_field(8, VARINT, item.paintseed))
    if item.killeaterscoretype: parts.append(encode_field(9, VARINT, item.killeaterscoretype))
    if item.killeatervalue:     parts.append(encode_field(10, VARINT, item.killeatervalue))
    if item.customname:         parts.append(encode_field(11, LENGTH_DELIMITED, item.customname.encode('utf-8')))
    for s in item.stickers:     parts.append(encode_field(12, LENGTH_DELIMITED, _encode_sticker(s)))
    if item.inventory:          parts.append(encode_field(13, VARINT, item.inventory))
    if item.origin:             parts.append(encode_field(14, VARINT, item.origin))
    if item.questid:            parts.append(encode_field(15, VARINT, item.questid))
    if item.dropreason:         parts.append(encode_field(16, VARINT, item.dropreason))
    if item.musicindex:         parts.append(encode_field(17, VARINT, item.musicindex))
    if item.entindex:           parts.append(encode_field(18, VARINT, item.entindex))
    if item.petindex:           parts.append(encode_field(19, VARINT, item.petindex))
    for k in item.keychains:    parts.append(encode_field(20, LENGTH_DELIMITED, _encode_sticker(k)))
    return b''.join(parts)


# ── Публичные функции ─────────────────────────────────────

def decode_hex(hex_str: str) -> ItemInfo:
    """
    Декодирует hex-строку (propid:6 или payload inspect-ссылки) в ItemInfo.
    Поддерживает как XOR-обфусцированные (key != 0), так и plain (key = 0) данные.
    Checksum не верифицируется при декодировании (аналогично поведению Valve).
    """
    hex_str = hex_str.strip()
    if len(hex_str) > _MAX_HEX_LEN:
        raise ValueError(f"Hex payload слишком длинный ({len(hex_str)} > {_MAX_HEX_LEN})")

    raw = bytes.fromhex(hex_str)
    if len(raw) < 6:
        raise ValueError("Payload слишком короткий")

    decoded = _xor_bytes(raw)
    proto_bytes = decoded[1:-4]

    return _parse_item_proto(proto_bytes)


def encode_hex(item: ItemInfo, xor_key: int = 0) -> str:
    """
    Кодирует ItemInfo в hex-строку.
    xor_key=0 — plain формат (tool links). Другие значения — обфускация.
    """
    if item.paintwear < 0 or item.paintwear > 1:
        raise ValueError("paintwear должен быть в диапазоне [0.0, 1.0]")
    if item.customname and len(item.customname) > 100:
        raise ValueError("customname слишком длинное (max 100)")

    proto_bytes = _encode_item_proto(item)
    checksum = _compute_checksum(proto_bytes)
    payload = b'\x00' + proto_bytes + checksum

    if xor_key:
        payload = bytes(b ^ xor_key for b in payload)

    return payload.hex().upper()


def decode_inspect_url(url: str) -> Optional[ItemInfo]:
    """
    Декодирует CS2 inspect-URL в ItemInfo.

    - Masked/Hybrid формат → возвращает ItemInfo с float, stickers и т.д.
    - Classic формат (S/A/D с decimal D) → возвращает None (нужен GC).
    - Невалидный URL → возвращает None.
    """
    url = unquote(url)
    m = _INSPECT_RE.search(url)
    if not m:
        return None

    payload = m.group(1).strip()

    if _CLASSIC_RE.match(payload):
        return None

    hybrid = _HYBRID_RE.match(payload)
    if hybrid:
        try:
            return decode_hex(hybrid.group(1))
        except Exception:
            return None

    try:
        return decode_hex(payload)
    except Exception:
        return None


def is_masked(url: str) -> bool:
    """True если URL в masked/hybrid формате (декодируется offline)."""
    url = unquote(url)
    m = _INSPECT_RE.search(url)
    if not m:
        return False
    return not _CLASSIC_RE.match(m.group(1).strip())


def is_classic(url: str) -> bool:
    """True если URL в classic формате (нужен Steam Game Coordinator)."""
    url = unquote(url)
    m = _INSPECT_RE.search(url)
    if not m:
        return False
    return bool(_CLASSIC_RE.match(m.group(1).strip()))
