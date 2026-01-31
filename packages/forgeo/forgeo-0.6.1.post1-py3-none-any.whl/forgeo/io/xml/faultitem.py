from forgeo.core import FaultItem
from forgeo.io.xml.base import Serializer
from forgeo.io.xml.ellipsoid import EllipsoidSerializer
from forgeo.io.xml.item import ItemSerializer


class FaultItemSerializer(Serializer, target=FaultItem, tag="Item"):
    @classmethod
    def dump_element(cls, item, e):
        ItemSerializer.dump_element(item, e)
        if item.extension is not None:
            e.append(EllipsoidSerializer.dump(item.extension))

    @classmethod
    def load_element(cls, e):
        item = ItemSerializer.load(e)
        extension = None
        for elem in e:
            if elem.tag == EllipsoidSerializer.tag:
                extension = EllipsoidSerializer.load(elem)
        return FaultItem(item.name, item.info, item.item_data, extension)
