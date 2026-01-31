from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from concurrent.futures import Future, ProcessPoolExecutor
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Iterable, Sequence, Callable

from .grid import HullGrid
from .models import Placement, PolycubePlacement

if TYPE_CHECKING:
    from os import PathLike

    from .hull import AbstractHull
    from .grid import Grid
    from .models import Polycube, JSON_SOLUTION, SNAPSHOT

__all__ = ("AbstractSolver", "ParallelSolver", "ScoreSolver", "SolverStatus")


class SolverStatus(StrEnum):
    INITIALIZED = auto()
    RUNNING = auto()
    FINISHED = auto()
    FAILED = auto()


class AbstractSolver[G: Grid](ABC):
    def __init__(self, grid: G, polycubes: tuple[Polycube, ...]) -> None:
        """The base init function. It must be called when being overwritten: super().__init__(grid, polycubes)"""
        self._grid = grid
        self._polycubes = polycubes
        self._status = SolverStatus.INITIALIZED
        self._logger = logging.getLogger(__name__)

    @property
    def grid(self) -> G:
        return self._grid

    @property
    def polycubes(self) -> tuple[Polycube, ...]:
        return self._polycubes

    @property
    def status(self) -> SolverStatus:
        return self._status

    def set_finished(self) -> None:
        self._status = SolverStatus.FINISHED

    def set_failed(self, message: str) -> None:
        self._status = SolverStatus.FAILED
        self._logger.error("Run failed: %s", message)

    @abstractmethod
    def step(self) -> None:
        """Performs a single iteration of the solving logic.
        This method should eventually call self.set_finished() or self.set_failed() to finish the run.
        """
        pass

    def is_running(self) -> bool:
        return self.status == SolverStatus.RUNNING

    def run(self, output_file: str | PathLike[str] | None) -> JSON_SOLUTION:
        """Runs the solver until the status is set to finished or failed.
        Finally returns the grid as JSON and writes it to the specified file if specified.
        """
        self._status = SolverStatus.RUNNING
        self._logger.info("Solver run started")

        while self.is_running():
            self.step()

        self.done()
        return self.grid.to_json(output_file)

    def done(self):
        self._logger.info("Solver run completed with status: %s", self.status)


class _GenericScoreSolver[H: AbstractHull, C, SC, SR](AbstractSolver[HullGrid[H]], ABC):
    def __init__(self, grid: HullGrid[H], polycubes: tuple[Polycube, ...]) -> None:
        super().__init__(grid, polycubes)
        self.remaining: dict[int, Polycube] = {p.id: p for p in polycubes}

    @abstractmethod
    def score(self, candidate: SC) -> SR:
        pass

    @abstractmethod
    def next_candidates(self) -> Sequence[C]:
        pass

    @abstractmethod
    def _compute_best(self, candidates: Iterable[C]) -> tuple[Placement | None, int]:
        """Computes the highest scoring candidate, deterministically."""
        pass

    def after_place(self, placement: Placement) -> None:
        """Called after a polycube is placed, override if needed, but you should call the super method."""
        del self.remaining[placement.rotated_polycube.id]

    def step(self) -> None:
        candidates = self.next_candidates()
        if not candidates:
            self.set_failed("No more candidates to try")
            return

        p, score = self._compute_best(candidates)
        if p is None:
            self.set_failed("No valid placement found")
            return

        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug("Selected best candidate: %s with score: %d", p, score)

        if not self.grid.can_place(p.rotated_polycube, p.pos):
            self.set_failed("Found placement is not valid")
            return

        self.grid.place(p.rotated_polycube, p.pos)
        self.after_place(p)
        if not self.grid.frontier:
            self.set_finished()


class ScoreSolver[H: AbstractHull](_GenericScoreSolver[H, Placement, Placement, int], ABC):
    def _compute_best(self, candidates: Iterable[Placement]) -> tuple[Placement | None, int]:
        """Computes the highest scoring candidate, deterministically."""
        p = max(candidates, key=self.score)
        return p, self.score(p)


type _snapshots = tuple[SNAPSHOT, SNAPSHOT, SNAPSHOT]
type _future_result = Future[tuple[SNAPSHOT, int]]


class ParallelSolver[H: AbstractHull](_GenericScoreSolver[H, PolycubePlacement, _snapshots, _future_result]):
    def __init__(
        self,
        grid: HullGrid[H],
        polycubes: tuple[Polycube, ...],
        scorer: Callable[[SNAPSHOT, SNAPSHOT, SNAPSHOT], tuple[SNAPSHOT, int]],
    ):
        super().__init__(grid, polycubes)
        self.scorer = scorer

        max_workers = os.cpu_count() or 1
        self.ex = ProcessPoolExecutor(max_workers=max_workers)

    @abstractmethod
    def next_candidates(self) -> Sequence[PolycubePlacement]:
        pass

    def score(self, candidate: _snapshots) -> _future_result:
        return self.ex.submit(self.scorer, *candidate)

    def _compute_best(self, candidates: Iterable[PolycubePlacement]) -> tuple[Placement | None, int]:
        grid_snap = self.grid.to_snapshot()
        hull_snap = self.grid.hull.to_snapshot()

        futures: list[_future_result] = [self.score((hull_snap, grid_snap, p.to_snapshot())) for p in candidates]
        best_score = -100000
        best_p: SNAPSHOT | None = None
        for fut in futures:
            placement, score = fut.result()
            if score > best_score:
                best_score = score
                best_p = placement

        return Placement.from_snapshot(best_p) if best_p is not None else None, best_score

    def done(self):
        super().done()
        self.ex.shutdown()
