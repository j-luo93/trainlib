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

# ---------------------------------------------------------------------------- #
#                               Trackable section                              #
# ---------------------------------------------------------------------------- #


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

# ---------------------------------------------------------------------------- #
#                                Tracker section                               #
# ---------------------------------------------------------------------------- #


@dataclass
class WhenToFinish:
    name: str
    value: Any


@dataclass
class Task:
    def __hash__(self):
        return id(self)

    def __eq__(self, other: Task):
        return id(self) == id(other)


class FinishConditionException(Exception):
    pass


UpdateFn = Union[str, Callable[[], None]]


class Tracker:

    def __init__(self):
        self._legacy_attrs = dict()
        self._legacy_update_fns = dict()
        self._legacy_when_to_finish = None

        self.trackables: Dict[name, Trackable] = dict()
        self.tasks: List[Task] = list()
        self.task_weights: List[Task] = list()

    @property
    @deprecated(reason='This is the old way of adding trackables.', action='once')
    def _attrs(self):
        return self._legacy_attrs

    @property
    @deprecated(reason='This is the old way of adding trackables.', action='once')
    def _update_fns(self):
        return self._legacy_update_fns

    @property
    @deprecated(reason='This is the old way of adding trackables.', action='once')
    def _when_to_finish(self):
        return self._legacy_when_to_finish

    @_when_to_finish.setter
    @deprecated(reason='This is the old way of adding trackables.', action='once')
    def _when_to_finish(self, value):
        self._legacy_when_to_finish = value

    @property
    def is_finished(self):
        if self._when_to_finish is None:
            raise FinishConditionException('Finishing condition not supplied.')
        return self._attrs[self._when_to_finish.name] >= self._when_to_finish.value

    def finish_when(self, name: str, value: Any):
        if not self._when_to_finish is None:
            raise FinishConditionException('Finishing condition already supplied.')
        self._when_to_finish = WhenToFinish(name, value)

    @deprecated(reason='use add_trackable', action='once')
    def add_track(self, name: str, init_value: Any = 0, *, update_fn: UpdateFn = None, finish_when: Any = None):
        if name in self._attrs:
            raise NameError(f'A track named "{name}" already exists.')

        self._attrs[name] = init_value
        if update_fn is not None:
            self.add_update_fn(name, update_fn)
        if finish_when is not None:
            self.finish_when(name, finish_when)

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

    def __getattribute__(self, attr: str):
        try:
            return super().__getattribute__(attr)
        except AttributeError as e:
            # NOTE(j_luo) This is called after __getattr__.
            if attr in self._attrs:
                return self._attrs[attr]
            else:
                raise

    def __getattr__(self, attr: str):
        try:
            return self.trackables[attr].value
        except KeyError:
            raise AttributeError(f'No trackable named {attr}.')

    def load(self, name: str, value: Any):
        self._attrs[name] = value

    def add_update_fn(self, name_to_update: str, update_fn: UpdateFn):
        if name_to_update in self._update_fns:
            raise NameError(f'An update function for {name_to_update} already exists.')

        if isinstance(update_fn, str):
            def add(x=1):
                self._attrs[name_to_update] += x

            if update_fn == 'add':
                update_fn = add
            elif update_fn == 'addx':
                update_fn = lambda x: add(x)
            else:
                raise NotImplementedError(f'Not recognized update function named "{update_fn}"')

        self._update_fns[name_to_update] = update_fn

    def update(self, *names: str):
        warnings.warn('You might need to use legacy_update.')
        for name in names:
            self.trackables[name].update()

    @deprecated(reason='Calling legacy_update.', action='once')
    def legacy_update(self, names_to_update: Union[str, List[str]] = None, value: Any = None):
        if value is not None and not isinstance(names_to_update, str):
            raise TypeError(f'Cannot specify a value for update, and a list of names to update at the same time.')

        if isinstance(names_to_update, str):
            name = names_to_update
            if value is None:
                self._update_fns[name]()
            else:
                self._update_fns[name](value)
        else:
            if names_to_update is None:
                names_to_update = self._update_fns.keys()
            for name in names_to_update:
                self._update_fns[name]()

    @property
    def now_as_tuple(self):
        return tuple(sorted(self._attrs.items()))

    @property
    def now(self):
        return '-'.join([f'{k}_{v}'for k, v in self.now_as_tuple])
