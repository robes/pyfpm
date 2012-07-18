try:
    import unittest2 as unittest
except ImportError:
    import unittest

from pyfpm import caseclass

class AbstractTests(object):
    def test_full_arglist(self):
        case = self.MyCase(1, 2, 3)
        self.assertEquals(case._case_args, (1, 2, 3))

    def test_extra_args(self):
        case = self.MyCase(1, 2, 3, 4, 5)
        self.assertEquals(case._case_args, (1, 2, 3, 4, 5))

class CaseMetaclass(unittest.TestCase, AbstractTests):
    def setUp(self):
        class MyCase(Exception):
            __metaclass__ = caseclass.case_metacls
        self.MyCase = MyCase

    def test_fail_define_kwargs(self):
        try:
            class MyOtherCase(object):
                __metaclass__ = caseclass.case_metacls
                def __init__(self, **kwargs): pass
            self.fail("can't define __init__ with kwargs")
        except AttributeError:
            pass

class ExtendCaseClass(unittest.TestCase, AbstractTests):
    def setUp(self):
        class MyCase(caseclass.Case):
            def __init__(self, a, b, c=3, *args):
                pass
        self.MyCase = MyCase

    def test_fail_define_kwargs(self):
        try:
            class MyOtherCase(caseclass.Case):
                def __init__(self, **kwargs): pass
            self.fail("can't define __init__ with kwargs")
        except AttributeError:
            pass

    # test additional goodies for Python initializers

    def test_default_args(self):
        case = self.MyCase(1, 2)
        self.assertEquals(case._case_args, (1, 2, 3))

    def test_use_kwargs(self):
        case = self.MyCase(1, c=3, b=2)
        self.assertEquals(case._case_args, (1, 2, 3))