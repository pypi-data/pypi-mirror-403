from typing import Dict, List
import requests


class XivAPI:
    def __init__(self):
        self.base_url = "https://v2.xivapi.com/api/"
        # test connection https://v2.xivapi.com/docs/welcome/
        response = requests.get("https://v2.xivapi.com/docs/welcome/")
        if response.status_code != 200:
            raise Exception(f"Could not connect to xivapi")

    def get_item_info(self, itemid: str, fields: List[str] = []) -> Dict[str, str]:
        """
        gets the item info for given item id and filters with given fields
        
        :param itemid: the id of the item (usually 5 digits)
        :type itemid: str
        :param fields: fields to filter by, !case sensitive! 
        ([xivapi docs](https://v2.xivapi.com/docs/guides/sheets/#filtering) for more)
        :type fields: List[str]
        :return: returns a dict of fields given (or everything if no filter)
        :rtype: Dict[str, str]
        """
        sub_url = "sheet/Item/"
        # build the fields filter
        if len(fields) > 0:
            filter_fields = "?fields="
        else:
            filter_fields = ""
        for field in fields:
            filter_fields += f"{field},"
        # cut last ','
        if len(filter_fields) > 0:
            filter_fields = filter_fields[:-1]
        # retrieve info
        response = requests.get(f"{self.base_url}{sub_url}{itemid}{filter_fields}")
        response_json: Dict = {}

        # check response
        if response.status_code == 200:
            response_json = response.json()
        else:
            raise Exception(f"Error getting gearset data: {response}")
        
        return response_json["fields"]