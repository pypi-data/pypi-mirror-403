from xml.etree.ElementTree import Element

from forgeo.core import Interpolator, Item
from forgeo.io.xml.base import Serializer
from forgeo.io.xml.neighborhood import NeighborhoodSerializer
from forgeo.io.xml.utils import add_child_text_node
from forgeo.io.xml.variogram import VariogramSerializer


class InterpolatorSerializer(Serializer, target=Interpolator, tag="Interpolator"):
    @classmethod
    def dump_element(cls, interp, e):
        e.attrib["method"] = interp.method
        if interp.dataset is not None:
            node = Element("Items")
            for item in interp.dataset:
                attrib = {"name": item.name}
                if item.type is not None:
                    attrib["type"] = item.type
                node.append(Element("Item", attrib))
            e.append(node)
        if interp.discontinuities is not None:
            node = Element("Discontinuities")
            for name in interp.discontinuities:
                node.append(Element("Fault", {"name": name}))
            e.append(node)
        node_params = Element("Parameters")
        if (variograms := interp.variograms) is not None:
            for vario in variograms:
                node_params.append(VariogramSerializer.dump(vario))
        if (drift_order := interp.drift_order) is not None:
            add_child_text_node(node_params, "DriftOrder", str(drift_order))
        if (neigh := interp.neighborhood) is not None:
            node_params.append(NeighborhoodSerializer.dump(neigh))
        if len(node_params) != 0:
            e.append(node_params)

    @classmethod
    def load_element(cls, e):
        method = e.attrib["method"]
        items = None
        discontinuities = None
        variograms = None
        drift_order = None
        neighborhood = None
        for elem in e:
            if elem.tag == "Items":
                items = []
                for item_elem in elem:
                    if item_elem.tag == "Item":
                        item = Item(item_elem.attrib["name"])
                        if "type" in item_elem.attrib:
                            item.type = item_elem.attrib["type"]
                        info = {}
                        for key, value in item_elem.attrib.items():
                            if key not in ("name", "type", "is_surface"):
                                info[key] = value
                        if len(info) != 0:
                            item.info = info
                        items.append(item)
            elif elem.tag == "Discontinuities":
                discontinuities = []
                for fault_elem in elem:
                    discontinuities.append(fault_elem.attrib["name"])
            elif elem.tag == "Parameters":
                variograms = []
                for param in elem:
                    if param.tag == VariogramSerializer.tag:
                        variograms.append(VariogramSerializer.load(param))
                    elif param.tag == "DriftOrder":
                        drift_order = int(param.text)
                    elif param.tag == NeighborhoodSerializer.tag:
                        neighborhood = NeighborhoodSerializer.load(param)
        return Interpolator(
            method, items, discontinuities, variograms, drift_order, neighborhood
        )
