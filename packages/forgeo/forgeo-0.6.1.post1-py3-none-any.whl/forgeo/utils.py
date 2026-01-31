import numpy as np
from attrs import cmp_using, converters, field, validators


def dim2_array_check(nbcols=None):
    def check(instance, attribute, value):  # noqa: ARG001
        if value is None:
            return
        if value.ndim != 2:
            msg = "expecting a bidimensional array"
            raise ValueError(msg)
        if nbcols is not None:
            nc = value.shape[1]
            try:
                ok = nc in nbcols
            except TypeError:
                ok = nc == nbcols
            if not ok:
                msg = f"wrong number of columns ({nc} instead of {nbcols})"
                raise ValueError(msg)

    return check


def dim1_array_check():
    def check(instance, attribute, value):  # noqa: ARG001
        if value is None:
            return
        if value.ndim != 1:
            msg = "expecting a 1D array"
            raise ValueError(msg)

    return check


def cmp_values(a, b):
    if a is None:
        return b is None
    return b is not None and np.array_equal(a, b)


def table_field(nbcols=None, /):
    return field(
        converter=lambda value: None if value is None else np.asarray(value, dtype="d"),
        default=None,
        validator=dim2_array_check(nbcols),
        eq=cmp_using(eq=cmp_values),
    )


def default_field(cls, **kwargs):
    kwargs.setdefault("converter", converters.default_if_none(factory=cls))
    return field(validator=validators.instance_of(cls), default=cls(), **kwargs)


class Spatial:
    @property
    def ambient_space_dimension(self):
        return 0 if self.values is None else self.values.shape[1]

    def __bool__(self):
        return self.values is not None and self.values.shape[0] > 0

    def __len__(self):
        return 0 if self.values is None else self.values.shape[0]


class BBox:
    def __init__(self, a=None):
        self._min = np.array((np.inf,) * 3, dtype="d")
        self._max = np.array((-np.inf,) * 3, dtype="d")
        if a is not None:
            self.update(a)

    def update(self, a):
        self._min = np.min(np.vstack([self._min, np.min(a, axis=0)]), axis=0)
        self._max = np.max(np.vstack([self._max, np.max(a, axis=0)]), axis=0)

    def union(self, bbox):
        self._min = np.min(np.vstack([self._min, bbox._min]), axis=0)
        self._max = np.max(np.vstack([self._max, bbox._max]), axis=0)

    @classmethod
    def from_array(cls, a):
        bbox = cls()
        bbox.update(a)
        return bbox

    @property
    def empty(self):
        return (
            self.xmin >= self.xmax or self.ymin >= self.ymax or self.zmin >= self.zmax
        )

    @property
    def extent(self):
        return (self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax)

    @property
    def x_length(self):
        return max(0, self.xmax - self.xmin)

    @property
    def y_length(self):
        return max(0, self.ymax - self.ymin)

    @property
    def z_length(self):
        return max(0, self.zmax - self.zmin)

    @property
    def lengths(self):
        return self.x_length, self.y_length, self.z_length

    @property
    def xmin(self):
        return self._min[0]

    @property
    def ymin(self):
        return self._min[1]

    @property
    def zmin(self):
        return self._min[2]

    @property
    def xmax(self):
        return self._max[0]

    @property
    def ymax(self):
        return self._max[1]

    @property
    def zmax(self):
        return self._max[2]

    def __str__(self):
        return (
            f"{self.xmin:+12e} <= x <= {self.xmax:+12e}\n"
            f"{self.ymin:+12e} <= y <= {self.ymax:+12e}\n"
            f"{self.zmin:+12e} <= z <= {self.zmax:+12e}"
        )

    def dilate(self, factor=1.0):
        assert factor >= 0
        L = np.array(self.lengths)
        L *= 0.5
        center = 0.5 * (self._min + self._max)
        self._min = center - factor * L
        self._max = center + factor * L
