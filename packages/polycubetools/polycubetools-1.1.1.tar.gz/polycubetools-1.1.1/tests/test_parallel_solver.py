from __future__ import annotations

import pytest
from polycubetools import (
    Coordinate,
    CuboidHull,
    HullGrid,
    ParallelSolver,
    Polycube,
    Placement,
    RotatedPolycube,
    PolycubePlacement,
    SNAPSHOT,
)


def scorer(hull_snap: SNAPSHOT, grid_snap: SNAPSHOT, polycube_placement_snap:SNAPSHOT) -> tuple[SNAPSHOT, int]:
    pc_placement = PolycubePlacement.from_snapshot(polycube_placement_snap)
    rpc = pc_placement.polycube.rotations[0]
    return Placement(rpc, pc_placement.pos).to_snapshot(), len(rpc.coords)


class PSolver(ParallelSolver[CuboidHull]):
    def next_candidates(self) -> list[PolycubePlacement]:
        active_frontier = self.grid.active_frontier

        v: list[PolycubePlacement] = []
        for cube in self.remaining.values():
            for position in active_frontier:
                v.append(PolycubePlacement(cube, position))
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

    solver = PSolver(grid, (pc,), scorer)
    out = solver.run(output_file=str(tmp_path / "out.json"))

    # solver should produce a JSON solution (list) even if no placement was possible
    assert isinstance(out, list)
