from __future__ import annotations

import pytest
from polycubetools import Coordinate, RotatedPolycube, utils, InvalidVolumeException


def test_validation_of_compactness():
    # use a cuboid
    cube = {
        Coordinate(x, y, z)
        for x in range(3)
        for y in range(3)
        for z in range(3)
        if x == 0 or x == 2 or y == 0 or y == 2 or z == 0 or z == 2
    }
    volume = utils.compute_volume(cube)
    assert volume == 1

    # remove side cube
    cube.remove(Coordinate(2, 1, 1))
    volume = utils.compute_volume(cube)
    assert volume == 0
    cube.add(Coordinate(2, 1, 1))

    # remove corner cube
    cube.remove(Coordinate(0, 0, 0))
    volume = utils.compute_volume(cube)
    assert volume == 0
    cube.add(Coordinate(0, 0, 0))

    cube.add(Coordinate(3, 1, 1))
    volume = utils.compute_volume(cube)
    assert volume == 1

    # now it has no volume
    cube.add(Coordinate(1, 1, 1))
    volume = utils.compute_volume(cube)
    assert volume == 0
    cube.remove(Coordinate(1, 1, 1))

    cuboid = {
        Coordinate(x, y, z)
        for x in range(4, 7)
        for y in range(5, 10)
        for z in range(7, 10)
        if (x, y, z) != (5, 6, 8) and (x, y, z) != (5, 7, 8)
    }
    volume = utils.compute_volume(cuboid)
    assert volume == 2

    two_hulls = cube.union(cuboid)
    with pytest.raises(InvalidVolumeException, match="Volume has multiple components"):
        volume = utils.compute_volume(two_hulls)

    two_hulls_with_one_empty_hull = two_hulls
    two_hulls_with_one_empty_hull.add(Coordinate(1, 1, 1))
    volume = utils.compute_volume(two_hulls_with_one_empty_hull)
    # we could also compute the sum of the enclosed area by multiple components
    assert volume == 2


def test_get_all_neighbor_cells():
    coords = frozenset({Coordinate(0, 0, 0), Coordinate(1, 0, 0)})
    polycube = RotatedPolycube(id=1, coords=coords)
    neighbors = polycube.get_all_neighbor_cells()

    expected = frozenset(
        {
            # neighbors of (0,0,0) except (1,0,0)
            Coordinate(-1, 0, 0),
            Coordinate(0, 1, 0),
            Coordinate(0, -1, 0),
            Coordinate(0, 0, 1),
            Coordinate(0, 0, -1),
            # neighbors of (1,0,0) except (0,0,0)
            Coordinate(2, 0, 0),
            Coordinate(1, 1, 0),
            Coordinate(1, -1, 0),
            Coordinate(1, 0, 1),
            Coordinate(1, 0, -1),
        }
    )

    assert neighbors == expected

    coords = frozenset(
        {
            Coordinate(0, 0, 0),
            Coordinate(1, 0, 0),
            Coordinate(2, 0, 0),
            Coordinate(2, 1, 0),
        }
    )
    rp = RotatedPolycube(id=2, coords=coords)

    neighbors = rp.get_all_neighbor_cells()

    expected = frozenset(
        {
            # from (0,0,0)
            Coordinate(-1, 0, 0),
            Coordinate(0, 1, 0),
            Coordinate(0, -1, 0),
            Coordinate(0, 0, 1),
            Coordinate(0, 0, -1),
            # from (1,0,0)
            Coordinate(1, 1, 0),
            Coordinate(1, -1, 0),
            Coordinate(1, 0, 1),
            Coordinate(1, 0, -1),
            # from (2,0,0)
            Coordinate(3, 0, 0),
            Coordinate(2, -1, 0),
            Coordinate(2, 0, 1),
            Coordinate(2, 0, -1),
            # from (2,1,0)
            Coordinate(1, 1, 0),  # duplicate, but frozenset deduplicates
            Coordinate(3, 1, 0),
            Coordinate(2, 2, 0),
            Coordinate(2, 1, 1),
            Coordinate(2, 1, -1),
        }
    )

    assert neighbors == expected
