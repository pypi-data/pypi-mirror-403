import time
import unittest


class OnChangeSinceTests(unittest.TestCase):
    def test_component_on_change_ignores_old_events(self):
        from simo_sdk.models import Component

        comp = Component(_simo=None, id=1, name='x')
        called = []

        def cb(_c):
            called.append(True)

        comp.on_change(cb, fields=['value'])
        since = comp._on_change_since
        self.assertIsNotNone(since)

        comp._emit_change({'value'}, actor=None, event_ts=float(since) - 1.0)
        self.assertEqual(called, [])

        comp._emit_change({'value'}, actor=None, event_ts=float(since) + 0.01)
        self.assertEqual(called, [True])

    def test_user_on_change_ignores_old_events(self):
        from simo_sdk.models import User

        u = User(_simo=None, id=1)
        called = []

        def cb(_u):
            called.append(True)

        u.on_change(cb, fields=['at_home'])
        since = u._on_change_since
        self.assertIsNotNone(since)

        u._emit_change({'at_home'}, event_ts=float(since) - 1.0)
        self.assertEqual(called, [])

        u._emit_change({'at_home'}, event_ts=float(since) + 0.01)
        self.assertEqual(called, [True])


if __name__ == '__main__':
    unittest.main()

