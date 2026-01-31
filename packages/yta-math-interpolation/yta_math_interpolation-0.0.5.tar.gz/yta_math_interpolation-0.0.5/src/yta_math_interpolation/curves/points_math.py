import math


# TODO: Maybe this could be moved to 'yta_math_graphic'
Point = tuple[float, float]

# TODO: Maybe this could be moved to 'yta_math_graphic'
class PointsMath:
    """
    *Static class*

    Class to wrap the functionality related to points
    math operations.
    """

    @staticmethod
    def add(
        point_a: Point,
        point_b: Point
    ) -> Point:
        """
        Sum the `point_a` and `point_b` points.
        """
        return (point_a[0] + point_b[0], point_a[1] + point_b[1])

    @staticmethod
    def substract(
        point_a: Point,
        point_b: Point
    ) -> Point:
        """
        Substract the `point_b` provided from the also given
        `point_a`.
        """
        return (point_a[0] - point_b[0], point_a[1] - point_b[1])

    @staticmethod
    def multiply(
        point: Point,
        factor: float
    ) -> Point:
        """
        Multiply the `point` provided by the also given
        `factor`.
        """
        return (point[0] * factor, point[1] * factor)
    
    @staticmethod
    def length(
        point: Point
    ) -> float:
        """
        Calculate the length of the `point` provided.

        The formula:
        - `math.sqrt(point[0] ** 2 + point[1] ** 2)`
        """
        return math.sqrt(point[0] ** 2 + point[1] ** 2)
    
    @staticmethod
    def distance(
        point_a: Point,
        point_b: Point
    ) -> float:
        """
        Calculate the euclidean distance in between the
        `point_a` and `point_b` provided.
        """
        return math.dist(point_a, point_b)

    @staticmethod
    def normalize(
        point: Point
    ) -> Point:
        """
        Normalize the `point` provided by dividing by its
        length.
        """
        length = PointsMath.length(point)

        return (
            (0.0, 0.0)
            if length == 0 else
            (point[0] / length, point[1] / length)
        )

    @staticmethod
    def perpendicular(
        point: Point
    ) -> Point:
        """
        Get the perpendicular point of the given as `point`
        parameter.

        The formula:
        - `(-point[1], point[0])`
        """
        return (-point[1], point[0])