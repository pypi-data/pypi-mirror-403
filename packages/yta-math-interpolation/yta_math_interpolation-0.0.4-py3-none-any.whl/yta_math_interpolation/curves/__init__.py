from yta_math_interpolation.curves.enums import BezierCubicCurvatureMode, BezierQuadraticCurvatureMode
from yta_math_interpolation.curves.parameters import BezierCubicCurvatureParameters, BezierQuadraticCurvatureParameters
from yta_math_interpolation.curves.points_math import Point, PointsMath
from typing import Union


# TODO: Rename to 'BezierCubicCurvature' or something
class BezierCubic:
    """
    Class to wrap curvature calculations related to
    cubic Bézier curves.
    """

    @staticmethod
    def get_control_points(
        point_start: Point,
        point_end: Point,
        mode: Union[BezierCubicCurvatureMode, str] = BezierCubicCurvatureMode.ARC_LEFT,
        parameters: BezierCubicCurvatureParameters = BezierCubicCurvatureParameters(0.3, 0, 0.8)
    ) -> tuple[Point, Point]:
        """
        Get the first and second control points as a tuple
        based on the `point_start`, `point_end`, the `mode`
        and the `parameters` provided.
        """
        mode = BezierCubicCurvatureMode.to_enum(mode)

        return {
            BezierCubicCurvatureMode.LINEAR:     lambda point_start, point_end, parameters: BezierCubic._linear(point_start, point_end, parameters),
            BezierCubicCurvatureMode.ARC_LEFT:   lambda point_start, point_end, parameters: BezierCubic._arc(point_start, point_end, parameters, +1.0),
            BezierCubicCurvatureMode.ARC_RIGHT:  lambda point_start, point_end, parameters: BezierCubic._arc(point_start, point_end, parameters, -1.0),
            BezierCubicCurvatureMode.S_CURVE:    lambda point_start, point_end, parameters: BezierCubic._s_curve(point_start, point_end, parameters),
        }[mode](point_start, point_end, parameters)

    @staticmethod
    def _linear(
        point_start: Point,
        point_end: Point,
        _
    ) -> tuple[Point, Point]:
        """
        *For internal use only*

        The linear curvature mode calculation.
        """
        d = PointsMath.substract(point_end, point_start)

        return (
            PointsMath.add(point_start, PointsMath.multiply(d, 1/3)),
            PointsMath.add(point_start, PointsMath.multiply(d, 2/3))
        )

    @staticmethod
    def _arc(
        point_start: Point,
        point_end: Point,
        parameters: BezierCubicCurvatureParameters,
        direction: float = -1
    ) -> tuple[Point, Point]:
        """
        *For internal use only*

        The arc curvature mode calculation.
        """
        # TODO: 'direction' must be +1.0 (left) or -1.0 (right)
        if float(direction) not in [1.0, -1.0]:
            raise Exception('Invalid "direction" parameter. Must be +1.0 (left) or -1.0 (right).')
        
        d = PointsMath.substract(point_end, point_start)
        dist = PointsMath.length(d)
        n = PointsMath.multiply(PointsMath.normalize(PointsMath.perpendicular(d)), direction)

        h = dist * parameters.intensity * parameters.smoothness
        n = PointsMath.multiply(n, h)

        t1 = 1/3 + parameters.bias * 0.1
        t2 = 2/3 + parameters.bias * 0.1

        return (
            PointsMath.add(PointsMath.add(point_start, PointsMath.multiply(d, t1)), n),
            PointsMath.add(PointsMath.add(point_start, PointsMath.multiply(d, t2)), n)
        )

    @staticmethod
    def _s_curve(
        point_start: Point,
        point_end: Point,
        parameters: BezierCubicCurvatureParameters
    ) -> tuple[Point, Point]:
        """
        *For internal use only*

        The s curve curvature mode calculation.
        """
        d = PointsMath.substract(point_end, point_start)
        dist = PointsMath.length(d)
        n = PointsMath.multiply(PointsMath.normalize(PointsMath.perpendicular(d)), dist * parameters.intensity * parameters.smoothness)

        return (
            PointsMath.add(PointsMath.add(point_start, PointsMath.multiply(d, 1/3)), n),
            PointsMath.substract(PointsMath.add(point_start, PointsMath.multiply(d, 2/3)), n)
        )

# TODO: Rename to 'BezierQuadraticCurvature' or something
class BezierQuadratic:
    """
    Class to wrap curvature calculations related to
    quadratic Bézier curves.
    """

    @staticmethod
    def get_control_point(
        point_start: Point,
        point_end: Point,
        mode: Union[BezierQuadraticCurvatureMode, str] = BezierQuadraticCurvatureMode.ARC_LEFT,
        parameters: BezierQuadraticCurvatureParameters = BezierQuadraticCurvatureParameters(0.3)
    ) -> Point:
        """
        Get the single control point based on the
        `point_start`, `point_end`, the `mode` and the
        `parameters` provided.
        """
        mode = BezierQuadraticCurvatureMode.to_enum(mode)

        return {
            BezierQuadraticCurvatureMode.LINEAR:     lambda point_start, point_end, parameters: BezierQuadratic._linear(point_start, point_end, parameters),
            BezierQuadraticCurvatureMode.ARC_LEFT:   lambda point_start, point_end, parameters: BezierQuadratic._arc(point_start, point_end, parameters, +1.0),
            BezierQuadraticCurvatureMode.ARC_RIGHT:  lambda point_start, point_end, parameters: BezierQuadratic._arc(point_start, point_end, parameters, -1.0),
        }[mode](point_start, point_end, parameters)

    @staticmethod
    def _linear(
        point_start: Point,
        point_end: Point
    ) -> Point:
        """
        *For internal use only*

        The linear curvature mode calculation.
        """
        # We force this value, only 1 point in the middle
        t = 0.5
        
        return PointsMath.add(
            point_start,
            PointsMath.multiply(
                PointsMath.substract(point_end, point_start),
                t
            )
        )
    
    @staticmethod
    def _arc(
        point_start: Point,
        point_end: Point,
        parameters: BezierQuadraticCurvatureParameters,
        direction: float = -1
    ) -> Point:
        """
        *For internal use only*

        The arc curvature mode calculation.
        """
        # TODO: 'direction' must be +1.0 (left) or -1.0 (right)
        if float(direction) not in [1.0, -1.0]:
            raise Exception('Invalid "direction" parameter. Must be +1.0 (left) or -1.0 (right).')
        
        d = PointsMath.substract(point_end, point_start)
        n = PointsMath.normalize(PointsMath.perpendicular(d))
        h = PointsMath.length(d) * parameters.intensity * direction

        point_middle = BezierQuadratic._linear(
            point_start = point_start,
            point_end = point_end
        )

        return PointsMath.add(point_middle, PointsMath.multiply(n, h))