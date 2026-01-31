import ast

from forgeo.core.data import Ellipsoid
from forgeo.io.xml.base import Serializer


class EllipsoidSerializer(Serializer, target=Ellipsoid, tag="Ellipsoid"):
    @classmethod
    def dump_element(cls, ellipsoid, e):
        e.attrib["center"] = str([float(v) for v in ellipsoid.center])
        e.attrib["radius"] = str([float(v) for v in ellipsoid.radius])

    @classmethod
    def load_element(cls, e):
        center = ast.literal_eval(e.attrib["center"])
        radius = ast.literal_eval(e.attrib["radius"])
        return Ellipsoid(center, radius)
