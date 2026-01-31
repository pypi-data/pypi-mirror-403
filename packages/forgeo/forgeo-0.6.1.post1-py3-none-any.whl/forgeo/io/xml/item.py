import ast

from forgeo.core import Item
from forgeo.io.xml.base import Serializer
from forgeo.io.xml.custom import ItemData as ItemDataSerializer


class ItemSerializer(Serializer, target=Item, tag="Item"):
    @classmethod
    def dump_element(cls, item, e):
        e.attrib["name"] = item.name
        e.attrib["is_surface"] = str(item.is_surface)
        if item.info:
            for key, value in item.info.items():
                e.attrib[key] = value
        if (type_ := item.type) is not None:
            e.attrib["type"] = type_
        if item.item_data is not None:
            e.append(ItemDataSerializer.dump(item.item_data))

    @classmethod
    def load_element(cls, e):
        name = e.attrib.pop("name")
        is_surface = ast.literal_eval(e.attrib.pop("is_surface"))
        type_ = e.attrib.pop("type", None)
        info = None
        if e.attrib:
            info = dict(e.attrib.items())
        item_data = None
        for elem in e:
            if elem.tag == ItemDataSerializer.tag:
                item_data = ItemDataSerializer.load(elem)
        return Item(name, info, is_surface, item_data, type_)
