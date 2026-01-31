from forgeo.core.erosion import Erosion
from forgeo.io.xml.base import Serializer


class ErosionSerializer(Serializer, target=Erosion, tag="Erosion"):
    @classmethod
    def dump_element(cls, erosion, e):
        e.attrib["name"] = erosion.name
        if erosion.info:
            for key, value in erosion.info.items():
                e.attrib[key] = value

    @classmethod
    def load_element(cls, e):
        name = e.attrib.pop("name")
        info = dict(e.attrib.items())
        return Erosion(name, info=info or None)
