##############
### Disclaimer
### all this data is subject to change due to changes to game data, xivgear API or xivapi
##############


from xivgear_wrapper_Cedohran.xivapi.xiv_api import XivAPI
from xivgear_wrapper_Cedohran.xivgear.xiv_gear_api import XIVGearAPI


# Here we want to get a list of the names of the gear pieces in our gear set

def get_item_names_with_set_id():
    # initiate xivgear API and xivapi
    gear_api = XIVGearAPI()
    xiv_api = XivAPI()

    # retrieve the gearset you want
    gearset = gear_api.get_gearset("e7315100-1b7d-47ba-8158-14b26321d2d6", 	"i790 7.4 Best In Slot")

    # get the items IDs
    item_ids = []
    for item in gearset.items:
        item_ids.append(item.itemid)
    
    # get names of items using the items ids and xivapi
    gear_names = []
    for itemid in item_ids:
        name = xiv_api.get_item_info(itemid, ["Name"])["Name"]
        gear_names.append(name)

    print(gear_names)
