import ast
from xml.etree.ElementTree import Element

import numpy as np

from forgeo.core import Variogram
from forgeo.io.xml.base import Serializer


class VariogramSerializer(Serializer, target=Variogram, tag="Variogram"):
    @classmethod
    def dump_element(cls, vario, e):
        e.attrib["model"] = vario.model
        if vario.range is not None:
            node = Element("Range")
            if isinstance(vario.range, float):
                node.attrib["value"] = str(vario.range)
            elif isinstance(vario.range, np.ndarray):
                aniso_node = Element("Anisotropy")
                if vario.range.shape == (3,):
                    aniso_node.attrib["values"] = str([float(v) for v in vario.range])
                elif vario.range.shape == (3, 3):
                    for axis in vario.range:
                        axis_node = Element("Axis")
                        axis_node.attrib["coords"] = str([float(v) for v in axis])
                        aniso_node.append(axis_node)
                node.append(aniso_node)
            e.append(node)
        if vario.sill is not None:
            node = Element("Sill")
            if isinstance(vario.sill, float):
                node.attrib["value"] = str(vario.sill)
            elif isinstance(vario.sill, np.ndarray):
                aniso_node = Element("Anisotropy")
                aniso_node.attrib["values"] = str([float(v) for v in vario.sill])
                node.append(aniso_node)
            e.append(node)
        if vario.nugget is not None:
            node = Element("Nugget")
            if isinstance(vario.nugget, float):
                node.attrib["value"] = str(vario.nugget)
            e.append(node)

    @classmethod
    def load_element(cls, e):
        model = e.attrib["model"]
        range = None
        sill = None
        nugget = None
        for elem in e:
            if elem.tag == "Range":
                if "value" in elem.attrib:
                    range = float(elem.attrib["value"])
                else:
                    aniso_elem = elem[0]
                    elem.remove(aniso_elem)
                    if "values" in aniso_elem.attrib:
                        range = ast.literal_eval(aniso_elem.attrib["values"])
                    else:
                        range = np.zeros((3, 3))
                        for i, axis_elem in enumerate(aniso_elem):
                            range[i] = ast.literal_eval(axis_elem.attrib["coords"])
                    range = np.asarray(range)
            elif elem.tag == "Sill":
                if "value" in elem.attrib:
                    sill = float(elem.attrib["value"])
                else:
                    aniso_elem = elem[0]
                    elem.remove(aniso_elem)
                    sill = ast.literal_eval(aniso_elem.attrib["values"])
                    sill = np.asarray(sill)
            elif elem.tag == "Nugget" and "value" in elem.attrib:
                nugget = float(elem.attrib["value"])
        return Variogram(model, range, sill, nugget)
