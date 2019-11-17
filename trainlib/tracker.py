"""
A Tracker instance is responsible for:
1. tracking epochs, rounds, steps or any Trackable instances.
2. tracking some curriculum- or annealing-related hyperparameters.
3. tracking metrics.
4. displaying a progress bar (through trackables.)
"""

from __future__ import annotations

import random
import time
import warnings
from collections import UserDict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Sequence, Union

import enlighten
from deprecated import deprecated

# -------------------------------------------------------------- #
#                        Trackable section                       #
# -------------------------------------------------------------- #


def reset_all():
    Trackable.reset_all()


class PBarOutOfBound(Exception):
    pass


class Trackable:

    _manager = enlighten.get_manager()
    _instances: Dict[str, Trackable] = dict()

    @classmethod
    def reset_all(cls):
        cls._manager = enlighten.get_manager()
        cls._instances.clear()

    def __init__(self, name: str, total: int = None, parent: Trackable = None, tracker: Tracker = None):
        """
        If `parent` is set, then this trackable will be reset whenever the parent is updated.
        """
        if name in self._instances:
            raise ValueError(f'A trackable named "{name}" already exists.')

        self._name = name
        self._total = total
        self._pbar = self._manager.counter(desc=name, total=total)
        self._to_reset: List[Trackable] = list()
        self._instances[name] = self

        if parent is not None:
            parent._to_reset.append(self)

        self._tracker = tracker
        if tracker is not None:
            # NOTE(j_luo) This is where trackables are updated for a tracker.
            self._tracker.trackables[name] = self

    @property
    def total(self):
        return self._total

    def update(self):
        self._pbar.update()
        if self._total is not None and self._pbar.count > self._total:
            raise PBarOutOfBound(f'Progress bar ran out of bound.')
        for trackable in self._to_reset:
            trackable.reset()

    def add_trackable(self, name: str, total: int = None) -> Trackable:
        trackable = Trackable(name, total=total, parent=self, tracker=self._tracker)
        return trackable

    def reset(self):
        self._pbar.start = time.time()
        self._pbar.count = 0
        self._pbar.refresh()

    @property
    def value(self):
        return self._pbar.count

# -------------------------------------------------------------- #
#                         Tracker section                        #
# -------------------------------------------------------------- #


@dataclass
class Task:
    def __hash__(self):
        return id(self)

    def __eq__(self, other: Task):
        return id(self) == id(other)


class Tracker:

    def __init__(self):
        self.trackables: Dict[str, Trackable] = dict()
        self.tasks: List[Task] = list()
        self.task_weights: List[Task] = list()

    def is_finished(self, name: str):
        return self.trackables[name].value >= self.trackables[name].total

    def add_trackable(self, name: str, total: int = None) -> Trackable:
        # NOTE(j_luo) self.trackables is actually handled by every Trackable constructor call.
        trackable = Trackable(name, total=total, tracker=self)
        return trackable

    def add_task(self, task: Task, weight: float):
        self.tasks.append(task)
        self.task_weights.append(weight)

    def add_tasks(self, tasks: Sequence[Task], weights: List[float]):
        if len(tasks) != len(weights):
            raise ValueError(f'Mismatched lengths from tasks ({len(tasks)}) and weights ({len(weights)}).')
        for task, weight in zip(tasks, weights):
            self.add_task(task, weight)

    def draw_task(self) -> Task:
        task = random.choices(self.tasks, weights=self.task_weights)[0]
        return task

    def __getattr__(self, attr: str):
        try:
            return self.trackables[attr].value
        except KeyError:
            raise AttributeError(f'No trackable named {attr}.')

    def update(self, *names: str):
        for name in names:
            self.trackables[name].update()
