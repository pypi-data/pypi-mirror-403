from typing import List
from xivgear_wrapper_Cedohran.xivgear.xiv_gear_item import XIVGearItem, XIVGearSlot


class XIVGearSet():
    def __init__(self, name: str,
                 description: str,
                 items: List[XIVGearItem],
                 food: str):
        self.name = name
        self.description = description
        self.items = items
        self.food = food

    def weapon(self) -> XIVGearItem:
        """
        :return: the weapon item as a XIVGearItem object
        :rtype: XIVGearItem
        """
        weapon = None
        weapon = [item for item in self.items if item.gear_slot == XIVGearSlot.WEAPON].pop()
        return weapon

    def head(self) -> XIVGearItem:
        """
        :return: the head item as a XIVGearItem object
        :rtype: XIVGearItem
        """
        head = None
        head = [item for item in self.items if item.gear_slot == XIVGearSlot.HEAD].pop()
        return head

    def body(self) -> XIVGearItem:
        """
        :return: the body item as a XIVGearItem object
        :rtype: XIVGearItem
        """
        body = None
        body = [item for item in self.items if item.gear_slot == XIVGearSlot.BODY].pop()
        return body

    def hand(self) -> XIVGearItem:
        """
        :return: the hand item as a XIVGearItem object
        :rtype: XIVGearItem
        """
        hand = None
        hand = [item for item in self.items if item.gear_slot == XIVGearSlot.HAND].pop()
        return hand

    def legs(self) -> XIVGearItem:
        """
        :return: the legs item as a XIVGearItem object
        :rtype: XIVGearItem
        """
        legs = None
        legs = [item for item in self.items if item.gear_slot == XIVGearSlot.LEGS].pop()
        return legs

    def feet(self) -> XIVGearItem:
        """
        :return: the feet item as a XIVGearItem object
        :rtype: XIVGearItem
        """
        feet = None
        feet = [item for item in self.items if item.gear_slot == XIVGearSlot.FEET].pop()
        return feet

    def ears(self) -> XIVGearItem:
        """
        :return: the ears item as a XIVGearItem object
        :rtype: XIVGearItem
        """
        ears = None
        ears = [item for item in self.items if item.gear_slot == XIVGearSlot.EARS].pop()
        return ears

    def neck(self) -> XIVGearItem:
        """
        :return: the neck item as a XIVGearItem object
        :rtype: XIVGearItem
        """
        neck = None
        neck = [item for item in self.items if item.gear_slot == XIVGearSlot.NECK].pop()
        return neck

    def wrist(self) -> XIVGearItem:
        """
        :return: the wrist item as a XIVGearItem object
        :rtype: XIVGearItem
        """
        wrist = None
        wrist = [item for item in self.items if item.gear_slot == XIVGearSlot.WRIST].pop()
        return wrist

    def ring_right(self) -> XIVGearItem:
        """
        :return: the right ring item as a XIVGearItem object
        :rtype: XIVGearItem
        """
        ring_right = None
        ring_right = [item for item in self.items if item.gear_slot == XIVGearSlot.RING_RIGHT].pop()
        return ring_right

    def ring_left(self) -> XIVGearItem:
        """
        :return: the left ring item as a XIVGearItem object
        :rtype: XIVGearItem
        """
        ring_left = None
        ring_left = [item for item in self.items if item.gear_slot == XIVGearSlot.RING_LEFT].pop()
        return ring_left