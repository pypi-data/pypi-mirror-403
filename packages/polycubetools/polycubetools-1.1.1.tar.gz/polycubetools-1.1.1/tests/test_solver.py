from __future__ import annotations

import pytest
from polycubetools import (
    Coordinate,
    CuboidHull,
    HullGrid,
    Placement,
    ScoreSolver,
    Polycube,
    RotatedPolycube,
)


class GreedySolver(ScoreSolver[CuboidHull]):
    def score(self, candidate: Placement) -> int:
        return 1

    def next_candidates(self) -> list[Placement]:
        active_frontier = self.grid.active_frontier

        v: list[Placement] = []
        for cube in self.remaining.values():
            for rotation in cube.rotations:
                for position in active_frontier:
                    v.append(Placement(rotation, position))
        return v


def test_solver_smoke(tmp_path):
    # simple hull and grid
    minc = Coordinate(0, 0, 0)
    maxc = Coordinate(1, 1, 1)
    hull = CuboidHull(minc, maxc)
    grid = HullGrid(Coordinate(3, 3, 3), hull)

    # one single-cube polycube
    rot = RotatedPolycube(id=42, coords=frozenset({Coordinate(0, 0, 0)}))
    pc = Polycube(id=42, rotations=(rot,))

    solver = GreedySolver(grid, (pc,))
    out = solver.run(output_file=str(tmp_path / "out.json"))

    # solver should produce a JSON solution (list) even if no placement was possible
    assert isinstance(out, list)
