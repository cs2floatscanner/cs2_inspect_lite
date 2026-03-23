"""Тесты с известными тест-векторами из спецификации CS2 inspect."""

import struct
import pytest
from cs2_inspect_lite import decode_hex, encode_hex, decode_inspect_url, is_masked, is_classic
from cs2_inspect_lite import ItemInfo, Sticker


# ── Тест-вектор 1: Native CS2 link (XOR key 0xE3) ─────────

VECTOR1_HEX = (
    "E3F3367440334DE2FBE4C345E0CBE0D3E7DB6943400AE0A379E481ECEBE2F36F"
    "D9DE2BDB515EA6E30D74D981ECEBE3F37BCBDE640D475DA6E35EFCD881ECEBE3"
    "F359D5DE37E9D75DA6436DD3DD81ECEBE3F366DCDE3F8F9BDDA69B43B6DE81EC"
    "EBE3F33BC8DEBB1CA3DFA623F7DDDF8B71E293EBFD43382B"
)


def test_vector1_decode():
    item = decode_hex(VECTOR1_HEX)
    assert item.itemid == 46876117973
    assert item.defindex == 7
    assert item.paintindex == 422
    assert item.paintseed == 922
    assert abs(item.paintwear - 0.04121) < 0.001
    assert item.rarity == 3
    assert item.quality == 4
    assert len(item.stickers) == 5
    sticker_ids = [s.sticker_id for s in item.stickers]
    assert sticker_ids == [7436, 5144, 6970, 8069, 5592]


# ── Тест-вектор 2: Tool-generated link (key 0x00) ─────────

VECTOR2_HEX = "00183C20B803280538E9A3C5DD0340E102C246A0D1"


def test_vector2_decode():
    item = decode_hex(VECTOR2_HEX)
    assert item.defindex == 60
    assert item.paintindex == 440
    assert item.paintseed == 353
    assert abs(item.paintwear - 0.005411) < 0.001
    assert item.rarity == 5


def test_vector2_roundtrip():
    """Декодирование → кодирование → декодирование должно сохранить данные."""
    original = decode_hex(VECTOR2_HEX)
    re_encoded = encode_hex(original, xor_key=0)
    restored = decode_hex(re_encoded)

    assert restored.defindex == original.defindex
    assert restored.paintindex == original.paintindex
    assert restored.paintseed == original.paintseed
    assert restored.rarity == original.rarity
    assert abs(restored.paintwear - original.paintwear) < 1e-6


# ── URL-парсинг ──────────────────────────────────────────

def test_masked_url():
    url = f"steam://run/730//+csgo_econ_action_preview%20{VECTOR2_HEX}"
    assert is_masked(url) is True
    assert is_classic(url) is False
    item = decode_inspect_url(url)
    assert item is not None
    assert item.defindex == 60


def test_classic_url():
    url = "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20S76561199842063946A49749521570D2751293026650298712"
    assert is_classic(url) is True
    assert is_masked(url) is False
    assert decode_inspect_url(url) is None


def test_hybrid_url():
    url = f"steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20S76561199323320483A50075495125D{VECTOR2_HEX}"
    assert is_masked(url) is True
    assert is_classic(url) is False
    item = decode_inspect_url(url)
    assert item is not None
    assert item.defindex == 60


# ── Encode ────────────────────────────────────────────────

def test_encode_plain():
    item = ItemInfo(defindex=60, paintindex=440, paintseed=353,
                    paintwear=0.005411375779658556, rarity=5)
    result = encode_hex(item, xor_key=0)
    assert result == VECTOR2_HEX.upper()


def test_encode_with_stickers():
    item = ItemInfo(
        defindex=7, paintindex=422, paintseed=922,
        paintwear=0.04121, rarity=3, quality=4,
        stickers=[Sticker(slot=0, sticker_id=7436)],
    )
    hex_str = encode_hex(item)
    restored = decode_hex(hex_str)
    assert restored.defindex == 7
    assert restored.paintseed == 922
    assert len(restored.stickers) == 1
    assert restored.stickers[0].sticker_id == 7436


def test_encode_validates_paintwear():
    with pytest.raises(ValueError, match="paintwear"):
        encode_hex(ItemInfo(paintwear=1.5))


# ── Ошибки ────────────────────────────────────────────────

def test_too_short():
    with pytest.raises(ValueError, match="короткий"):
        decode_hex("0011")


def test_invalid_hex():
    with pytest.raises(ValueError):
        decode_hex("ZZZZZZ")


def test_invalid_url():
    assert decode_inspect_url("https://example.com") is None
