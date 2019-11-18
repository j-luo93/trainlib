from __future__ import annotations

import time
from typing import Dict, List

import enlighten


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

    def __init__(self, name: str, total: int = None, parent: Trackable = None):
        """
        If `parent` is set, then this trackable will be reset whenever the parent is updated.
        """
        if name in self._instances:
            raise ValueError(f'A trackable named "{name}" already exists.')

        self._name = name
        self._total = total
        self._pbar = self._manager.counter(desc=name, total=total)
        self._instances[name] = self

        self.children: List[Trackable] = list()
        if parent is not None:
            # NOTE(j_luo) Every child here would be reset after the parent is updated.
            parent.children.append(self)

    @property
    def total(self):
        return self._total

    @property
    def name(self):
        return self._name

    def update(self):
        self._pbar.update()
        if self._total is not None and self._pbar.count > self._total:
            raise PBarOutOfBound(f'Progress bar ran out of bound.')
        for trackable in self.children:
            trackable.reset()

    def add_trackable(self, name: str, total: int = None) -> Trackable:
        trackable = Trackable(name, total=total, parent=self)
        return trackable

    def reset(self):
        self._pbar.start = time.time()
        self._pbar.count = 0
        self._pbar.refresh()

    @property
    def value(self):
        return self._pbar.count
