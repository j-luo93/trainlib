from unittest import TestCase

from .trackable import Trackable, reset_manager, PBarOutOfBound


class ClassName(TestCase):

    def setUp(self):
        reset_manager()

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
