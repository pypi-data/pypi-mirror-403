import ast
from dataclasses import dataclass
from xml.etree.ElementTree import Element

import numpy as np

from forgeo.core.faultnetwork import FaultNetwork
from forgeo.io.xml.base import Serializer
from forgeo.io.xml.faultitem import FaultItemSerializer
from forgeo.io.xml.interpolator import InterpolatorSerializer


@dataclass
class FaultRelations:
    array: np.ndarray


class FaultRelationsSerializer(Serializer, target=FaultRelations, tag="FaultRelations"):
    @classmethod
    def dump_element(cls, relations, e):
        array = [[bool(b) for b in line] for line in relations.array]
        e.attrib["array"] = str(array)

    @classmethod
    def load_element(cls, e):
        assert len(e.attrib) == 1
        array = ast.literal_eval(e.attrib["array"])
        if array:
            array = np.asarray(array, dtype=np.bool_)
        else:
            array = np.empty((0, 0), dtype=np.bool_)
        return array


class FaultNetworkSerializer(Serializer, target=FaultNetwork, tag="FaultNetwork"):
    @classmethod
    def dump_element(cls, faultnet, e):
        e.attrib["name"] = faultnet.name
        e.append(
            Element(
                "ActiveFaults",
                {"array": str([bool(b) for b in faultnet.active_faults])},
            )
        )
        e.append(FaultRelationsSerializer.dump(FaultRelations(faultnet.relations)))
        if faultnet.dataset is not None:
            node = Element("Dataset")
            for item in faultnet.dataset:
                node.append(FaultItemSerializer.dump(item))
            e.append(node)
        if faultnet.interpolators is not None:
            node = Element("Interpolators")
            for interp in faultnet.interpolators:
                node.append(InterpolatorSerializer.dump(interp))
            e.append(node)

    @classmethod
    def load_element(cls, e):
        name = e.attrib.pop("name")
        dataset = None
        active_faults = None
        relations = None
        dataset = None
        interpolators = None
        for elem in e:
            if elem.tag == "Dataset":
                dataset = []
                for fault_elem in elem:
                    dataset.append(FaultItemSerializer.load(fault_elem))
            elif elem.tag == "ActiveFaults":
                active_faults = ast.literal_eval(elem.attrib["array"])
            elif elem.tag == "FaultRelations":
                relations = FaultRelationsSerializer.load(elem)
            elif elem.tag == "Interpolators":
                interpolators = []
                for interp_elem in elem:
                    assert interp_elem.tag == InterpolatorSerializer.tag
                    interpolators.append(InterpolatorSerializer.load(interp_elem))
        faultnet = FaultNetwork(name, dataset, active_faults, relations, interpolators)
        if interpolators:  # Resolve references to dataset items
            for interpolator in interpolators:
                items = []
                if interpolator.dataset is not None:
                    for incomplete_item in interpolator.dataset:
                        item = faultnet.get_item(incomplete_item.name)
                        item.type = incomplete_item.type
                        items.append(item)
                    interpolator.dataset = items
        return faultnet
