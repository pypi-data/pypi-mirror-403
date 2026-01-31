import numpy as np

from forgeo.core import data
from forgeo.io.xml.base import Serializer
from forgeo.io.xml.utils import (
    CompoundSerializer,
    TableSerializer,
    dump_array_node,
    load_array_node,
)


class NpArray(Serializer, target=np.ndarray, tag="Array"):
    @staticmethod
    def dump_element(a, e, **kwargs):
        dump_array_node(a, e, **kwargs)

    @staticmethod
    def load_element(e):
        return load_array_node(e)


class Locations(Serializer, TableSerializer, target=data.Locations, tag="Locations"):
    pass


class UnitNormals(
    Serializer, TableSerializer, target=data.UnitNormals, tag="UnitNormals"
):
    pass


class DipDirMeasurements(
    Serializer,
    TableSerializer,
    target=data.DipDirMeasurements,
    tag="DipDirMeasurements",
):
    pass


class Orientations(
    Serializer,
    CompoundSerializer,
    target=data.Orientations,
    tag="Orientations",
    vars=("locations", "normals"),
):
    pass


class ItemData(
    Serializer,
    CompoundSerializer,
    target=data.ItemData,
    tag="ItemData",
    vars=("observations", "orientations", "orientations_only"),
):
    pass


serializers = [
    NpArray,
    Locations,
    UnitNormals,
    DipDirMeasurements,
    Orientations,
    ItemData,
]
