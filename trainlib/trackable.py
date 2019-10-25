"""
A Trackable instance is, trackable. Used by a Tracker instance.
A Trackable instance is associated with a progress bar.
"""

import enlighten


def reset_manager():
    Trackable.reset_manager()


class PBarOutOfBound(Exception):
    pass


class Trackable:

    _manager = enlighten.get_manager()
    _instances = dict()

    @classmethod
    def reset_manager(cls):
        cls._manager = enlighten.get_manager()
        cls._instances.clear()

    def __init__(self, name: str, total: int = None):
        if name in self._instances:
            raise ValueError(f'A trackable named "{name}" already exists.')

        self._name = name
        self._total = total
        self._pbar = self._manager.counter(desc=name, total=total)
        self._instances[name] = self

    def update(self):
        self._pbar.update()
        if self._total is not None and self._pbar.count > self._total:
            raise PBarOutOfBound(f'Progress bar ran out of bound.')

    @property
    def value(self):
        return self._pbar.count
