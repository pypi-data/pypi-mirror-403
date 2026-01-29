from typing import NamedTuple

Point = tuple[float, float]


class ColRow(NamedTuple):
    col: int
    row: int

    def invert(self) -> "ColRow":
        """Return a new ColRow with inverted row (for flipping the board)."""
        return ColRow(col=self.col, row=7 - self.row)


class LineSegment(NamedTuple):
    start: Point
    end: Point


class RGB(NamedTuple):
    r: float
    g: float
    b: float

    def gradient(self, ratio: float) -> "RGB":
        """Generate a color that is a gradient towards white by the given ratio."""
        return RGB(
            self.r + (1 - self.r) * ratio,
            self.g + (1 - self.g) * ratio,
            self.b + (1 - self.b) * ratio,
        )
