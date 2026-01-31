from yta_math_interpolation.abstract import InterpolationFunction
from yta_math_interpolation.enums import InterpolationFunctionName
from yta_math_interpolation.curves.points_math import Point, PointsMath
from yta_programming.decorators.requires_dependency import requires_dependency


class LinearInterpolation(InterpolationFunction):
    """
    A linear interpolation function, also called LERP.

    The formula:
    ```
    return PointsMath.add(
        point_start,
        PointsMath.multiply(
            PointsMath.substract(point_end, point_start),
            t
        )
    )
    ```
    """
    _name: str = InterpolationFunctionName.LINEAR.value

    # Special method
    def interpolate_autocalculated(
        self,
        t: float,
        point_start: Point,
        point_end: Point
    ):
        return self.interpolate(
            t = t,
            point_start = point_start,
            point_end = point_end
        )

    def interpolate(
        self,
        t: float,
        point_start: Point,
        point_end: Point,
    ) -> Point:
        return super().interpolate(
            t = t,
            point_start = point_start,
            point_end = point_end
        )

    def _interpolate(
        self,
        t: float,
        point_start: Point,
        point_end: Point
    ) -> tuple[Point, Point]:
        return PointsMath.add(
            point_start,
            PointsMath.multiply(
                PointsMath.substract(point_end, point_start),
                t
            )
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
        
        key_points = [point_start, point_end]

        # We will draw 'n' points between 0.0 and 1.0
        curve_points = [
            self.interpolate(
                t = t,
                point_start = point_start,
                point_end = point_end
            )
            for t in np.linspace(0.0, 1.0, number_of_samples).tolist()
        ]

        return self._plot(
            key_points = key_points,
            curve_points = curve_points
        )

    
