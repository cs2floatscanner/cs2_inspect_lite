"""
cs2_inspect_lite — минималистичная библиотека для декодирования/кодирования
CS2 inspect-ссылок и propid:6 данных.

Pure Python, без внешних зависимостей.

Основные функции:
    decode_hex(hex_str)        — декодировать hex-строку (propid:6 или inspect payload)
    encode_hex(item, xor_key)  — кодировать ItemInfo в hex-строку
    decode_inspect_url(url)    — декодировать inspect-URL (masked/hybrid → ItemInfo, classic → None)
    is_masked(url)             — True если URL декодируется offline
    is_classic(url)            — True если URL требует GC

Модели:
    ItemInfo  — полная информация о предмете (float, paintseed, stickers и т.д.)
    Sticker   — стикер/брелок
"""

from .models import ItemInfo, Sticker
from ._codec import (
    decode_hex,
    encode_hex,
    decode_inspect_url,
    is_masked,
    is_classic,
)

__all__ = [
    "ItemInfo",
    "Sticker",
    "decode_hex",
    "encode_hex",
    "decode_inspect_url",
    "is_masked",
    "is_classic",
]

__version__ = "0.1.0"
