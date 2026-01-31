from copy import deepcopy

import numpy as np

from ..utils import BBox
from .data import InterpolationMethod, Interpolator, Item


class FaultNetwork:
    """Represents the fault network.

    Attributes
    ----------
    name : str
        The name of the fault network.
    dataset : list of FaultItem, optional
        List of FaultItem objects that have data for the fault network.
    active_faults : list, optional
        active or unactive state for each fault
    relations : np.ndarray (nb_faults, nb_faults), optionnal
        matrix representing the faults relations.
        relations[i, j] != 0 if fault i stops on fault j
        relations[i, j] = 0 else
    interpolators : list of Interpolator, optional
        List of Interpolator objects that will be used to represent the fault network.
    """

    def __init__(
        self,
        name=None,
        dataset=None,
        active_faults=None,
        relations=None,
        interpolators=None,
    ):
        # FIXME Could we directly set dataset / interpolators /relations to empty
        # lists / arrays if None is passed as input?
        # This would avoid many tedious "not None" checks later...
        self.name = name or "Fault network"
        if dataset is not None:
            for item in dataset:
                assert isinstance(item, Item)
            fnames = [f.name for f in dataset]
            assert len(set(fnames)) == len(fnames), "Do not duplicate faults names"
        self.dataset = dataset
        if active_faults is None:
            active_faults = [True] * self.nb_faults
        else:
            assert self.nb_faults == len(active_faults)
        self.active_faults = active_faults
        if relations is None:
            relations = np.zeros((self.nb_faults, self.nb_faults), dtype=np.bool_)
        else:
            relations = np.asarray(relations, dtype=np.bool_)
            assert relations.ndim == 2
            assert len(relations) == self.nb_faults
            assert relations.shape[0] == relations.shape[1]
        self.relations = relations
        if interpolators is None:
            if dataset is not None:
                method = InterpolationMethod.get_default_method()
                interpolators = [Interpolator(method, [item]) for item in dataset]
        else:
            assert len(interpolators) == self.nb_faults
            assert all(isinstance(interp, Interpolator) for interp in interpolators)
        self.interpolators = interpolators

    @property
    def nb_faults(self):
        return len(self.dataset) if self.dataset is not None else 0

    def __repr__(self):
        """Returns a string representation of the faults in the fault network"""
        if self.dataset:
            return self.name + f" : {[item.name for item in self.dataset]}"
        return self.name

    def get_item(self, item_name):
        for item in self.dataset:
            if item.name == item_name:
                return item
        return None

    def set_item(self, item):
        """Replaces an item with the same name than previously,
        otherwises nothing changes."""
        assert isinstance(item, Item)
        for idx, cur_item in enumerate(self.dataset):
            if cur_item.name == item.name:
                self.dataset[idx] = item

    def items_bounding_box(self):
        """Return the bouding box of all item data locations."""
        bbox = BBox()
        if dataset := self.dataset:
            for item in dataset:
                bbox.union(item.bounding_box)
        return bbox

    def get_interpolator(self, fault_name):
        for interp in self.interpolators:
            if fault_name == interp.dataset[0].name:
                return interp
        return None

    def set_interpolator(self, interp):
        """Replaces an interpolator whose data (fault) has the same name than previously,
        otherwises nothing changes."""
        assert isinstance(interp, Interpolator)
        fault = interp.dataset[0]
        for idx, cur_interp in enumerate(self.interpolators):
            if fault.name in [f.name for f in cur_interp.dataset]:
                self.interpolators[idx] = interp

    def add_fault(self, fault, is_active=True):
        """Adds a fault to the network.

        Parameters
        ----------
        fault : Item
            The fault to add.
        is_active : bool, optional
            True if the fault must be used during interpolation, else False.
        """
        if self.dataset is None:
            self.dataset = []
            self.interpolators = []
        assert isinstance(fault, Item)
        assert fault.name not in [f.name for f in self.dataset], (
            "Do not duplicate faults names"
        )
        self.dataset.append(fault)
        self.active_faults.append(is_active)
        relations = np.zeros((self.nb_faults, self.nb_faults), dtype=np.bool_)
        relations[:-1, :-1] = self.relations
        self.relations = relations
        self.interpolators.append(
            Interpolator(InterpolationMethod.get_default_method(), [fault])
        )

    def delete_fault(self, fault):
        """Deletes a fault from the network.

        Parameters
        ----------
        fault : Item
            The fault to delete.
        """
        # FIXME Authorize passing a fault name as input?
        assert isinstance(fault, Item)  # FIXME FaultItem?
        if fault in self.dataset:
            idx = self.get_fault_index(fault.name)
            del self.active_faults[idx]
            del self.dataset[idx]
            self.relations = np.delete(self.relations, idx, axis=0)
            self.relations = np.delete(self.relations, idx, axis=1)
            del self.interpolators[idx]
            if self.nb_faults == 0:
                self.dataset = None
                self.interpolators = None

    def rename_fault(self, fault, new_name):
        """Renames a fault from the network. and its interpolators

        Parameters
        ----------
        fault : Item
            The fault to rename.
        new_name : str
            The new name.
        """
        # FIXME Authorize passing a fault name as input?
        assert self.get_item(new_name) is None, "Fault name already used"
        # Rename in interpolator dataset
        interp = self.get_interpolator(fault.name)
        interp.dataset = [fault]
        self.set_interpolator(interp)
        # Rename in fault network dataset
        f = self.get_item(fault.name)
        f.name = new_name
        # Rename fault object
        fault.name = new_name

    def stops_on(self, f1_name, f2_name):
        """Tells if f1 stops on f2

        Parameters
        ----------
        f1_name, f2_name : str
            The names of the faults.
        """
        f1_idx = self.get_fault_index(f1_name)
        f2_idx = self.get_fault_index(f2_name)
        return self.relations[f1_idx, f2_idx]

    def is_active(self, name):
        """Tells if the fault is currently active in the network.

        Parameters
        ----------
        name : str
            The name of the fault whose state is requested.
        """
        idx = self.get_fault_index(name)
        assert idx is not None, "Fault not found in fault network"
        return self.active_faults[idx]

    def set_as_active(self, name, state):
        """Set the state of the fault (active or not) in the network.

        Parameters
        ----------
        name : str
            The name of the fault.
        state : bool
            The new state: True if the fault is active else False
        """
        idx = self.get_fault_index(name)
        assert idx is not None, "Fault not found in fault network"
        self.active_faults[idx] = state

    def get_fault_index(self, name):
        """Get the index of a fault in the dataset.

        Parameters
        ----------
        name : str
            The name of the fault to find.
        """
        try:
            return next(i for i, f in enumerate(self.dataset) if f.name == name)
        except StopIteration:  # No field matching the input use
            return None

    def get_subnetwork(self, faults_to_keep):
        """Returns a new (deep-copied) FaultNetwork object, containing only the
        faults listed in `faults_to_keep`

        Parameters
        ----------
        faults_to_keep: list[str | FaultItem]

        Return
        ------
        network: FaultNetwork
        """
        if not faults_to_keep:
            return self.__class__(name=self.name)

        # network = FaultNetworkSerializer.dump(self)
        network = deepcopy(self)
        faults_to_keep = [
            name if isinstance(name, str) else name.name for name in faults_to_keep
        ]
        faults_to_remove = [
            item for item in network.dataset if item.name not in faults_to_keep
        ]
        for item in faults_to_remove:
            network.delete_fault(item)
        return network
