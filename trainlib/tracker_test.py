from unittest import TestCase

from .tracker import Tracker, reset_tracker


class TestTracker(TestCase):

    def setUp(self):
        reset_tracker()

    def test_basic(self):
        tracker = Tracker()
        tracker.add_track('epoch')
        tracker.add_track('step', 10)
        self.assertEqual(tracker.epoch, 0)
        self.assertEqual(tracker.step, 10)

    def test_update_and_now(self):
        tracker = Tracker()
        tracker.add_track('epoch')
        tracker.add_track('step', 10)
        tracker.add_update_fn('epoch', 'add')
        for epoch in range(10):
            tracker.update()
            self.assertEqual(tracker.epoch, epoch + 1)
            self.assertEqual(tracker.step, 10)
        self.assertTupleEqual(tracker.now_as_tuple, (('epoch', 10), ('step', 10)))
        self.assertEqual(tracker.now, 'epoch_10-step_10')

    def test_update_with_args(self):
        tracker = Tracker()
        tracker.add_track('epoch')
        tracker.add_track('step')
        tracker.add_update_fn('epoch', 'add')
        tracker.add_update_fn('step', 'add')
        for step in range(1, 101):
            if step % 10 == 0:
                tracker.update('epoch')
            tracker.update('step')

            self.assertEqual(tracker.step, step)
            self.assertEqual(tracker.epoch, step // 10)

    def test_update_addx(self):
        tracker = Tracker()
        tracker.add_track('n_sentences')
        tracker.add_update_fn('n_sentences', 'addx')
        tracker.update('n_sentences', 5)
        self.assertEqual(tracker.n_sentences, 5)
