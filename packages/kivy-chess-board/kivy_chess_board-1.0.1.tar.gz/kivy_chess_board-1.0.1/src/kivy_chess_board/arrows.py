import math

from kivy.graphics import Canvas, Color, Line, Triangle

from .type import RGB, LineSegment, Point

ARROW_GROUP = "arrows_group"


def draw_arrow(
    canvas: Canvas,
    line: LineSegment,
    square_size: float,
    rgb: RGB,
    highlight: bool = False,
) -> None:
    """Draw an arrow on the given canvas.

    Parameters
    ----------
    canvas :
        The Kivy canvas to draw on.
    line :
        The line segment representing the arrow from start to end.
    square_size :
        The size of the square grid cell, used to scale the arrow.
    rgb :
        The RGB color of the arrow.
    highlight :
        Whether to draw the arrow with a highlight (black outline).
    """
    dx = line.end[0] - line.start[0]
    dy = line.end[1] - line.start[1]
    angle = math.atan2(dy, dx)

    arrowhead_len = square_size * 0.8
    line_width = square_size * 0.1

    # total distance from pos1 to pos2
    arrow_len = math.hypot(dx, dy)

    # how far the line portion should go before the arrowhead
    line_len = max(arrow_len - (arrowhead_len * 0.5), 0)

    # The line will end here, so the triangle tip is at pos2.
    # If you want the *tip* to be at pos2, the line must stop earlier:
    base = _point_at_distance(line.start, angle, line_len)

    # The arrowhead triangle: tip is at pos2; the "base" is around `base`.
    left_angle = angle + math.radians(150)
    right_angle = angle - math.radians(150)
    left = _point_at_distance(line.end, left_angle, arrowhead_len)
    right = _point_at_distance(line.end, right_angle, arrowhead_len)

    line_points = *line.start, *base
    arrow_head_points = *line.end, *left, *right

    with canvas:
        if highlight:
            # Draw a black line in the background to make the arrow stand out
            Color(0, 0, 0, 1, group=ARROW_GROUP)  # Black
            Line(points=line_points, width=line_width * 1.2, group=ARROW_GROUP)

            # Black arrowhead
            Line(
                points=arrow_head_points,
                close=True,
                width=line_width * 0.2,
                group=ARROW_GROUP,
            )

        Color(*rgb, 1, group=ARROW_GROUP)
        # Draw line from pos1 to the start of the arrowhead.
        Line(points=line_points, width=line_width, group=ARROW_GROUP)

        # Draw the arrowhead
        Triangle(points=arrow_head_points, group=ARROW_GROUP)


def _point_at_distance(p: Point, angle: float, distance: float) -> Point:
    """Return the point at a given distance.

    Calculates the distance from the point `p` in the direction
    `angle` (in radians) and returns the new point as (x, y).
    """
    x = p[0] + distance * math.cos(angle)
    y = p[1] + distance * math.sin(angle)
    return x, y
