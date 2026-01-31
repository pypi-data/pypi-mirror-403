from typing import List
from enum import Enum


class XIVGearSlot(str, Enum):
    WEAPON = "Weapon"
    HEAD = "Head"
    BODY = "Body"
    HAND = "Hand"
    LEGS = "Legs"
    FEET = "Feet"
    EARS = "Ears"
    NECK = "Neck"
    WRIST = "Wrist"
    RING_RIGHT = "RingRight"
    RING_LEFT = "RingLeft"


class GearTier(str, Enum):
    UNKNOWN = "UNKNOWN"
    OTHER = "OTHER"
    CRAFTED = "CRAFTED"
    TOME = "TOME"
    TOME_UPGRADED = "TOME_UPGRADED"
    EX_TRIAL = "EX_TRIAL"
    NORMAL_RAID = "NORMAL_RAID"
    SAVAGE = "SAVAGE"
    RELIC = "RELIC"


class XIVGearItem():
    def __init__(self, itemid: str,
                 gear_slot: XIVGearSlot,
                 materia: List[str]):
        self.itemid = itemid
        self.gear_slot = gear_slot
        self.materia = materia

    def __eq__(self, other):
        # enable == None
        if self.itemid == "None":
            return None

        # don't attempt to compare against unrelated types
        if not isinstance(other, XIVGearItem):
            return NotImplemented
        
        return self.itemid == other.itemid

    def __str__(self):
        return ""