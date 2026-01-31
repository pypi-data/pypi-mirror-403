import typing
from math import isnan, nan
from numbers import Number

import numpy as np
from attrs import cmp_using, define, field

from forgeo.utils import (
    BBox,
    Spatial,
    cmp_values,
    default_field,
    dim1_array_check,
    table_field,
)


@define
class Locations(Spatial):
    values = table_field((1, 2, 3))


@define
class UnitNormals(Spatial):
    values = table_field((2, 3))

    def as_unit_normals(self):
        return self


@define
class DipDirMeasurements:
    values = table_field(2)
    reverse_polarities = field(
        converter=lambda value: (
            None if value is None else np.asarray(value, dtype=bool)
        ),
        default=None,
        validator=dim1_array_check(),
        eq=cmp_using(eq=cmp_values),
    )

    def __attrs_post_init__(self):
        if np.any(self.dips < 0) or np.any(self.dips > 90):
            msg = "expecting a positive angle in degree for dips"
            raise ValueError(msg)
        if np.any(self.dirs < 0) or np.any(self.dirs > 360):
            msg = "expecting a positive angle in degree for dirs"
            raise ValueError(msg)
        if self.reverse_polarities is not None and len(self.reverse_polarities) != len(
            self.values
        ):
            msg = "expecting the same number of dips and polarities"
            raise ValueError(msg)

    @property
    def dips(self):
        return self.values[:, 0]

    @property
    def dirs(self):
        return self.values[:, 1]

    def as_unit_normals(self):
        """
        Convert dip dir measurements to unit normals assuming degrees.
        """
        theta = np.deg2rad(90 - self.dirs)
        dips_rad = np.deg2rad(self.dips)
        cphi = np.cos(dips_rad)
        sphi = np.sin(dips_rad)
        normals = np.vstack([np.cos(theta) * sphi, np.sin(theta) * sphi, cphi]).T
        if self.reverse_polarities is not None:
            normals[self.reverse_polarities] *= -1
        return UnitNormals(normals)


@define
class Orientations:
    locations: Locations = default_field(Locations)
    normals: UnitNormals = default_field(
        UnitNormals,
        converter=lambda values: (
            UnitNormals() if values is None else values.as_unit_normals()
        ),
    )

    def __attrs_post_init__(self):
        if (
            self.locations.ambient_space_dimension
            != self.normals.ambient_space_dimension
        ):
            msg = "expecting locations and normals with the same dimension"
            raise ValueError(msg)
        if len(self.locations) != len(self.normals):
            msg = "expecting the same number of locations and normals"
            raise ValueError(msg)

    @property
    def ambient_space_dimension(self):
        return self.locations.ambient_space_dimension

    def __bool__(self):
        return bool(self.locations)


