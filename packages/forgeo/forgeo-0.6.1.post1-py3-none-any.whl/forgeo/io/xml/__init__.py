import sys
import xml.etree.ElementTree as ET
from functools import cmp_to_key
from importlib.metadata import entry_points
from pathlib import Path

from forgeo.io.xml import builtins, custom
from forgeo.io.xml.base import Serializer as Serializer
from forgeo.io.xml.base import WrongSerializationTarget

# If you want to add custom serializer from package foo to the list of forgeo serializers
# use the entrypoint "forgeo.io.xml.serializer"
# Just add the following line to foo's pyproject.toml where custom quand be any meaningful name
# [project.entry-points."forgeo.io.xml.serializer"]
# customm_serializer = "foo.subpackage:CustomSerializer"
# another_serializer = "foo.subpackage:AnotherSerializer"


def _collect_serializers():
    # shipped serializers
    serializers = list(builtins.serializers) + list(custom.serializers)
    assert sys.version_info >= (3, 9)
    group = entry_points(group="forgeo.io.xml.serializer")
    serializers.extend(eps.load() for eps in group)

    # sort serializers according to their target
    # we want to consider derived class first
    def cmp(s1, s2):
        t1 = s1.target
        t2 = s2.target
        if issubclass(t1, t2):
            if t1 == t2:
                return 0
            return -1
        return 1

    serializers.sort(key=cmp_to_key(cmp))
    return serializers


# serializers are collected upon import
_serializers_collection = None


def check_serializers():
    global _serializers_collection  # noqa: PLW0603
    if _serializers_collection is None:
        _serializers_collection = _collect_serializers()
    return _serializers_collection


def dump(x, path=None, **kwargs):
    check_serializers()
    node = None
    for serializer in _serializers_collection:
        try:
            node = serializer.dump(x, **kwargs)
            break
        except WrongSerializationTarget:
            pass
    else:
        msg = f"No serializer found to dump: {type(x)}"
        raise RuntimeError(msg)
    if path is not None:
        ET.ElementTree(node).write(Path(path).as_posix())
    return node


def load(e):
    check_serializers()
    if isinstance(e, Path):
        e = ET.parse(e.as_posix()).getroot()
    elif isinstance(e, (bytes, str)):
        e = ET.fromstring(e)
    for serializer in _serializers_collection:
        try:
            return serializer.load(e)
        except WrongSerializationTarget:
            pass
    msg = f"No serializer found to load: {e.tag}"
    raise RuntimeError(msg)


def deep_copy(element):
    from ...core import Interpolator  # noqa: PLC0415

    cls = type(element)
    for serializer in check_serializers():
        if serializer.target == cls:
            copy = serializer.load(serializer.dump(element))
            if cls == Interpolator:
                copy.dataset = [
                    get_complete_item(element, item) for item in copy.dataset
                ]
            return copy
    msg = f"Unknown serializer for class {cls}"
    raise TypeError(msg)


def get_complete_item(interp, incomplete_item):
    # Inspired from pile.Model serializer, as InterpolatorSerializer only
    # saves a couple (item_name, item_type) instead of a whole item
    for item in interp.dataset:
        if item.name == incomplete_item.name:
            new_item = deep_copy(item)
            new_item.type = incomplete_item.type
            return new_item
    msg = f"Unknown item name: {incomplete_item.name}"
    raise ValueError(msg)
