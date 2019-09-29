"""
A Tracker instance is responsible for:
1. tracking epochs, rounds, steps or anything that marks the stage that the training process is in.
2. tracking potentially some curriculum- or annealing-related hyperparameters.
3. tracking metrics.
4. displaying a progress bar.
"""

from collections import UserDict
from typing import Any, Callable, Dict, Iterable, List, Union


def reset_tracker():
    tracker = Tracker()
    tracker.reset_tracker()


class Tracker:

    _shared_state = dict()
    _attrs_to_track = set()
    _update_fns = dict()

    def __init__(self):
        # NOTE Make this basically a singleton.
        self.__dict__ = self._shared_state

    def add_track(self, name: str, init_value: Any = 0):
        if name in self._attrs_to_track:
            raise NameError(f'A track named "{name}" already exists.')

        self._attrs_to_track.add(name)
        self.__dict__[name] = init_value

    def add_update_fn(self, name_to_update: str, update_fn: Union[str, Callable[[], None]]):
        if name_to_update in self._update_fns:
            raise NameError(f'An update function for {name_to_update} already exists.')

        if isinstance(update_fn, str):
            if update_fn == 'add':
                update_fn = lambda: setattr(self, name_to_update, getattr(self, name_to_update) + 1)
            elif update_fn == 'addx':
                update_fn = lambda x: setattr(self, name_to_update, getattr(self, name_to_update) + x)
            else:
                raise NotImplementedError(f'Not recognized update function named "{update_fn}"')

        self._update_fns[name_to_update] = update_fn

    def update(self, names_to_update: Union[str, List[str]] = None, value: Any = None):
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

    def reset_tracker(self):
        self._shared_state.clear()
        # NOTE(j_luo) These are class variables.
        self._attrs_to_track.clear()
        self._update_fns.clear()

    @property
    def now_as_tuple(self):
        return tuple(sorted(self.__dict__.items()))

    @property
    def now(self):
        return '-'.join([f'{k}_{v}'for k, v in self.now_as_tuple])
