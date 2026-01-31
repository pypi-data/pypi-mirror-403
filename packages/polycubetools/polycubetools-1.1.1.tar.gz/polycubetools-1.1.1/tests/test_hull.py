from __future__ import annotations

import pytest

from polycubetools import Coordinate
from polycubetools.hull import CuboidHull, CoordinateHull


class TestCuboidHullInHull:
    """Tests for CuboidHull.in_hull method."""

    def test_in_hull_inside_point(self):
        """A point strictly inside the cuboid should be in the hull."""
        hull = CuboidHull(Coordinate(0, 0, 0), Coordinate(4, 4, 4))
        assert hull.inside_hull(Coordinate(2, 2, 2))

    def test_in_hull_on_boundary(self):
        """A point on the boundary should be in the hull."""
        hull = CuboidHull(Coordinate(0, 0, 0), Coordinate(4, 4, 4))
        # On face
        assert hull.inside_hull(Coordinate(0, 2, 2))
        assert hull.inside_hull(Coordinate(4, 2, 2))
        # On edge
        assert hull.inside_hull(Coordinate(0, 0, 2))
        # On corner
        assert hull.inside_hull(Coordinate(0, 0, 0))
        assert hull.inside_hull(Coordinate(4, 4, 4))

    def test_in_hull_outside_point(self):
        """A point outside the cuboid should not be in the hull."""
        hull = CuboidHull(Coordinate(0, 0, 0), Coordinate(4, 4, 4))
        # Outside in x
        assert not hull.inside_hull(Coordinate(-1, 2, 2))
        assert not hull.inside_hull(Coordinate(5, 2, 2))
        # Outside in y
        assert not hull.inside_hull(Coordinate(2, -1, 2))
        assert not hull.inside_hull(Coordinate(2, 5, 2))
        # Outside in z
        assert not hull.inside_hull(Coordinate(2, 2, -1))
        assert not hull.inside_hull(Coordinate(2, 2, 5))

    def test_in_hull_with_negative_coordinates(self):
        """Test hull with negative coordinate bounds."""
        hull = CuboidHull(Coordinate(-3, -3, -3), Coordinate(3, 3, 3))
        assert hull.inside_hull(Coordinate(0, 0, 0))
        assert hull.inside_hull(Coordinate(-3, -3, -3))
        assert hull.inside_hull(Coordinate(3, 3, 3))
        assert not hull.inside_hull(Coordinate(-4, 0, 0))

    def test_in_hull_single_point(self):
        """Test a hull that is a single point."""
        hull = CuboidHull(Coordinate(1, 1, 1), Coordinate(1, 1, 1))
        assert hull.inside_hull(Coordinate(1, 1, 1))
        assert not hull.inside_hull(Coordinate(0, 1, 1))
        assert not hull.inside_hull(Coordinate(2, 1, 1))


class TestCuboidHullOnHull:
    """Tests for CuboidHull.on_hull method."""

    def test_on_hull_corner(self):
        """Corner points should be on the hull."""
        hull = CuboidHull(Coordinate(0, 0, 0), Coordinate(4, 4, 4))
        assert hull.in_hull(Coordinate(0, 0, 0))
        assert hull.in_hull(Coordinate(4, 4, 4))
        assert hull.in_hull(Coordinate(0, 4, 4))
        assert hull.in_hull(Coordinate(4, 0, 0))

    def test_on_hull_edge(self):
        """Edge points should be on the hull."""
        hull = CuboidHull(Coordinate(0, 0, 0), Coordinate(4, 4, 4))
        assert hull.in_hull(Coordinate(0, 0, 2))
        assert hull.in_hull(Coordinate(4, 4, 2))
        assert hull.in_hull(Coordinate(2, 0, 0))

    def test_on_hull_face(self):
        """Points on faces should be on the hull."""
        hull = CuboidHull(Coordinate(0, 0, 0), Coordinate(4, 4, 4))
        # x-face
        assert hull.in_hull(Coordinate(0, 2, 2))
        assert hull.in_hull(Coordinate(4, 2, 2))
        # y-face
        assert hull.in_hull(Coordinate(2, 0, 2))
        assert hull.in_hull(Coordinate(2, 4, 2))
        # z-face
        assert hull.in_hull(Coordinate(2, 2, 0))
        assert hull.in_hull(Coordinate(2, 2, 4))

    def test_on_hull_interior_point(self):
        """Interior points should NOT be on the hull."""
        hull = CuboidHull(Coordinate(0, 0, 0), Coordinate(4, 4, 4))
        assert not hull.in_hull(Coordinate(2, 2, 2))
        assert not hull.in_hull(Coordinate(1, 1, 1))
        assert not hull.in_hull(Coordinate(3, 3, 3))

    def test_on_hull_outside_point(self):
        """Points outside the hull should NOT be on the hull."""
        hull = CuboidHull(Coordinate(0, 0, 0), Coordinate(4, 4, 4))
        assert not hull.in_hull(Coordinate(-1, 2, 2))
        assert not hull.in_hull(Coordinate(5, 2, 2))
        # Even if one coordinate matches a boundary
        assert not hull.in_hull(Coordinate(0, 5, 2))

    def test_on_hull_with_negative_coordinates(self):
        """Test on_hull with negative coordinate bounds."""
        hull = CuboidHull(Coordinate(-2, -2, -2), Coordinate(2, 2, 2))
        # Corners
        assert hull.in_hull(Coordinate(-2, -2, -2))
        assert hull.in_hull(Coordinate(2, 2, 2))
        # Face
        assert hull.in_hull(Coordinate(-2, 0, 0))
        # Interior
        assert not hull.in_hull(Coordinate(0, 0, 0))

    def test_on_hull_single_point(self):
        """A single-point hull should be on the hull."""
        hull = CuboidHull(Coordinate(1, 1, 1), Coordinate(1, 1, 1))
        assert hull.in_hull(Coordinate(1, 1, 1))
        assert not hull.in_hull(Coordinate(0, 1, 1))


class TestCoordinateHullInHull:
    """Tests for CoordinateHull.in_hull method."""

    def test_in_hull_present_coordinate(self):
        """Coordinates in the set should be in the hull."""
        coords = frozenset({
            Coordinate(0, 0, 0),
            Coordinate(1, 0, 0),
            Coordinate(0, 1, 0),
        })
        hull = CoordinateHull(coords)
        assert hull.in_hull(Coordinate(0, 0, 0))
        assert hull.in_hull(Coordinate(1, 0, 0))
        assert hull.in_hull(Coordinate(0, 1, 0))

    def test_in_hull_absent_coordinate(self):
        """Coordinates not in the set should not be in the hull."""
        coords = frozenset({
            Coordinate(0, 0, 0),
            Coordinate(1, 0, 0),
        })
        hull = CoordinateHull(coords)
        assert not hull.in_hull(Coordinate(2, 0, 0))
        assert not hull.in_hull(Coordinate(0, 1, 0))
        assert not hull.in_hull(Coordinate(-1, 0, 0))

    def test_in_hull_empty_hull(self):
        """Empty hull should contain no coordinates."""
        hull = CoordinateHull(frozenset())
        assert not hull.in_hull(Coordinate(0, 0, 0))
