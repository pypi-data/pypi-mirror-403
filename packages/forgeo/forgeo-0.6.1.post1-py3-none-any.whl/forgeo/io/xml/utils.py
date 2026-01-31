from io import BytesIO
from xml.etree.ElementTree import Element

import numpy as np

from forgeo.io import xml


def add_child_text_node(node, tag, text):
    child = Element(tag)
    child.text = text
    node.append(child)


def dump_array_node(a, e, format="numpy", **kwargs):  # noqa: ARG001
    assert format in ("numpy", "ascii")
    e.attrib["format"] = format
    if format == "numpy":
        output = BytesIO()
        np.save(output, a)
        e.text = output.getbuffer().tobytes().hex()
    elif format == "ascii":
        e.attrib["shape"] = ",".join(str(n) for n in a.shape)
        if np.issubdtype(a.dtype, np.integer):
            e.text = " ".join(f"{i:d}" for i in np.ravel(a, order="C"))
        else:
            # 18 digits cf. https://stackoverflow.com/a/51392044
            e.text = " ".join(f"{x:.18e}" for x in np.ravel(a, order="C"))


def load_array_node(e):
    format = e.attrib["format"]
    assert format in ("numpy", "ascii")
    if format == "numpy":
        return np.load(BytesIO(bytes.fromhex(e.text.strip())))
    if format == "ascii":
        a = np.fromstring(e.text.strip(), sep=" ")
        shape = e.attrib["shape"].strip()
        if len(shape) != 0:
            a.shape = tuple(int(s) for s in shape.split(","))
        return a
    return None


class TableSerializer:
    def __init_subclass__(cls, /, table="values", **kwargs):
        super().__init_subclass__(**kwargs)
        cls.table = table

    @classmethod
    def dump_element(cls, x, e, **kwargs):
        a = getattr(x, cls.table)
        if a is not None:
            dump_array_node(a, e, **kwargs)
        return e

    @classmethod
    def load_element(cls, e):
        if e.text is None:
            return cls.target()
        return cls.target(load_array_node(e))


class CompoundSerializer:
    def __init_subclass__(cls, /, flags=None, vars=None, **kwargs):
        super().__init_subclass__(**kwargs)

        def _process(x):
            if isinstance(x, str):
                return (x,)
            return x or ()

        cls.flags = _process(flags)
        cls.vars = _process(vars)

    @classmethod
    def dump_element(cls, x, e, **kwargs):
        for name in cls.flags:
            assert isinstance(getattr(x, name), bool)
            e.attrib[name] = "true" if getattr(x, name) else "false"
        for name in cls.vars:
            e.append(xml.dump(getattr(x, name), **kwargs))

    @classmethod
    def load_element(cls, e):
        """
        WARNING: this assumes the children of e come in the right order
                 (the same as the one used for dump_element)
        """
        params = {}
        for name in cls.flags:
            assert e.attrib[name] in ("false", "true")
            params[name] = e.attrib[name] == "true"
        children = list(e)
        nv, nc = len(cls.vars), len(children)
        assert nv >= nc
        for name, child in zip(cls.vars[:nc], children, strict=False):
            params[name] = xml.load(child)
        return cls.target(**params)
