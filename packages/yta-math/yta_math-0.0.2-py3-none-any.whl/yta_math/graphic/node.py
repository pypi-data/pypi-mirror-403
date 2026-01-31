from dataclasses import dataclass


@dataclass
class GraphicNode:
    """
    *Dataclass*

    Dataclass that represent a Node in a Graphic, which
    has to be inside the limits (this is checked by
    the Graphic when added to it).
    """
    
    @property
    def x(
        self
    ) -> float:
        """
        The `x` position of the node.
        """
        return self.position[0]

    @property
    def y(
        self
    ) -> float:
        """
        The `y` position of the node.
        """
        return self.position[1]

    def __init__(
        self,
        x: float,
        y: float
    ):
        self.position: tuple[float, float] = (x, y)
        """
        The position of the node represented by a
        `(x, y)` tuple.
        """