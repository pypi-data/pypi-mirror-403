from __future__ import annotations

import importlib.resources
import json
import logging
from typing import Any, TYPE_CHECKING

from .errors import InvalidVolumeException
from .models import TWENTY_SIX_NEIGHBORHOOD_DIRECTIONS, Polycube, RotatedPolycube, Coordinate

if TYPE_CHECKING:
    from os import PathLike

_logger = logging.getLogger(__name__)

__all__ = (
    "collect_volume",
    "compute_volume",
    "find_connected_component",
    "get_extreme_points",
    "is_valid_fence",
    "load_polycubes",
    "load_pentacubes",
    "load_hexacubes",
    "load_heptacubes",
    "load_octacubes",
    "PolycubeDecoder",
    "PolycubeEncoder",
)


def is_valid_fence(coords: set[Coordinate]) -> bool:
    """Checks if the given set of coordinates form a valid fence in 3D space."""
    # TODO build a check whether all used polycubes are only used once and are valid to their ID
    #  (is one of the known rotated polycubes)
    return compute_volume(coords) > 0


def _is_border_coordinate(coord: Coordinate, max_extrem_point: Coordinate, min_extrem_point: Coordinate) -> bool:
    """Checks if the given coordinate is on the border of the bounding box defined by the max values."""
    return (
        coord.x == max_extrem_point.x
        or coord.x == min_extrem_point.x
        or coord.y == max_extrem_point.y
        or coord.y == min_extrem_point.y
        or coord.z == max_extrem_point.z
        or coord.z == min_extrem_point.z
    )


def find_connected_component(visible_coords: set[Coordinate]) -> set[Coordinate]:
    """Finds all coordinates connected to the first coordinate in the set using 26-neighborhood."""
    start = visible_coords.pop()
    stack = [start]
    component: set[Coordinate] = {start}

    while stack:
        current = stack.pop()

        for delta in TWENTY_SIX_NEIGHBORHOOD_DIRECTIONS:
            neighbor = current + delta
            if neighbor not in visible_coords:
                continue

            stack.append(neighbor)
            component.add(neighbor)
            visible_coords.remove(neighbor)

    return component


def get_extreme_points(coords: set[Coordinate]) -> tuple[Coordinate, Coordinate]:
    initial_coord = coords.pop()
    x_max, y_max, z_max = initial_coord.x, initial_coord.y, initial_coord.z
    x_min, y_min, z_min = initial_coord.x, initial_coord.y, initial_coord.z
    for coord in coords:
        x_max = max(x_max, coord.x)
        y_max = max(y_max, coord.y)
        z_max = max(z_max, coord.z)
        x_min = min(x_min, coord.x)
        y_min = min(y_min, coord.y)
        z_min = min(z_min, coord.z)
    coords.add(initial_coord)

    return Coordinate(x_max, y_max, z_max), Coordinate(x_min, y_min, z_min)


def collect_volume(coords: set[Coordinate]) -> set[Coordinate]:
    """Compute the volume from the hull formed by the coordinates"""
    max_extreme_point, min_extreme_point = get_extreme_points(coords)
    max_extreme_point = Coordinate(max_extreme_point.x + 1, max_extreme_point.y + 1, max_extreme_point.z + 1)
    min_extreme_point = Coordinate(min_extreme_point.x - 1, min_extreme_point.y - 1, min_extreme_point.z - 1)

    visible_coords = {
        c
        for x in range(min_extreme_point.x, max_extreme_point.x + 1)
        for y in range(min_extreme_point.y, max_extreme_point.y + 1)
        for z in range(min_extreme_point.z, max_extreme_point.z + 1)
        if (c := Coordinate(x, y, z)) not in coords
    }

    # the here popped coordinate is always outside the hull; this is because we added this outside new layer!
    find_connected_component(visible_coords)

    if not visible_coords:
        _logger.warning("No volume found! Only one component detected.")
        return set()

    volume_cubes = find_connected_component(visible_coords)
    if visible_coords:
        _logger.warning(
            f"Found {len(volume_cubes)} as volume, but still {len(visible_coords)} unvisited cubes left. Another enclosed area exists!"
        )
        raise InvalidVolumeException("Volume has multiple components")

    if any(_is_border_coordinate(c, max_extreme_point, min_extreme_point) for c in volume_cubes):
        _logger.warning("Volume has been found on the border! Bug in the validation.")
        raise InvalidVolumeException("Volume has been found on the border")

    return volume_cubes


def compute_volume(coords: set[Coordinate]) -> int:
    """
    Ruft die Funktion collect_volume auf, um alle Punkte der Volumen-Komponente zu erhalten.
    Die Anzahl dieser Punkte ist das Volumen.
    """
    volume_cubes = collect_volume(coords)
    return len(volume_cubes)


class PolycubeEncoder(json.JSONEncoder):
    """JSON Encoder for Polycube objects."""

    def default(self, o: Any) -> Any:
        if isinstance(o, Polycube):
            return {"id": o.id, "rotations": [self.default(rot) for rot in o.rotations]}

        if isinstance(o, RotatedPolycube):
            return {"id": o.id, "coords": [self.default(coord) for coord in o.coords]}

        if isinstance(o, Coordinate):
            return {"x": o.x, "y": o.y, "z": o.z}

        return super().default(o)


class PolycubeDecoder(json.JSONDecoder):
    """JSON Decoder for Polycube objects."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(object_hook=self._polycube_object_hook, *args, **kwargs)

    @staticmethod
    def _polycube_object_hook(obj: Any) -> Any:
        # Coordinate dict -> Coordinate instance
        if set(obj.keys()) == {"x", "y", "z"}:
            return Coordinate(obj["x"], obj["y"], obj["z"])

        # RotatedPolycube dict -> RotatedPolycube instance
        if "id" in obj and "coords" in obj:
            # coords expected to be list of Coordinate instances (from inner object_hook)
            return RotatedPolycube(id=obj["id"], coords=frozenset(obj["coords"]))

        # Polycube dict -> Polycube instance
        if "id" in obj and "rotations" in obj:
            # rotations expected to be list of RotatedPolycube instances
            return Polycube(id=obj["id"], rotations=tuple(obj["rotations"]))

        return obj


def load_polycubes(filename: str | PathLike[str]) -> tuple[Polycube, ...]:
    """Load polycubes from a JSON file."""
    with open(filename, encoding="UTF-8") as f:
        js = json.load(f, cls=PolycubeDecoder)

    return tuple(js)


def _load_resource(filename: str) -> tuple[Polycube, ...]:
    """Load a resource file from the package's data directory."""
    resource_path = importlib.resources.files(__package__) / "data" / filename
    with importlib.resources.as_file(resource_path) as path:
        return load_polycubes(path)


def load_pentacubes() -> tuple[Polycube, ...]:
    """Load pentacubes from the default JSON file."""
    return _load_resource("pentacubes.json")


def load_hexacubes() -> tuple[Polycube, ...]:
    """Load hexacubes from the default JSON file."""
    return _load_resource("hexacubes.json")


def load_heptacubes() -> tuple[Polycube, ...]:
    """Load heptacubes from the default JSON file."""
    return _load_resource("heptacubes.json")


def load_octacubes() -> tuple[Polycube, ...]:
    """Load octacubes from the default JSON file."""
    return _load_resource("octacubes.json")
