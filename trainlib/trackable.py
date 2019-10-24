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

    @classmethod
    def reset_manager(cls):
        cls._manager = enlighten.get_manager()

    def __init__(self, name: str, total: int = None):
        self._name = name
        self._total = total
        self._pbar = self._manager.counter(desc=name, total=total)

    def update(self):
        self._pbar.update()
        if self._total is not None and self._pbar.count > self._total:
            raise PBarOutOfBound(f'Progress bar ran out of bound.')

    @property
    def value(self):
        return self._pbar.count
