class Erosion:
    """Represents an erosion event.

    Attributes
    ----------
    name : str
        The name of the erosion event.
    info : any, optional
        Additional information about the erosion.
    """

    def __init__(self, name, info=None):
        self.name = name
        self.info = info

    def __repr__(self):
        """Returns a string representation of the Erosion instance."""
        return self.name
