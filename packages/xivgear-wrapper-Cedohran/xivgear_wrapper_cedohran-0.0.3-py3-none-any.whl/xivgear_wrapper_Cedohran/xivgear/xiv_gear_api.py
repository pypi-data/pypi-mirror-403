from typing import Dict, List
import requests

from xivgear_wrapper_Cedohran.xivgear.xiv_gear_item import XIVGearItem, XIVGearSlot
from xivgear_wrapper_Cedohran.xivgear.xiv_gear_set import XIVGearSet

class XIVGearAPI:
    def __init__(self):
        self.base_url = "https://api.xivgear.app/shortlink/"
        # test connection https://xivgear.app/docs/
        response = requests.get("https://xivgear.app/docs/")
        if response.status_code != 200:
            raise Exception(f"Could not connect to xivgear API")


    def get_all_gearsets(self, sheetid: str) -> List[XIVGearSet]:
        """
        Retrieves gearsets by given sheet ID via xivgear API
        
        :param sheetid: the sheet ID from the xivgear URL
        :type sheetid: str
        :return: returns a list of XIVGearSet objects
        :rtype: XIVGearSet
        """
        response = requests.get(f"{self.base_url}{sheetid}")
        sheet_json: Dict = {}
        gearsets: List[XIVGearSet] = []

        # check response
        if response.status_code == 200:
            sheet_json = response.json()
        else:
            raise Exception(f"Error getting gearset data: {response}")
        
        # all the sets contained in the sheet
        try:
            sheet_sets: List = sheet_json["sets"]
        except KeyError:
            # maybe there is only one set in the sheet
            sheet_sets = [sheet_json]

        # read all the gearsets
        for gearset in sheet_sets:
            # read set items
            set_items: List[XIVGearItem] = []
            for slot, info in gearset["items"].items():
                set_item_materia = [item["id"] for item in info["materia"]]
                set_items.append(XIVGearItem(itemid=info["id"],
                                                    gear_slot=XIVGearSlot(slot),
                                                    materia=set_item_materia))
            # check if food is set
            try:
                wanted_food = gearset["food"]
            except:
                wanted_food = ""
            # create the set
            new_set = XIVGearSet(name=gearset["name"],
                                    description=gearset["description"],
                                    items=set_items,
                                    food=wanted_food)
            gearsets.append(new_set)

        return gearsets


    def get_gearset(self, sheetid: str, set_name: str) -> XIVGearSet:
        """
        Retrieves gearsets by given sheet ID via xivgear API and filters by set name
        
        :param sheetid: the sheet ID from the xivgear URL
        :type sheetid: str
        :param set_name: wanted gearset name
        :type set_name: str
        :return: the gearset as a XIVGearSet object
        :rtype: XIVGearSet
        """
        response = requests.get(f"{self.base_url}{sheetid}")
        sheet_json: Dict = {}
        wanted_set: XIVGearSet = None # type: ignore

        # check response
        if response.status_code == 200:
            sheet_json = response.json()
        else:
            raise Exception(f"Error getting gearset data: {response}")
        
        # all the sets contained in the sheet
        try:
            sheet_sets: List = sheet_json["sets"]
        except KeyError:
            # maybe there is only one set in the sheet
            sheet_sets = [sheet_json]

        # find the wanted set
        for gearset in sheet_sets:
            if gearset["name"] == set_name:
                # read all the items contained in the wanted set
                wanted_set_items: List[XIVGearItem] = []
                for slot, info in gearset["items"].items():
                    wanted_item_materia = [item["id"] for item in info["materia"]]
                    wanted_set_items.append(XIVGearItem(itemid=info["id"],
                                                        gear_slot=XIVGearSlot(slot),
                                                        materia=wanted_item_materia))
                # check if food is set
                try:
                    wanted_food = gearset["food"]
                except:
                    wanted_food = ""
                # create the set
                wanted_set = XIVGearSet(name=gearset["name"],
                                        description=gearset["description"],
                                        items=wanted_set_items,
                                        food=wanted_food)
                
        return wanted_set
