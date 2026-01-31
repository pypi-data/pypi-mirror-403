from forgeo.core.erosion import Erosion
from forgeo.core.unit import ModellingUnit
from forgeo.io.xml.base import Serializer
from forgeo.io.xml.erosion import ErosionSerializer


class ModellingUnitSerializer(Serializer, target=ModellingUnit, tag="ModellingUnit"):
    @classmethod
    def dump_element(cls, unit, e):
        e.attrib["name"] = unit.name
        if unit.info:
            for key, value in unit.info.items():
                e.attrib[key] = value
        if unit.hasChildren():
            for subunit in unit.description:
                if isinstance(subunit, Erosion):
                    e.append(ErosionSerializer.dump(subunit))
                else:
                    e.append(ModellingUnitSerializer.dump(subunit))

    @classmethod
    def load_element(cls, e):
        if e.tag == cls.tag:
            # Name
            name = e.attrib["name"]
            # Info
            if len(e.attrib.items()) > 1:
                info = {}
                for key, value in e.attrib.items():
                    if key != "name":
                        info[key] = value
                pile = ModellingUnit(name=name, info=info)
            else:
                pile = ModellingUnit(name=name)
            # Children
            if len(e) > 0:
                for subunit in e:
                    if subunit.tag == cls.tag:
                        pile.description.append(cls.load(subunit))
                    elif subunit.tag == ErosionSerializer.tag:
                        pile.description.append(ErosionSerializer.load(subunit))
            return pile
        return None