@define
class ItemData:
    observations: Locations = default_field(Locations, kw_only=True)
    orientations: Orientations = default_field(Orientations, kw_only=True)
    orientations_only: Orientations = default_field(Orientations, kw_only=True)

    def __attrs_post_init__(self):
        if not (self.observations or self.orientations or self.orientations_only):
            msg = "items must have observations or orientations data"
            raise ValueError(msg)
        if self.observations and (
            (
                self.orientations
                and (
                    self.observations.ambient_space_dimension
                    != self.orientations.ambient_space_dimension
                )
            )
            or (
                self.orientations_only
                and (
                    self.observations.ambient_space_dimension
                    != self.orientations_only.ambient_space_dimension
                )
            )
        ):
            msg = "expecting observations and orientations with the same dimension"
            raise ValueError(msg)

    @classmethod
    def from_observations(cls, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and isinstance(args[0], Locations):
            return cls(observations=args[0])
        return cls(observations=Locations(*args, **kwargs))

    @classmethod
    def from_orientations(cls, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and isinstance(args[0], Orientations):
            return cls(orientations=args[0])
        return cls(orientations=Orientations(*args, **kwargs))

    @classmethod
    def from_orientations_only(cls, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and isinstance(args[0], Orientations):
            return cls(orientations_only=args[0])
        return cls(orientations_only=Orientations(*args, **kwargs))

    def has_observation_data(self):
        """Returns True if self has either observation or orientation
        data (as orientations are also used both as observations data)
        """
        return self.observations or self.orientations

    def has_orientation_data(self):
        """Returns True if self has either orientation or orientation_only data"""
        return self.orientations or self.orientations_only

    def has_observation_and_orientation_data(self):
        """Returns True if this item_data has both observation and orientation data"""
        return self.orientations or (self.observations and self.orientations_only)

    def nb_observation_data(self):
        nb_points = 0
        if self.observations:
            nb_points += len(self.observations.values)
        if self.orientations:
            nb_points += len(self.orientations.locations.values)
        return nb_points

    def nb_orientation_data(self):
        nb_points = 0
        if self.orientations:
            nb_points += len(self.orientations.locations.values)
        if self.orientations_only:
            nb_points += len(self.orientations_only.locations.values)
        return nb_points

    @property
    def all_observations(self) -> Locations:
        data = []
        if self.observations:
            data.append(self.observations)
        if self.orientations:
            data.append(self.orientations.locations)
        nb_arrays = len(data)
        if nb_arrays == 0:
            return None
        if nb_arrays == 1:
            return data[0]  # Already a Locations
        return Locations(np.vstack([data[0].values, data[1].values]))

    @property
    def all_orientations(self) -> Orientations:
        data = []
        if self.orientations:
            data.append(self.orientations)
        if self.orientations_only:
            data.append(self.orientations_only)
        nb_arrays = len(data)
        if nb_arrays == 0:
            return None
        if nb_arrays == 1:
            return data[0]  # Already an Orientations
        return Orientations(
            Locations(np.vstack([data[0].locations.values, data[1].locations.values])),
            UnitNormals(np.vstack([data[0].normals.values, data[1].normals.values])),
        )

    @property
    def ambient_space_dimension(self):
        if self.observations:
            return self.observations.ambient_space_dimension
        if self.orientations_only:
            return self.orientations_only.ambient_space_dimension
        return self.orientations.ambient_space_dimension


class InterpolationMethod:
    POTENTIAL = "potential"
    ELEVATION_KRIGING = "elevation_kriging"
    RASTER = "raster"
    _AUTHORIZED_METHODS: typing.ClassVar = [POTENTIAL, ELEVATION_KRIGING]
    _DEFAULT = POTENTIAL

    @classmethod
    def list_available_methods(cls):
        # Returns a copy to forbid modification
        return list(cls._AUTHORIZED_METHODS)

    @classmethod
    def declare_new_method(cls, cls_attribute_name, value):
        assert cls_attribute_name not in cls._AUTHORIZED_METHODS
        setattr(cls, cls_attribute_name, value)
        cls._AUTHORIZED_METHODS.append(value)

    @classmethod
    def is_available(cls, method):
        return method in cls._AUTHORIZED_METHODS

    @classmethod
    def set_default_method(cls, method):
        assert cls.is_available(method)
        cls._DEFAULT = method

    @classmethod
    def get_default_method(cls):
        return cls._DEFAULT


class Item:
    """Stores data of an item of the model.
    An item can represent a modelling unit, a contact, or a fault

    Attributes
    ----------
    name : str
        The name of the element.
    info : any, optional
        Additional information about the modelling unit.
    is_surface : bool, optional
        True if the item represents a surface, False if it represents a volume.
    item_data: ItemData, optional
        Data used associated with this element.
    """

    def __init__(self, name, info=None, is_surface=False, item_data=None, type=None):
        self.name = name
        self.info = info
        self.is_surface = is_surface
        self.item_data = item_data
        self.type = type  # Warning: Not serialized by default

    def __repr__(self):
        return f"Item: {self.type} {self.name}"

    def get_color(self):
        if (info := self.info) is not None:
            return info.get("color")
        return None

    @property
    def bounding_box(self):
        bbox = BBox()
        if data := self.item_data:
            if observations := data.observations:
                bbox.update(observations.values)
            for orientations in [data.orientations, data.orientations_only]:
                if orientations:
                    bbox.update(orientations.locations.values)
        return bbox


class FaultItem(Item):
    """Stores data of a fault

    Attributes
    ----------
    name : str
        The name of the element.
    info : any, optional
        Additional information about the modelling unit.
    item_data: ItemData, optional
        Data used associated with this element.
    extension: Ellipsoid, optionnal
        Ellipsoidal axtension of a finite fault
    """

    def __init__(self, name, info=None, item_data=None, extension=None):
        super().__init__(name, info, is_surface=True, item_data=item_data, type="Fault")
        if extension is not None:
            assert isinstance(extension, Ellipsoid)
        self.extension = extension

    def is_finite(self):
        return self.extension is not None

    def set_extension(self, center, radius):
        self.extension = Ellipsoid(center, radius)

    def get_principal_axes(self):
        """Returns the prncipal axes of the ellispoid bounding the fault

        The axes are computed using a PCA. The two first one are horizontal
        (they are supposed to be respectively along strike and along dip). The
        last one is vertical.

        If there are less than two "observation" points (observation / orientations),
        we cannot run the PCA and an identity matrix is returned instead.
        """

        if (data := self.item_data) is None:
            return None
        locations = data.all_observations
        if locations is None or len(locations.values) < 2:
            # Cannot compute a 2D PCA with less than 2 points
            return np.identity(3)
        locations = locations.values
        # PCA to fit the 2 horizontal axes (at least for now...), we consider that
        # the third axis is always vertical...
        locations = np.asarray(locations)[:, :2]
        _, axes = _simple_pca(locations)
        result = np.zeros((3, 3))
        result[0, :2] = axes[0]  # Along strike
        result[1, :2] = axes[1]  # Along dip
        result[2, 2] = 1  # Vertical
        return result[0], result[1], result[2]


class Ellipsoid:
    """Stores data to describe a 3D ellispoid.

    # FIXME Store ellipsoid axes!
    Warning: this class only defines an ellipsoid center and 3 radii along "some"
    major axes that are not stored by this class...

    Attributes
    ----------
    center: tuple of size 3
        The coordinates of the ellipsoid's center
    radius: tuple of size 3
        The radii of the ellispoid in the princicpal axes of the fault
    """

    def __init__(self, center, radius):
        assert len(center) == 3
        assert len(radius) == 3
        self.center = center
        self.radius = radius


class Interpolator:
    """Interpolation parameters.

    Attributes
    ----------
    method : str
        The name of the interpolation method to use.
        It must be declared in InterpolationMethod.
    dataset : list
        The items to interpolate.
    discontinuities : list, optional
        Names of the discontinuities in the interpolation area.
    variograms : list of Variogram, optional
        Variograms parameters.
    drift_order: int, optional
        The maximum order of the drift polynomial to include in the kriging system.
    neighborhood: Neighborhood, optional
        Parameters for the neighborhood search parameters
    """

    def __init__(
        self,
        method,
        dataset=None,
        discontinuities=None,
        variograms=None,
        drift_order=None,
        neighborhood=None,
    ):
        self.method = method
        self.dataset = dataset
        self.discontinuities = discontinuities
        self.variograms = variograms
        self.drift_order = drift_order
        self.neighborhood = neighborhood

    def has_volume_data(self):
        return any(not item.is_surface for item in self.dataset)

    def references_are_resolved(self):
        return not (
            self.dataset and any(not isinstance(item, Item) for item in self.dataset)
        )

    def set_discontinuities(self, names):
        self.discontinuities = names

    def remove_discontinuities(self):
        self.discontinuities = None

    def add_discontinuity(self, name):
        if self.discontinuities is None:
            self.discontinuities = [name]
        elif name not in self.discontinuities:
            self.discontinuities.append(name)

    def remove_discontinuity(self, name):
        if name in self.discontinuities:
            self.discontinuities.remove(name)


class Variogram:
    """Variogram parameters

    Attributes
    ----------
    model : str
        Variogram model
    range : ?
        Variogram range. Can be a Float value, a list of [Ox, Oy, Oz] values, or a (3, 3) array with one line per axis.
    sill : ?
        Variogram sill. Can be a Float value or a list of [Ox, Oy, Oz] values.
    nugget : float
        Variogram nugget.
    """

    def __init__(self, model, range=None, sill=None, nugget=None):
        self.model = model
        if isinstance(range, Number):
            range = float(range)
        elif range is not None:
            range = np.asarray(range, dtype=float)
        self.range = range
        if isinstance(sill, Number):
            sill = float(sill)
        elif sill is not None:
            sill = np.asarray(sill, dtype=float)
        self.sill = sill
        if isinstance(nugget, Number):
            nugget = float(nugget)
        self.nugget = nugget


class Neighborhood:
    """Stores neighborhood search parameters for interpolation

    Mainly useful for moving neighborhood (unique neighborhood has no parameters)

    Atributes
    ---------
    max_search_distance: float
        Samples located further than this distance will not be considered during
        interpolation
    nb_max_neighbors: int
        Maximum number of samples to use during interpolation
    nb_min_neighbors: int
        Minimum number of samples to use during interpolation
    nb_angular_sectors: int
        If set, the search space is subdivided in different sectors. This can help
        dealing with clustered data.
    nb_max_neighbors_per_sector: int
        Maximum number of samples to use per angular sector, if any
    """

    DEFAULT_UNIQUE: typing.ClassVar = {
        "max_search_distance": None,
        "nb_max_neighbors": None,
        "nb_min_neighbors": None,
        "nb_angular_sectors": None,
        "nb_max_neighbors_per_sector": None,
    }
    DEFAULT_MOVING: typing.ClassVar = {
        "max_search_distance": nan,
        "nb_max_neighbors": 24,
        "nb_min_neighbors": 1,
        "nb_angular_sectors": 8,
        "nb_max_neighbors_per_sector": 3,
    }

    def __init__(
        self,
        *,
        is_unique: bool,
        max_search_distance: float | None = None,
        nb_max_neighbors: int | None = None,
        nb_min_neighbors: int | None = None,
        nb_angular_sectors: int | None = None,
        nb_max_neighbors_per_sector: int | None = None,
    ):
        kwargs = {**locals()}
        default = self.DEFAULT_UNIQUE if is_unique else self.DEFAULT_MOVING
        # Filter out None arguments (default values will be used instead)
        kwargs = {
            k: (v if (v := kwargs[k]) is not None else v_default)
            for k, v_default in default.items()
        }

        self.is_unique = is_unique
        self.max_search_distance = kwargs["max_search_distance"]
        self.nb_max_neighbors = kwargs["nb_max_neighbors"]
        self.nb_min_neighbors = kwargs["nb_min_neighbors"]
        self.nb_angular_sectors = kwargs["nb_angular_sectors"]
        self.nb_max_neighbors_per_sector = kwargs["nb_max_neighbors_per_sector"]

    @classmethod
    def create_unique(cls):
        return cls(is_unique=True)

    @classmethod
    def create_moving(
        cls,
        *,
        max_search_distance: float | None = None,
        nb_max_neighbors: int | None = None,
        nb_min_neighbors: int | None = None,
        nb_angular_sectors: int | None = None,
        nb_max_neighbors_per_sector: int | None = None,
    ):
        kwargs = {k: v for k, v in locals().items() if v is not cls}
        return cls(is_unique=False, **kwargs)

    def is_valid(self, with_details=False):
        errors = []
        if not self.is_unique:
            if not ((d := self.max_search_distance) > 0 or isnan(d)):
                errors.append(f"Neighborhood: Invalid maximum search distance: {d = }")
            if (nmax := self.nb_max_neighbors) < 1:
                errors.append(
                    f"Neighborhood: Invalid maximum number of neighbors: {nmax = }"
                )
            if (nmin := self.nb_min_neighbors) < 1:
                errors.append(
                    f"Neighborhood: Invalid minimum number of neighbors: {nmin = }"
                )
            if (nb_sectors := self.nb_angular_sectors) < 1:
                errors.append(
                    f"Neighborhood: Invalid number of angular sectors: {nb_sectors = }"
                )
            if (nmax := self.nb_max_neighbors_per_sector) < 1:
                errors.append(
                    f"Neighborhood: Invalid maximum number of neighbors per angular sector: {nmax = }"
                )
        if not with_details:
            return len(errors) == 0
        return errors


# TODO Unsure this class is very useful and where to put it, currently used in qgspile
class RasterDescription:
    def __init__(self, origin, shape, steps, values, name="Topography"):
        assert len(origin) == 2
        assert len(shape) == 2
        assert len(steps) == 2
        assert all(n >= 1 for n in shape)
        assert all(dx > 0 for dx in steps)
        values = np.asarray(values).reshape(-1)
        assert len(values) == shape[0] * shape[1]
        self.name = name
        self.origin = origin
        self.shape = shape
        self.steps = steps
        self.values = values

    @classmethod
    def from_bbox(cls, shape, xmin, xmax, values, name="Topography"):
        # Alternative constructor
        shape = np.asarray(shape, dtype=int)
        assert shape.shape == (2,)
        assert np.all(shape > 0)
        xmin = np.asarray(xmin, dtype=float)
        xmax = np.asarray(xmax, dtype=float)
        assert xmin.shape == (2,)
        assert xmax.shape == (2,)
        assert np.all(xmax > xmin)
        # Use shape[::-1], because array is ordered (ny, nx), but coords are (dx,dy)
        steps = (xmax - xmin) / shape[::-1]
        return cls(xmin, shape, steps, values, name)


def _simple_pca(points):
    """Principal Component Analysis, used to fit an ellipsoid with principal axes
    aligned on fault observations

    Atributes
    ---------
    points: np.array_like
        Dimension (m, n).

    Returns
    -------
    eigenvalues: np.ndarray
        Shape (n,), ordered from major to minor.
    eigenvectors: np.ndarray
        Shape (m, m), ordered as eigenvalues.
    """
    # Note: we reimplement it to avoid depending on scipy "just for a PCA"
    points = np.asarray(points)
    assert points.ndim == 2, "Input point set has invalid shape"
    assert points.shape[0] >= points.shape[1], (
        "Cannot compute PCA if less points than space dimensions"
    )
    # Compute covariance matrix of the point set around its barycenter
    barycenter = np.mean(points, axis=0)
    cov_matrix = np.cov(points - barycenter, rowvar=False)
    # Compute covariance matrix eigen-values/vectors to get principal axes
    eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
    for i in range(len(eigenvectors) - 1):
        assert np.allclose(
            np.dot(eigenvectors[i], eigenvectors[i + 1]), 0.0, rtol=0, atol=1e-15
        )
    # Sort eigens from major to minor
    ranking = np.argsort(eigenvalues)[::-1]
    return eigenvalues[ranking], eigenvectors[:, ranking]
