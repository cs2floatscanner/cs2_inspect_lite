# cs2-inspect-lite

Минималистичная Pure Python библиотека для декодирования и кодирования CS2 inspect-ссылок и `propid:6` данных.

**Без внешних зависимостей** — встроенный protobuf парсер.

## Установка

```bash
pip install cs2-inspect-lite
```

Или из исходников:

```bash
pip install .
```

## Быстрый старт

### Декодирование propid:6 (данные с маркета)

```python
from cs2_inspect_lite import decode_hex

item = decode_hex("00183C20B803280538E9A3C5DD0340E102C246A0D1")

print(item.defindex)    # 60
print(item.paintindex)  # 440
print(item.paintseed)   # 353
print(item.paintwear)   # ~0.00541
print(item.rarity)      # 5
```

### Декодирование inspect-URL

```python
from cs2_inspect_lite import decode_inspect_url, is_masked, is_classic

# Masked/hybrid формат — декодируется offline
url = "steam://run/730//+csgo_econ_action_preview%20E3F336..."
item = decode_inspect_url(url)
if item:
    print(f"Float: {item.paintwear}")
    print(f"Paint seed: {item.paintseed}")
    for s in item.stickers:
        print(f"Sticker #{s.slot}: id={s.sticker_id}")

# Проверка формата
print(is_masked(url))   # True — можно декодировать
print(is_classic(url))  # False
```

### Кодирование

```python
from cs2_inspect_lite import encode_hex, ItemInfo, Sticker

item = ItemInfo(
    defindex=7,
    paintindex=422,
    paintseed=922,
    paintwear=0.04121,
    rarity=3,
    quality=4,
    stickers=[
        Sticker(slot=0, sticker_id=7436),
        Sticker(slot=1, sticker_id=5144, wear=0.1),
    ],
)

hex_str = encode_hex(item)            # plain формат (key=0)
hex_str = encode_hex(item, xor_key=0xE3)  # обфусцированный
```

## Поддерживаемые форматы URL

| Формат | Пример | Offline |
|--------|--------|---------|
| Masked | `steam://run/730//+csgo_econ_action_preview%20<hex>` | Да |
| Hybrid | `...S<id>A<id>D<hex_proto>` | Да |
| Classic | `...S<id>A<id>D<decimal>` | Нет (нужен GC) |

## Структура ItemInfo

| Поле | Тип | Описание |
|------|-----|----------|
| `defindex` | int | Тип оружия |
| `paintindex` | int | Индекс скина |
| `paintwear` | float | Float value (износ) |
| `paintseed` | int | Pattern seed |
| `rarity` | int | Редкость |
| `quality` | int | Качество |
| `stickers` | list[Sticker] | Наклейки |
| `keychains` | list[Sticker] | Брелоки |
| `itemid` | int | ID предмета |
| `customname` | str | Nametag |

## Тесты

```bash
pip install pytest
pytest tests/
```

## Лицензия

MIT
