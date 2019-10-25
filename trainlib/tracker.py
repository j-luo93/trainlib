"""
A Tracker instance is responsible for:
1. tracking epochs, rounds, steps or anything that marks the stage that the training process is in.
2. tracking potentially some curriculum- or annealing-related hyperparameters.
3. tracking metrics.
4. displaying a progress bar.
"""

import warnings
from collections import UserDict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Union

from deprecated import deprecated

from trainlib.trackable import Trackable


@dataclass
class WhenToFinish:
    name: str
    value: Any


class FinishConditionException(Exception):
    pass


UpdateFn = Union[str, Callable[[], None]]


class Tracker:

    def __init__(self):
        self._legacy_attrs = dict()
        self._legacy_update_fns = dict()
        self._legacy_when_to_finish = None

        self._trackables: Dict[name, Trackable] = dict()

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
        trackable = Trackable(name, total=total)
        self._trackables[name] = trackable
        return trackable

    def __getattribute__(self, attr: str):
        try:
            return super().__getattribute__(attr)
        except AttributeError as e:
            if attr in self._attrs:
                return self._attrs[attr]
            else:
                raise

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
            self._trackables[name].update()

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
