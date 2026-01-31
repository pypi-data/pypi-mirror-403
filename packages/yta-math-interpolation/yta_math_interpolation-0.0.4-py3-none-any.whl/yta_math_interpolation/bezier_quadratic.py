from yta_math_interpolation.abstract import InterpolationFunction
from yta_math_interpolation.enums import InterpolationFunctionName
from yta_math_interpolation.curves.points_math import PointsMath, Point
from yta_math_interpolation.curves.parameters import BezierQuadraticCurvatureParameters
from yta_math_interpolation.curves.enums import BezierQuadraticCurvatureMode
from yta_math_interpolation.curves import BezierQuadratic
from yta_programming.decorators.requires_dependency import requires_dependency


class BezierQuadraticInterpolation(InterpolationFunction):
    """
    A quadratic bezier interpolation function, that
    needs one control point. The curve will not pass
    through the `point_control` unless it is lineal.

    The formula:
    ```
    u = 1 - t
    return PointsMath.add(
        PointsMath.add(
            PointsMath.multiply(point_start, u * u),
            PointsMath.multiply(point_control, 2 * u * t)
        ),
        PointsMath.multiply(point_end, t * t)
    )
    ```
    Try a bezier curve online here:
    - https://ytyt.github.io/siiiimple-bezier/
    """
    _name: str = InterpolationFunctionName.BEZIER_QUADRATIC.value

    # Special method
    def interpolate_autocalculated(
        self,
        t: float,
        point_start: Point,
        point_end: Point,
        curvature_mode: BezierQuadraticCurvatureMode,
        curvature_parameters: BezierQuadraticCurvatureParameters
    ):
        point_control = BezierQuadratic.get_control_point(
            point_start = point_start,
            point_end = point_end,
            mode = curvature_mode,
            parameters = curvature_parameters
        )

        return self.interpolate(
            t = t,
            point_start = point_start,
            point_control = point_control,
            point_end = point_end
        )

    def interpolate(
        self,
        t: float,
        point_start: Point,
        point_control: Point,
        point_end: Point
    ):
        """
        Interpolate a point on a quadratic Bézier curve for
        a given normalized parameter `t` (in the `[0.0, 1.0]`
        range), using all the points provided.

        Return the position obtained by evaluating the curve
        at `t`.
        """
        return super().interpolate(
            t = t,
            point_start = point_start,
            point_control = point_control,
            point_end = point_end
        )

    def _interpolate(
        self,
        t: float,
        point_start: Point,
        point_control: Point,
        point_end: Point
    ) -> tuple[Point, Point]:
        u = 1.0 - t
    
        return PointsMath.add(
            PointsMath.add(
                PointsMath.multiply(point_start, u * u),
                PointsMath.multiply(point_control, 2 * u * t)
            ),
            PointsMath.multiply(point_end, t * t)
        )
    
    @requires_dependency('numpy', 'yta_math_interpolation', 'numpy')
    def plot(
        self,
        # TODO: Should this be set in the '__init__' (?)
        point_start: Point,
        point_end: Point,
        number_of_samples: int = 100
    ):
        import numpy as np

        point_control = BezierQuadratic.get_control_point(
            point_start = point_start,
            point_end = point_end
        )
        
        key_points = [point_start, point_control, point_end]

        # We will draw 'n' points between 0.0 and 1.0
        curve_points = [
            self.interpolate(
                t = t,
                point_start = point_start,
                point_control = point_control,
                point_end = point_end
            )
            for t in np.linspace(0.0, 1.0, number_of_samples).tolist()
        ]

        return self._plot(
            key_points = key_points,
            curve_points = curve_points
        )
    
