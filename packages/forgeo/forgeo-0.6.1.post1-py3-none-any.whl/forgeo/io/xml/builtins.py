from forgeo.io.xml.ellipsoid import EllipsoidSerializer
from forgeo.io.xml.erosion import ErosionSerializer
from forgeo.io.xml.faultitem import FaultItemSerializer
from forgeo.io.xml.faultnetwork import FaultNetworkSerializer
from forgeo.io.xml.interpolator import InterpolatorSerializer
from forgeo.io.xml.item import ItemSerializer
from forgeo.io.xml.model import ModelSerializer
from forgeo.io.xml.neighborhood import NeighborhoodSerializer
from forgeo.io.xml.unit import ModellingUnitSerializer
from forgeo.io.xml.variogram import VariogramSerializer

serializers = [
    FaultItemSerializer,
    EllipsoidSerializer,
    ItemSerializer,
    InterpolatorSerializer,
    ErosionSerializer,
    ModellingUnitSerializer,
    ModelSerializer,
    FaultNetworkSerializer,
    NeighborhoodSerializer,
    VariogramSerializer,
]
