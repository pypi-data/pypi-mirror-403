from __future__ import annotations

import pytest
from polycubetools import (
    Coordinate,
    Grid,
    Polycube,
    RotatedPolycube,
)


def test_grid_place_and_export():
    pc = Polycube(3, (RotatedPolycube(3, frozenset((Coordinate(0, 0, 0), Coordinate(0, 0, 1), Coordinate(0, 1, 1)))),))
    grid = Grid(Coordinate(20, 20, 20))

    assert grid.in_bounds(Coordinate(12, 13, 8)), "Check in Bounds 12, 13, 8"

    rcube = pc.rotations[0]
    assert grid.can_place(rcube, Coordinate(4, 5, 7)), "Check can place 0, 0, 1 at 4, 5, 7"

    grid.place(rcube, Coordinate(4, 5, 7))
    assert grid.to_json() == [[20, 20, 20], [3, 4, 5, 7], [3, 4, 5, 8], [3, 4, 6, 8]]
