from xml.etree.ElementTree import Element

from forgeo.core.model import Model
from forgeo.io.xml.base import Serializer
from forgeo.io.xml.interpolator import InterpolatorSerializer
from forgeo.io.xml.item import ItemSerializer


class ModelSerializer(Serializer, target=Model, tag="Model"):
    @classmethod
    def dump_element(cls, model, e):
        e.attrib["name"] = model.name
        e.append(Element("Pile", {"name": model.pilename}))
        if model.faultnetname:
            e.append(Element("FaultNetwork", {"name": model.faultnetname}))
        if model.dataset is not None:
            node = Element("Dataset")
            for item in model.dataset:
                node.append(ItemSerializer.dump(item))
            e.append(node)
        if model.interpolators is not None:
            node = Element("Interpolators")
            for item in model.interpolators:
                node.append(InterpolatorSerializer.dump(item))
            e.append(node)

    @classmethod
    def load_element(cls, e):
        name = e.attrib.pop("name")
        dataset = None
        interpolators = None
        faultnetname = None
        for elem in e:
            if elem.tag == "Pile":
                pilename = elem.attrib["name"]
            elif elem.tag == "FaultNetwork":
                faultnetname = elem.attrib["name"]
            elif elem.tag == "Dataset":
                dataset = []
                for item_elem in elem:
                    assert item_elem.tag == "Item"
                    dataset.append(ItemSerializer.load(item_elem))
            elif elem.tag == "Interpolators":
                interpolators = []
                for interp_elem in elem:
                    assert interp_elem.tag == "Interpolator"
                    interpolators.append(InterpolatorSerializer.load(interp_elem))
        model = Model(name, pilename, dataset, interpolators, faultnetname)
        if interpolators:  # Resolve references to dataset items
            for interpolator in interpolators:
                items = []
                for incomplete_item in interpolator.dataset:
                    item = model.get_item(incomplete_item.name)
                    item.type = incomplete_item.type
                    items.append(item)
                    model.set_item(item)
                interpolator.dataset = items
            for item in model.dataset:
                if not item.type:
                    item.type = "Unit"
        return model
