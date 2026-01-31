from xml.etree.ElementTree import Element


class WrongSerializationTarget(Exception):
    pass


class Serializer:
    def __init_subclass__(cls, /, target, tag, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.target = target
        cls.tag = tag

    @classmethod
    def dump(cls, x, **kwargs):
        if not isinstance(x, cls.target):
            raise WrongSerializationTarget
        e = Element(cls.tag)
        cls.dump_element(x, e, **kwargs)
        return e

    @classmethod
    def load(cls, e):
        if e.tag != cls.tag:
            raise WrongSerializationTarget
        return cls.load_element(e)
