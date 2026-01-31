from dataclasses import dataclass


@dataclass
class BezierCubicCurvatureParameters:
    """
    The parameters of the curvature we are defining for
    a cubic bezier interpolation.
    """

    def __init__(
        self,
        intensity: float = 0.3, # 0..1
        bias: float = 0.0,      # -1..1 (bring the curve forward or backward)
        smoothness: float = 1.0 # How soft it is
    ):
        # TODO: Validate (?)

        self.intensity: float = intensity
        """
        The intensity of the curve.
        """
        self.bias: float = bias
        """
        The inclination of the curve.
        """
        self.smoothness: float = smoothness
        """
        The smoothness of the curve.
        """

@dataclass
class BezierQuadraticCurvatureParameters:
    """
    The parameters of the curvature we are defining for
    a quadratic bezier interpolation.
    """

    def __init__(
        self,
        intensity: float = 0.3, # 0..1
    ):
        # TODO: Validate (?)

        self.intensity: float = intensity
        """
        The intensity of the curve.
        """
