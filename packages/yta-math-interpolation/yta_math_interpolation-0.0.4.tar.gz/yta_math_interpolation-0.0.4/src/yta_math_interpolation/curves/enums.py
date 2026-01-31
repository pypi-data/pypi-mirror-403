from yta_constants.enum import YTAEnum as Enum


class BezierCubicCurvatureMode(Enum):
    """
    The mode of the curvature we want to apply in
    a cubic bezier interpolation
    """

    LINEAR = 'linear'
    ARC_LEFT = 'arc_left'
    ARC_RIGHT = 'arc_right'
    S_CURVE = 's_curve'

class BezierQuadraticCurvatureMode(Enum):
    """
    The mode of the curvature we want to apply in
    a quadratic bezier interpolation
    """

    LINEAR = 'linear'
    ARC_LEFT = 'arc_left'
    ARC_RIGHT = 'arc_right'
