from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self, TYPE_CHECKING

from .models import Coordinate

if TYPE_CHECKING:
    from .models import RotatedPolycube, SNAPSHOT

__all__ = ("AbstractHull", "CoordinateHull", "CuboidHull")


class AbstractHull(ABC):
    def __init__(self) -> None:
        self.frontier: set[Coordinate] = set()

    def update_frontier(self, polycube: RotatedPolycube, offset: Coordinate) -> None:
        """Remove the coordinates of the polycube at the offset from the frontier, if present."""
        self.frontier.difference_update(c + offset for c in polycube.coords)

    @classmethod
    @abstractmethod
    def from_snapshot(cls, snapshot: SNAPSHOT) -> Self:
        """Constructs a hull from a snapshot."""
        pass

    @abstractmethod
    def to_snapshot(self) -> SNAPSHOT:
        """Exports the hull into a snapshot."""
        pass

    @abstractmethod
    def in_hull(self, pos: Coordinate) -> bool:
        """Checks if the given coordinate is inside the hull."""
        pass

    @abstractmethod
    def inside_hull(self, pos: Coordinate) -> bool:
        """Checks if the given coordinate is inside the hull or in its inner part."""
        pass

    @abstractmethod
    def in_inner_part(self, pos: Coordinate) -> bool:
        """Checks if the given coordinate is inside the inner part of the hull."""
        pass


class CoordinateHull(AbstractHull):
    def __init__(self, coords: frozenset[Coordinate], frontier: set[Coordinate] | None = None) -> None:
        super().__init__()
        self.coords = coords

        if frontier is None:
            self.frontier = set(coords)
        else:
            self.frontier = frontier

    @classmethod
    def from_snapshot(cls, snapshot: SNAPSHOT) -> Self:
        coords = frozenset(Coordinate.from_tuple(t) for t in snapshot["coords"])
        frontier = {Coordinate.from_tuple(t) for t in snapshot["frontier"]}

        return cls(coords, frontier)

    def to_snapshot(self) -> SNAPSHOT:
        return {
            "coords": tuple(c.to_tuple() for c in self.coords),
            "frontier": tuple(c.to_tuple() for c in self.frontier),
        }

    def in_hull(self, pos: Coordinate) -> bool:
        return pos in self.coords

    def inside_hull(self, pos: Coordinate) -> bool:
        return pos in self.coords or self.in_inner_part(pos)

    def in_inner_part(self, pos: Coordinate) -> bool:
        raise NotImplementedError(
            "Inner part is not defined for coordinate hulls (you can implement it in a subclass if needed)"
        )


class CuboidHull(AbstractHull):
    def __init__(self, min_coord: Coordinate, max_coord: Coordinate, frontier: set[Coordinate] | None = None) -> None:
        super().__init__()
        self.min_coord = min_coord
        self.max_coord = max_coord

        if frontier is None:
            self.init_frontier()
        else:
            self.frontier = frontier

    def init_frontier(self):
        """Initialize the frontier with all the coordinates of the cuboid."""
        self.frontier.clear()
        minc, maxc = self.min_coord, self.max_coord

        for x in range(self.min_coord.x, self.max_coord.x + 1):
            for y in range(self.min_coord.y, self.max_coord.y + 1):
                for z in range(self.min_coord.z, self.max_coord.z + 1):
                    if x == minc.x or x == maxc.x or y == minc.y or y == maxc.y or z == minc.z or z == maxc.z:
                        self.frontier.add(Coordinate(x, y, z))

    @classmethod
    def from_snapshot(cls, snapshot: SNAPSHOT) -> Self:
        minc = Coordinate.from_tuple(snapshot["min"])
        maxc = Coordinate.from_tuple(snapshot["max"])
        frontier = {Coordinate.from_tuple(t) for t in snapshot["frontier"]}

        return cls(minc, maxc, frontier)

    def to_snapshot(self) -> SNAPSHOT:
        return {
            "min": self.min_coord.to_tuple(),
            "max": self.max_coord.to_tuple(),
            "frontier": tuple(c.to_tuple() for c in self.frontier),
        }

    def in_hull(self, pos: Coordinate) -> bool:
        minc, maxc = self.min_coord, self.max_coord
        px, py, pz = pos.x, pos.y, pos.z
        return (
            px == minc.x or px == maxc.x or py == minc.y or py == maxc.y or pz == minc.z or pz == maxc.z
        ) and self.inside_hull(pos)

    def inside_hull(self, pos: Coordinate) -> bool:
        minc, maxc = self.min_coord, self.max_coord
        px, py, pz = pos.x, pos.y, pos.z
        return minc.x <= px <= maxc.x and minc.y <= py <= maxc.y and minc.z <= pz <= maxc.z

    def in_inner_part(self, pos: Coordinate) -> bool:
        minc, maxc = self.min_coord, self.max_coord
        px, py, pz = pos.x, pos.y, pos.z
        return minc.x < px < maxc.x and minc.y < py < maxc.y and minc.z < pz < maxc.z
