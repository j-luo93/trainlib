from collections import Counter
from unittest import TestCase

from .tracker import PBarOutOfBound, Task, Trackable, Tracker, reset_all


class TestTrackable(TestCase):

    def setUp(self):
        reset_all()

    def test_update(self):
        x = Trackable('step', total=10)
        for i in range(10):
            x.update()
            self.assertEqual(x.value, i + 1)

        with self.assertRaises(PBarOutOfBound):
            x.update()

    def test_update_without_total(self):
        x = Trackable('step')
        for i in range(100):
            x.update()
            self.assertEqual(x.value, i + 1)

    def test_nested(self):
        x = Trackable('epoch', total=10)
        y = x.add_trackable('step', total=10)
        for i in range(10):
            for j in range(10):
                y.update()
                self.assertEqual(y.value, j + 1)
            x.update()
            self.assertEqual(x.value, i + 1)


class TestTracker(TestCase):

    def setUp(self):
        reset_all()

    def test_basic(self):
        tracker = Tracker()
        tracker.add_trackable('epoch', total=10)
        for i in range(10):
            tracker.update('epoch')
            self.assertEqual(tracker.epoch, i + 1)

    def test_nested(self):
        tracker = Tracker()
        epoch = tracker.add_trackable('epoch', total=10)
        step = epoch.add_trackable('step', total=10)
        for i in range(10):
            for j in range(10):
                tracker.update('step')
                self.assertEqual(tracker.step, j + 1)
            tracker.update('epoch')
            self.assertEqual(tracker.epoch, i + 1)

    def test_tasks(self):
        tracker = Tracker()
        tracker.add_trackable('step', total=1000)
        task1 = Task()
        task2 = Task()
        tracker.add_tasks([task1, task2], [1.0, 0.5])
        cnt = Counter()
        for _ in range(1000):
            task = tracker.draw_task()
            cnt[task] += 1
            tracker.update('step')
        self.assertTrue(abs(2 - cnt[task1] / cnt[task2]) < 0.5)
