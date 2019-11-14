from unittest import TestCase

from deprecated import deprecated

from .tracker import (FinishConditionException, PBarOutOfBound, Trackable,
                      Tracker, reset_all)


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

    @deprecated
    def test_legacy_basic(self):
        tracker = Tracker()
        tracker.add_track('epoch')
        tracker.add_track('step', 10)
        self.assertEqual(tracker.epoch, 0)
        self.assertEqual(tracker.step, 10)

    @deprecated
    def test_legacy_update_and_now(self):
        tracker = Tracker()
        tracker.add_track('epoch')
        tracker.add_track('step', 10)
        tracker.add_update_fn('epoch', 'add')
        for epoch in range(10):
            tracker.legacy_update()
            self.assertEqual(tracker.epoch, epoch + 1)
            self.assertEqual(tracker.step, 10)
        self.assertTupleEqual(tracker.now_as_tuple, (('epoch', 10), ('step', 10)))
        self.assertEqual(tracker.now, 'epoch_10-step_10')

    @deprecated
    def test_legacy_update_with_args(self):
        tracker = Tracker()
        tracker.add_track('epoch')
        tracker.add_track('step')
        tracker.add_update_fn('epoch', 'add')
        tracker.add_update_fn('step', 'add')
        for step in range(1, 101):
            if step % 10 == 0:
                tracker.legacy_update('epoch')
            tracker.legacy_update('step')

            self.assertEqual(tracker.step, step)
            self.assertEqual(tracker.epoch, step // 10)

    @deprecated
    def test_legacy_update_addx(self):
        tracker = Tracker()
        tracker.add_track('n_sentences')
        tracker.add_update_fn('n_sentences', 'addx')
        tracker.legacy_update('n_sentences', 5)
        self.assertEqual(tracker.n_sentences, 5)

    @deprecated
    def test_legacy_when_to_finish(self):
        tracker = Tracker()
        tracker.add_track('epoch')
        tracker.add_update_fn('epoch', 'add')
        with self.assertRaises(FinishConditionException):
            tracker.is_finished
        tracker.finish_when('epoch', 10)
        while not tracker.is_finished:
            tracker.legacy_update()
        self.assertEqual(tracker.epoch, 10)

    @deprecated
    def test_legacy_add_track_with_extra_args(self):
        tracker = Tracker()
        tracker.add_track('epoch', update_fn='add', finish_when=10)
        while not tracker.is_finished:
            tracker.legacy_update()
        self.assertEqual(tracker.epoch, 10)

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
