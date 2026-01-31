import ast
from math import isnan
from xml.etree.ElementTree import Element

from forgeo.core import Neighborhood
from forgeo.io.xml.base import Serializer


class NeighborhoodSerializer(Serializer, target=Neighborhood, tag="Neighborhood"):
    TAG_DISTANCE = "SearchDistance"
    TAG_NB_NEIGHBORS = "NumberOfNeighbors"
    TAG_SECTORS = "AngularSectors"

    @classmethod
    def dump_element(cls, neighborhood, e, **kwargs):  # noqa:ARG003
        is_unique = neighborhood.is_unique
        e.attrib["is_unique"] = str(is_unique)
        if is_unique:
            return
        # else > moving neighborhood: values cannot be None

        # Dump search distance (if any)
        if not isnan(distance := neighborhood.max_search_distance):
            e.append(Element(cls.TAG_DISTANCE, {"max": str(distance)}))
        # Dump number of neighbors
        e.append(
            Element(
                cls.TAG_NB_NEIGHBORS,
                {
                    "min": str(neighborhood.nb_min_neighbors),
                    "max": str(neighborhood.nb_max_neighbors),
                },
            )
        )
        # Dump information about sectors
        e.append(
            Element(
                cls.TAG_SECTORS,
                {
                    "number_of_sectors": str(neighborhood.nb_angular_sectors),
                    "max_neighbors_per_sector": str(
                        neighborhood.nb_max_neighbors_per_sector
                    ),
                },
            )
        )

    @classmethod
    def load_element(cls, e):
        is_unique = ast.literal_eval(e.attrib.pop("is_unique"))
        if is_unique:
            return Neighborhood.create_unique()
        params = {}
        for child in e:
            if child.tag == cls.TAG_DISTANCE:
                params["max_search_distance"] = float(child.attrib.get("max"))
            elif child.tag == cls.TAG_NB_NEIGHBORS:
                params["nb_min_neighbors"] = int(child.attrib.get("min"))
                params["nb_max_neighbors"] = int(child.attrib.get("max"))
            elif child.tag == cls.TAG_SECTORS:
                params["nb_angular_sectors"] = int(
                    child.attrib.get("number_of_sectors")
                )
                params["nb_max_neighbors_per_sector"] = int(
                    child.attrib.get("max_neighbors_per_sector")
                )
        return Neighborhood.create_moving(**params)
