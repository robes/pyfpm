from __future__ import print_function
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from pyfpm.matcher import DynamicMatcher, NoMatch, StaticMatcher, statichandler
from pyfpm.pattern import build as _

class TestDynamicMatcher(unittest.TestCase):
    def test_equality(self):
        m1 = DynamicMatcher()
        m2 = DynamicMatcher()
        self.assertEquals(m1, m2)
        f = lambda: None
        m2.register(_(), f)
        self.assertNotEquals(m1, m2)
        m1.register(_(), f)
        self.assertEquals(m1, m2)

    def test_decorator(self):
        m1 = DynamicMatcher()
        m2 = DynamicMatcher()
        f = lambda: None
        m1.register(_(), f)
        decf = m2.handler(_())(f)
        self.assertEquals(decf, f)
        self.assertEquals(m1, m2)

    def test_emptymatcher(self):
        matcher = DynamicMatcher()
        try:
            matcher.match(None)
            self.fail('should fail with NoMatch')
        except NoMatch:
            pass

    def test_simplematch(self):
        m = DynamicMatcher()
        m.register(_(), lambda: 'test')
        self.assertEquals(m(None), 'test')

    def test_varbind(self):
        m = DynamicMatcher()
        m.register(_()%'x', lambda x: 'x=%s' % x)
        self.assertEquals(m(None), 'x=None')
        self.assertEquals(m(1), 'x=1')

    def test_handler_priority(self):
        m = DynamicMatcher()
        m.register(_(1), lambda: 'my precious, the one')
        m.register(_(int), lambda: 'just an int')
        m.register(_(), lambda: 'just an object? whatever')
        m.register(_(str), lambda: 'i wish i could find a string')
        self.assertNotEquals(m('hi'), 'i wish i could find a string')
        self.assertEquals(m(None), 'just an object? whatever')
        self.assertEquals(m(3), 'just an int')
        self.assertEquals(m(1), 'my precious, the one')

class TestStaticMatcher(unittest.TestCase):
    def test_simplematch(self):
        class m(StaticMatcher): pass
        try:
            m(None)
            self.fail('should fail with NoMatch')
        except NoMatch:
            pass

    def test_varbind(self):
        class m(StaticMatcher):
            @statichandler(_()%'x')
            def any(x):
                return 'x=%s' % x
        self.assertEquals(m(None), m.match(None))
        self.assertEquals(m(None), 'x=None')
        self.assertEquals(m(1), 'x=1')

    def test_handler_priority(self):
        class m(StaticMatcher):
            @statichandler(_(1))
            def one(): return 'my precious, the one'
            @statichandler(_(int))
            def int(): return 'just an int'
            @statichandler(_())
            def any(): return 'just an object? whatever'
            @statichandler(_(str))
            def str(): return 'i wish i could find a string'
        self.assertNotEquals(m('hi'), 'i wish i could find a string')
        self.assertEquals(m(None), 'just an object? whatever')
        self.assertEquals(m(3), 'just an int')
        self.assertEquals(m(1), 'my precious, the one')