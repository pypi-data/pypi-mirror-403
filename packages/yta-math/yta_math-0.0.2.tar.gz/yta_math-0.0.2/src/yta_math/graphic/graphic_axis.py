from yta_validation.parameter import ParameterValidator
from dataclasses import dataclass


@dataclass
class GraphicAxis:
    """
    *Dataclass*

    Dataclass that represent a Graphic axis with
    its min and max range.
    """

    @property
    def min(
        self
    ) -> float:
        """
        The minimum value of the axis.
        """
        return self.range[0]
    
    @property
    def max(
        self
    ) -> float:
        """
        The maximum value of the axis.
        """
        return self.range[1]

    def __init__(
        self,
        min: float,
        max: float
    ):
        ParameterValidator.validate_mandatory_number('min', min)
        ParameterValidator.validate_mandatory_number('max', max)
        
        if min >= max:
            raise Exception('The "min" parameter cannot be greater or equal than the "max" parameter.')

        self.range: tuple[float, float] = (min, max)
        """
        The range of the axis, a `(min, max)` tuple.
        """