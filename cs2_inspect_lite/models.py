"""Модели данных для CS2 inspect link декодирования."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Sticker:
    """Стикер или брелок на предмете."""
    slot: int = 0
    sticker_id: int = 0
    wear: Optional[float] = None
    scale: Optional[float] = None
    rotation: Optional[float] = None
    tint_id: int = 0
    offset_x: Optional[float] = None
    offset_y: Optional[float] = None
    offset_z: Optional[float] = None
    pattern: int = 0


@dataclass
class ItemInfo:
    """Полная информация о предмете CS2, извлечённая из inspect-ссылки или propid:6."""
    accountid: int = 0
    itemid: int = 0
    defindex: int = 0
    paintindex: int = 0
    rarity: int = 0
    quality: int = 0
    paintwear: float = 0.0
    paintseed: int = 0
    killeaterscoretype: int = 0
    killeatervalue: int = 0
    customname: str = ""
    stickers: List[Sticker] = field(default_factory=list)
    inventory: int = 0
    origin: int = 0
    questid: int = 0
    dropreason: int = 0
    musicindex: int = 0
    entindex: int = 0
    petindex: int = 0
    keychains: List[Sticker] = field(default_factory=list)
