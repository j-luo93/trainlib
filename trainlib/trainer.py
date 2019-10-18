from abc import ABC, abstractmethod

from .tracker import Tracker
from .metrics import Metrics


class Trainer(ABC):
    """A base Trainer class that defines the basic workflow of a trainer."""

    def __init__(self):
        self.tracker = Tracker()

    @abstractmethod
    def check_metrics(self, accum_metrics: Metrics):
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def train_loop(self, *args, **kwargs) -> Metrics:
        pass

    def train(self, *args, **kwargs):
        accum_metrics = Metrics()
        while not self.tracker.is_finished:
            metrics = self.train_loop(*args, **kwargs)
            accum_metrics += metrics
            self.tracker.update()

            self.check_metrics()
            self.save()
