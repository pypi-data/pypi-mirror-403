from ..utils import BBox
from .data import InterpolationMethod, Interpolator, Item
from .faultnetwork import FaultNetwork
from .unit import ModellingUnit


class Model:
    """Represents the model: a dataset and interpolation parameters
    associated to a pile and optionnally to a fault network

    Attributes
    ----------
    name : str
        The model name.
    pilename : str
        The name fo the pile used to build this model.
    dataset : list of Item, optional
        List of Item objects that have data for the model.
    interpolators : list of Interpolator, optional
        List of Interpolator objects that will be used to represent the model.
    faultnetname : str, optional
        The name of the fault network that affects this model.
    """

    def __init__(
        self, name, pilename=None, dataset=None, interpolators=None, faultnetname=None
    ):
        self.name = name
        self.pilename = pilename
        self.dataset = dataset  # TODO Implement as a dict
        self.interpolators = interpolators
        self.faultnetname = faultnetname

    def get_item(self, item_name):
        for item in self.dataset:
            if item.name == item_name:
                return item
        return None

    def set_item(self, item):
        assert isinstance(item, Item)
        try:
            idx = next(
                i for i, other in enumerate(self.dataset) if other.name == item.name
            )
            self.dataset[idx] = item
        except StopIteration:  # No field matching the input use
            self.dataset.append(item)  # FIXME Do we authorize this case?

    def get_interpolator(self, item_name):
        for interp in self.interpolators:
            for item in interp.dataset:
                if item.name == item_name:
                    return interp
        return None

    def items_bounding_box(self):
        """Return the bouding box of all item data locations."""
        bbox = BBox()
        if dataset := self.dataset:
            for item in dataset:
                bbox.union(item.bounding_box)
        return bbox

    def update_interpolator(self, other):
        """Copies the method, discontinuities and variograms of `other`,
        if `other.dataset` matches `self.dataset`.

        WARNING: this method steals the attributes of `other`, which is left in
        an invalid state after update.

        Otherwise, raises an Exception
        """
        assert isinstance(other, Interpolator)
        # Find the corresponding interpolator
        interpolator = None
        for interp in self.interpolators:
            interp_items = [item.name for item in interp.dataset]
            other_items = [item.name for item in other.dataset]
            if interp_items == other_items:
                interpolator = interp
                break
        if interpolator is None:
            msg = "None of this model interpolators matches the input interpolator dataset"
            raise ValueError(msg)
        # TODO Implement using serialization as deep_copy?
        interpolator.method = other.method  # str, no need to invalidate other
        interpolator.discontinuities = other.discontinuities
        other.discontinuities = None
        interpolator.variograms = other.variograms
        other.variograms = None
        interpolator.drift_order = other.drift_order  # int, no need to invalidate other
        interpolator.neighborhood = other.neighborhood
        other.neighborhood = None

    def get_elem_types(self):
        """Get a type for all elements of the model.

        Returns
        -------
        elem_type : dict
            Returns the type of of an element given its name. The possible types are
            ["Unit", "Erosion", "Surface only", "Base", "Top", "Conformable"].
        """
        elem_type = {}
        for interp in self.interpolators:
            if not interp.has_volume_data() and len(interp.dataset) == 1:
                item_name = interp.dataset[0].name
                if item_name.startswith("Contact ") and " - " in item_name:
                    elem_type[item_name] = "Surface only"
                else:
                    elem_type[item_name] = "Erosion"
                continue
            for item in interp.dataset:
                item_name = item.name
                if item.is_surface:
                    if item_name.startswith("Contact ") and " - " in item_name:
                        [e1, e2] = item_name[len("Contact ") :].split(" - ")
                        e1, e2 = self.get_item(e1), self.get_item(e2)
                        if e1 in interp.dataset and e2 in interp.dataset:
                            elem_type[item_name] = "Conformable"
                        elif e1 in interp.dataset and e2 not in interp.dataset:
                            elem_type[item_name] = "Top"
                        elif e1 not in interp.dataset and e2 in interp.dataset:
                            elem_type[item_name] = "Base"
                    else:
                        elem_type[item_name] = "Erosion"
                else:
                    elem_type[item_name] = "Unit"
        # Add elements of the model that are not in interpolators
        for item in self.dataset:
            if item.name not in elem_type:
                elem_type[item.name] = "Unit"
        return elem_type

    def initialize(self, pile):
        self.dataset = []
        prev_elem = None
        for elem in pile.subunits():
            if isinstance(elem, ModellingUnit):
                if prev_elem is not None:
                    contact = Item(
                        self.get_contact_name(prev_elem, elem),
                        is_surface=True,
                        type="Conformable",
                    )
                    self.dataset.append(contact)
                prev_elem = elem
                unit = Item(elem.name, elem.info, type="Unit")
                self.dataset.append(unit)
            else:
                prev_elem = None
                erosion = Item(elem.name, elem.info, is_surface=True, type="Erosion")
                self.dataset.append(erosion)
        self.update_interpolators()

    def update_interpolators(self):
        old_interpolators = self.interpolators
        new_interpolators = []
        current = []
        start_idx = 0
        nb_elements = len(self.dataset)
        for idx, item in enumerate(self.dataset):
            type_ = item.type
            if type_ in ["Erosion", "Surface only"]:
                if len(current) > 1:
                    new_interpolators.append(current)
                new_interpolators.append([item])
                current = []
                start_idx = idx + 1
            elif type_ == "Top":
                current.append(item)
                new_interpolators.append(current)
                current = []
                start_idx = idx + 1
            elif type_ == "Base":
                nb_current_items = len(current)
                assert nb_current_items > 0
                if nb_current_items > 1:
                    new_interpolators.append(current)
                else:
                    assert current[0].type == "Unit"
                current = [item]
                start_idx = idx
            else:  # Unit or Conformable contact
                assert type_ in ["Unit", "Conformable"]
                current.append(item)
                if idx == nb_elements - 1 and len(current) > 1:
                    new_interpolators.append(current)

        interpolation_method = InterpolationMethod.get_default_method()
        if old_interpolators:

            def interpolators_are_identical(idx):
                assert idx < len(new_interpolators)
                assert idx < len(old_interpolators)
                old_items = [item.name for item in old_interpolators[idx].dataset]
                new_items = [item.name for item in new_interpolators[idx]]
                return old_items == new_items

            start_idx = 0
            while start_idx < len(new_interpolators) and interpolators_are_identical(
                start_idx
            ):
                start_idx += 1
            end_idx = -1
            while (-end_idx) <= len(new_interpolators) and interpolators_are_identical(
                end_idx
            ):
                end_idx -= 1
            old_end_idx = 1 + len(old_interpolators) - end_idx
            new_end_idx = 1 + len(new_interpolators) - end_idx
            interpolators = old_interpolators[:start_idx]
            interpolators.extend(
                [
                    Interpolator(interpolation_method, items)
                    for items in new_interpolators[start_idx:new_end_idx]
                ]
            )
            interpolators.extend(old_interpolators[old_end_idx:])
        else:
            interpolators = [
                Interpolator(interpolation_method, items) for items in new_interpolators
            ]
        self.interpolators = interpolators

    def set_fault_network(self, fault_network):
        assert isinstance(fault_network, FaultNetwork)
        self.faultnetname = fault_network.name

    def remove_fault_network(self):
        self.faultnetname = None
        if (interpolators := self.interpolators) is not None:
            for interpolator in interpolators:
                interpolator.discontinuities = None

    @classmethod
    def create_from_pile(cls, name, pile):
        model = cls(name, pile.name)
        model.initialize(pile)
        return model

    @staticmethod
    def get_contact_name(unit_below, unit_above):
        return f"Contact {unit_below.name} - {unit_above.name}"
