"""
Simple function to help with geometrical transformations in svg files
"""


class Transfo:
    """Store coordinates transformation from global referential to local one"""

    @staticmethod
    def identity():
        return Transfo([1, 0, 0, 1, 0, 0])

    def __init__(self, transfo):
        self._transfo = [transfo]  # list of transfo from global to local (i.e. doc, layer, group, ...)

    def compose(self, transfo):
        """Compose transformation with more local one

        Args:
            transfo (tuple): local trasnformation

        Returns:
            None
        """
        self._transfo.append(transfo)

    def to_local(self, x, y):
        """Convert global coordinates to local ones

        Args:
            x (float): global x coordinate
            y (float): global y coordinate

        Returns:
            (float, float): local lx, ly
        """
        raise NotImplementedError
        # lx = x - self._transfo[4]
        # ly = y - self._transfo[5]
        #
        # return lx, ly

    def to_global(self, lx, ly):
        """Convert local coordinates to global ones

        Args:
            lx (float): local x coordinate
            ly (float): local y coordinate

        Returns:
            (float, float): global x, y
        """
        x, y = lx, ly
        for t in self._transfo:
            x = lx * t[0] + ly * t[2] + t[4]
            y = lx * t[1] + ly * t[3] + t[5]

        return x, y
