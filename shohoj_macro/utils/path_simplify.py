"""
Ramer-Douglas-Peucker (RDP) Path Simplification Algorithm
Compresses thousands of continuous mouse move coordinates into clean,
low-overhead control waypoints while preserving curve shape.
"""

import math


def _perpendicular_distance(point: tuple[float, float], line_start: tuple[float, float], line_end: tuple[float, float]) -> float:
    """Calculates perpendicular distance from point to line segment."""
    x0, y0 = point
    x1, y1 = line_start
    x2, y2 = line_end

    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return math.hypot(x0 - x1, y0 - y1)

    numerator = abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1)
    denominator = math.hypot(dx, dy)
    return numerator / denominator


def rdp_simplify(points: list[tuple[float, float]], epsilon: float = 2.0) -> list[tuple[float, float]]:
    """
    Simplifies a 2D polyline path using Ramer-Douglas-Peucker algorithm.
    :param points: List of (x, y) coordinates.
    :param epsilon: Maximum allowable distance tolerance in pixels.
    :return: Simplified list of (x, y) coordinates.
    """
    if len(points) <= 2:
        return points

    # Find the point with maximum distance from the line connecting start and end
    dmax = 0.0
    index = 0
    start = points[0]
    end = points[-1]

    for i in range(1, len(points) - 1):
        d = _perpendicular_distance(points[i], start, end)
        if d > dmax:
            index = i
            dmax = d

    # If max distance is greater than epsilon, recursively simplify
    if dmax > epsilon:
        rec_results1 = rdp_simplify(points[: index + 1], epsilon)
        rec_results2 = rdp_simplify(points[index:], epsilon)
        return rec_results1[:-1] + rec_results2
    else:
        return [points[0], points[-1]]
