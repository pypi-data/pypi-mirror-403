from __future__ import annotations

from dataclasses import dataclass

__all__ = (
    "Coordinate",
    "Placement",
    "Polycube",
    "PolycubePlacement",
    "RotatedPolycube",
    "JSON_SOLUTION",
    "SIX_NEIGHBORHOOD_DIRECTIONS",
    "SNAPSHOT",
    "TWENTY_SIX_NEIGHBORHOOD_DIRECTIONS",
)

from typing import Any, Self

type JSON_SOLUTION = list[list[int | str]]
type SNAPSHOT = dict[str, Any]


@dataclass(frozen=True, slots=True)
class Coordinate:
    """Represents a single point in a 3D grid."""

    x: int
    y: int
    z: int

    @classmethod
    def from_tuple(cls, coords: tuple[int, int, int]) -> Coordinate:
        return cls(*coords)

    def to_tuple(self) -> tuple[int, int, int]:
        return self.x, self.y, self.z

    def __add__(self, other: Coordinate) -> Coordinate:
        """Pairwise addition of coordinates."""
        return Coordinate(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Coordinate) -> Coordinate:
        """Pairwise subtraction of coordinates."""
        return Coordinate(self.x - other.x, self.y - other.y, self.z - other.z)


@dataclass(frozen=True, slots=True)
class RotatedPolycube:
    """Represents a specific rotation of a polycube."""

    id: int
    """The id of the base polycube."""
    coords: frozenset[Coordinate]
    """The coordinates of the n unit-cubes that make up the polycube."""

    def get_all_neighbor_cells(self) -> frozenset[Coordinate]:
        """Return all 6-neighborhood cells adjacent to this rotated polycube."""
        return frozenset(
            [
                point + offset
                for point in self.coords
                for offset in SIX_NEIGHBORHOOD_DIRECTIONS
                if point + offset not in self.coords
            ]
        )


@dataclass(frozen=True, slots=True)
class Polycube:
    """Represents a single n-polycube."""

    id: int
    rotations: tuple[RotatedPolycube, ...]
    """All unique rotations of this polycube."""


@dataclass(frozen=True, slots=True)
class Placement:
    """Represents a placement of a specifically rotated polycube on a specific coordinate."""

    rotated_polycube: RotatedPolycube
    pos: Coordinate

    @classmethod
    def from_snapshot(cls, snapshot: SNAPSHOT) -> Self:
        rpc_id = snapshot["rotated_polycube_id"]
        rpc_coords = frozenset(Coordinate.from_tuple(t) for t in snapshot["rotated_polycube_coords"])
        rpc = RotatedPolycube(rpc_id, rpc_coords)
        pos = Coordinate.from_tuple(snapshot["pos"])
        return cls(rpc, pos)

    def to_snapshot(self) -> SNAPSHOT:
        return {
            "rotated_polycube_id": self.rotated_polycube.id,
            "rotated_polycube_coords": tuple(c.to_tuple() for c in self.rotated_polycube.coords),
            "pos": self.pos.to_tuple(),
        }


@dataclass(frozen=True, slots=True)
class PolycubePlacement:
    """Represents a placement of a generic polycube, so all its rotations on a specific coordinate."""

    polycube: Polycube
    pos: Coordinate

    @classmethod
    def from_snapshot(cls, snapshot: SNAPSHOT) -> Self:
        polycube_id = snapshot["polycube_id"]
        rpc_coords = snapshot["rotated_polycube_coords"]
        rpcs = tuple(
            RotatedPolycube(polycube_id, frozenset(Coordinate.from_tuple(t) for t in rpc_coord))
            for rpc_coord in rpc_coords
        )
        polycube = Polycube(polycube_id, rpcs)
        pos = Coordinate.from_tuple(snapshot["pos"])
        return cls(polycube, pos)

    def to_snapshot(self) -> SNAPSHOT:
        return {
            "polycube_id": self.polycube.id,
            "rotated_polycube_coords": tuple(
                tuple(c.to_tuple() for c in rpc.coords) for rpc in self.polycube.rotations
            ),
            "pos": self.pos.to_tuple(),
        }


SIX_NEIGHBORHOOD_DIRECTIONS = (
    Coordinate(1, 0, 0),
    Coordinate(-1, 0, 0),
    Coordinate(0, 1, 0),
    Coordinate(0, -1, 0),
    Coordinate(0, 0, 1),
    Coordinate(0, 0, -1),
)
"""All possible directions in a 3D Grid (without diagonals).
The neighbors grows additively with the dimension: 2 * dimension."""

TWENTY_SIX_NEIGHBORHOOD_DIRECTIONS = (
    # 6 orthogonal directions (6-neighborhood)
    Coordinate(1, 0, 0),
    Coordinate(-1, 0, 0),
    Coordinate(0, 1, 0),
    Coordinate(0, -1, 0),
    Coordinate(0, 0, 1),
    Coordinate(0, 0, -1),
    # 12 edge-diagonal directions (connecting edge centers)
    Coordinate(1, 1, 0),
    Coordinate(1, -1, 0),
    Coordinate(-1, 1, 0),
    Coordinate(-1, -1, 0),
    Coordinate(1, 0, 1),
    Coordinate(1, 0, -1),
    Coordinate(-1, 0, 1),
    Coordinate(-1, 0, -1),
    Coordinate(0, 1, 1),
    Coordinate(0, 1, -1),
    Coordinate(0, -1, 1),
    Coordinate(0, -1, -1),
    # 8 face-diagonal directions (connecting corners)
    Coordinate(1, 1, 1),
    Coordinate(1, 1, -1),
    Coordinate(1, -1, 1),
    Coordinate(1, -1, -1),
    Coordinate(-1, 1, 1),
    Coordinate(-1, 1, -1),
    Coordinate(-1, -1, 1),
    Coordinate(-1, -1, -1),
)
"""All possible directions in a 3D Grid.
The neighbors grows exponentially with the dimension: 3 ^ dimension - 1."""
