"""
Module to include the functionality related
to interpolation.
"""
from yta_math_interpolation.enums import InterpolationFunctionName
from yta_math_interpolation.curves.points_math import Point
from yta_programming.decorators.requires_dependency import requires_dependency
from abc import ABC, abstractmethod


class InterpolationFunction(ABC):
    """
    *Abstract class*

    Abstract class to be inherited by the specific
    interpolation implementations.

    An interpolation function that is able to
    calculate additional points associated to
    the points already provided.
    """
    _registry: dict[str, type['InterpolationFunction']] = {}
    """
    *For internal use only*
    
    A register to simplify the way we instantiate
    new classes from strings.
    """
    _name: str
    """
    *For internal use only*

    The string name of the specific interpolation
    implementation class.
    """
    # may_overshoot: bool
    # """
    # Boolean flag to indicate if the easing function can
    # generate values out of the bounds or not.
    # """

    def __init_subclass__(
        cls,
        **kwargs
    ):
        """
        Init the subclass and register it.
        """
        super().__init_subclass__(**kwargs)

        if hasattr(cls, '_name'):
            InterpolationFunction._registry[cls.get_name()] = cls

    @classmethod
    def get(
        cls,
        name: InterpolationFunctionName
    ) -> type['InterpolationFunction']:
        """
        Get the specific class associated to the given
        interpolation function `name`.
        """
        name = InterpolationFunctionName.to_enum(name)

        return cls._registry[name.value]

    @classmethod
    def get_name(
        cls
    ) -> str:
        """
        Get the string name of the specific interpolation
        implementation class.
        """
        return cls._name
    
    # This method below is to be able to interpolate
    # by providing only the start and end points
    @abstractmethod
    def interpolate_autocalculated(
        self,
        t: float,
        point_start: Point,
        point_end: Point
    ):
        """
        This method can be called when we want to let the
        system do its magic and calculate the control points
        automatically if needed.

        Return the position obtained by evaluating the line
        at `t`.

        This method will autocalculate the control points, if
        necessary, and call the `self.interpolate(...)` method.
        """
        pass

    @abstractmethod
    def _interpolate(
        self,
        t: float,
        point_start: Point,
        point_end: Point,
        **kwargs
    ) -> Point:
        """
        *For internal use only*

        The proper calculation of the interpolation, that
        must be implemented for each specific class.

        The interpolation calculation will provide the
        new point (or points) for the ones given as input,
        using the `t` provided (that must be a value in the
        `[0.0, 1.0]` range indicating the progress in
        between the `point_start` and `point_end`).

        Return the position obtained by evaluating the curve
        at `t`.
        """
        pass

    def interpolate(
        self,
        t: float,
        point_start: Point,
        point_end: Point,
        **kwargs
    ) -> Point:
        """
        Apply the interpolation with the points provided as
        input.

        The interpolation calculation will provide the
        new point (or points) for the ones given as input,
        using the `t` provided (that must be a value in the
        `[0.0, 1.0]` range indicating the progress in
        between the `point_start` and `point_end`).

        Return the position obtained by evaluating the curve
        at `t`.
        """
        # TODO: Validate points

        # TODO: I think I only need 1 interpolate method
        return self._interpolate(
            t = t,
            point_start = point_start,
            point_end = point_end,
            **kwargs
        )

    def __call__(
        self,
        t: float,
        point_start: Point,
        point_end: Point,
        **kwargs
    ) -> Point:
        """
        Special method to allow us doing
        `interpolation_function(point_start, point_end)`
        instead of
        `interpolation_function.interpolate(point_start, point_end)`.

        Apply the interpolation with the points provided as
        input.

        The interpolation calculation will provide the
        new point (or points) for the ones given as input,
        using the `t` provided (that must be a value in
        the `[0.0, 1.0]` range indicating the progress in
        between the `point_start` and `point_end`).

        Return the position obtained by evaluating the curve
        at `t`.
        """
        return self.interpolate(
            t = t,
            point_start = point_start,
            point_end = point_end,
            **kwargs
        )
    
    @requires_dependency('matplotlib', 'yta_math_interpolation', 'matplotlib')
    @requires_dependency('numpy', 'yta_math_interpolation', 'numpy')
    def _plot(
        self,
        key_points: list[Point],
        curve_points: list[Point]
    ):
        """
        *For internal use only*

        *Optional `matplotlib` library required*

        *Optional `numpy` library required*

        The internal method to plot the key and curve
        points.
        """
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Limit and draw axis
        # plt.xlim(0, 1)
        # plt.ylim(0, 1)
        plt.axhline(0, color = 'black', linewidth = 1)
        plt.axvline(0, color = 'black', linewidth = 1)
        plt.grid(True)

        # Draw the points that are the curve
        x_vals = [
            curve_point[0]
            for curve_point in curve_points
        ]
        y_vals = [
            curve_point[1]
            for curve_point in curve_points
        ]
        plt.scatter(x_vals, y_vals, color = 'white', edgecolors = 'black', s = 10)

        # Draw the key points (start, end and control points)
        kx, ky = zip(*key_points)
        plt.scatter(
            kx,
            ky,
            s = 100,
            color = 'red',
            zorder = 3
        )

        plt.title('')
        plt.xlabel('X axis')
        plt.ylabel('Y axis')
        
        plt.show()

    @abstractmethod
    @requires_dependency('numpy', 'yta_math_interpolation', 'numpy')
    def plot(
        self,
        # TODO: Should this be set in the '__init__' (?)
        point_start: Point,
        point_end: Point,
        number_of_samples: int = 100
    ):
        """
        Plot a graphic representing `number_of_samples`
        values from the `point_start` to the `point_end`.
        """
        import numpy as np
        
        # TODO: Define the p0,p1,p2
        from yta_math_interpolation.curves import BezierQuadratic
        from yta_math_interpolation.curves.enums import BezierQuadraticCurvatureMode
        from yta_math_interpolation.curves.parameters import BezierQuadraticCurvatureParameters

        # TODO: By now I'm forcing BezierQuadratic
        point_control = BezierQuadratic.get_control_point(
            point_start = point_start,
            point_end = point_end
        )

        key_points = [point_start, point_control, point_end]

        # We will draw 'n' points between 0.0 and 1.1
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
