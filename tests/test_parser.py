import re
import unittest

from pyfpm import parser
from pyfpm.pattern import build as _

_has_named_tuple = False
try:
    from collections import namedtuple
    _has_named_tuple = True
    Case3 = namedtuple('Case3', 'a b c')
    Case0 = namedtuple('Case0', '')
except ImportError:
    pass

class TestParser(unittest.TestCase):
    def setUp(self):
        self.parse = parser.Parser()

    def test_automatic_context(self):
        self.assertEquals(self.parse.context, globals())

    def test_manual_context(self):
        obj = 'my local string'
        p = parser.Parser({'x': obj})
        self.assertEquals(p.context['x'], obj)

    def test_anon_var(self):
        pattern = self.parse('_')
        self.assertEquals(pattern, _())

    def test_named_var(self):
        pattern = self.parse('x')
        self.assertEquals(pattern, _()%'x')

    def test_type_annotation_space_irrelevance(self):
        self.assertEquals(self.parse('_:str'), self.parse('_ : str'))

    def test_typed_anon_var(self):
        pattern = self.parse('_:str')
        self.assertEquals(pattern, _(str))

    def test_typed_named_var(self):
        pattern = self.parse('x:str')
        self.assertEquals(pattern, _(str)%'x')

    def test_nested_type_var(self):
        pattern = self.parse('x:unittest.TestCase')
        self.assertEquals(pattern, _(unittest.TestCase)%'x')

    def test_named_var_clash(self):
        for expr in ('str', 'object:str'):
            try:
                self.parse(expr)
                self.fail()
            except parser.ParseException:
                pass

    def test_fail_with_unknown_type(self):
        try:
            self.parse('_:fdsa')
            self.fail('fdsa is undefined')
        except parser.ParseException:
            pass

    def test_fail_with_known_nontype(self):
        try:
            self.parse('_:unittest')
            self.fail('unittest is not a type')
        except parser.ParseException:
            pass

    def test_int_constant(self):
        self.assertTrue(self.parse('1'), _(1))
        self.assertTrue(self.parse('-1'), _(-1))
        try:
            self.parse('- 1')
            self.fail('bad integer')
        except parser.ParseException:
            pass

    def test_float_constant(self):
        self.assertEquals(self.parse('1.'), _(1.))
        self.assertEquals(self.parse('.5'), _(.5))
        self.assertEquals(self.parse('1.5'), _(1.5))
        self.assertEquals(self.parse('-1.'), _(-1.))
        self.assertEquals(self.parse('-.5'), _(-.5))
        self.assertEquals(self.parse('-1.5'), _(-1.5))
        try:
            self.parse('1 . 0')
            self.fail('bad float')
        except parser.ParseException:
            pass

    def test_str_constant(self):
        self.assertEquals(self.parse('"abc"'), _('abc'))
        self.assertEquals(self.parse("'abc'"), _('abc'))

    def test_regex_constant(self):
        self.assertEquals(self.parse('/abc/'), _(re.compile('abc')))
        self.assertEquals(self.parse(r'/\//'), _(re.compile('/')))
        self.assertEquals(self.parse(r'/\\/'), _(re.compile(r'\\')))

    def test_head_tail(self):
        self.assertEquals(self.parse('head :: tail'), _()%'head' + _()%'tail')
        self.assertEquals(self.parse('head :: []'), _()%'head' + _([]))
        self.assertEquals(self.parse('a :: b :: c'),
                _()%'a' + _()%'b' + _()%'c')
        self.assertEquals(self.parse('a :: b :: c :: d'),
                _()%'a' + _()%'b' + _()%'c' + _()%'d')

    def test_explicit_list(self):
        self.assertEquals(self.parse('[]'), _([]))
        self.assertEquals(self.parse('[x:int]'), _([_(int)%'x']))
        self.assertEquals(self.parse('[_, x:int]'), _(_(), _(int)%'x'))
        self.assertEquals(self.parse('[_, []]'), _(_(), _([])))
        self.assertEquals(self.parse('[[]]'), _([_([])]))
        self.assertEquals(self.parse('[[], _]'), _([_([]), _()]))

    def test_or(self):
        self.assertEquals(self.parse('x | y'), _()%'x' | _()%'y')

    def test_nested_or(self):
        self.assertEquals(self.parse('[x | y]'), _([_()%'x' | _()%'y']))
        self.assertEquals(self.parse('[(x | y)]'), _([_()%'x' | _()%'y']))

    if _has_named_tuple:
        def test_case_classes(self):
            self.assertEquals(self.parse('Case3(1, 2, 3)'), _(Case3(1, 2, 3)))
            self.assertEquals(self.parse('Case0()'), _(Case0()))

    def test_conditional_pattern(self):
        p = self.parse('_ if False')
        self.assertFalse(p << 1)
        
        p = self.parse('x:int if x > 1')
        self.assertFalse(p << 1)
        self.assertTrue(p << 2)

        p = self.parse('x if x==unittest')
        self.assertFalse(p << parser)
        self.assertTrue(p << unittest)

        p = self.parse('x if y==1')
        try:
            p << 1
            self.fail()
        except NameError:
            pass

        try:
            self.parse('x if TY*(*&^')
            self.fail()
        except SyntaxError:
            pass

    def test_conditional_pattern_equality(self):
        self.assertEquals(self.parse('x if x'), self.parse('x if x'))
        self.assertNotEquals(self.parse('x if not x'), self.parse('x if x'))
        self.assertTrue(str(self.parse('x if x').condition).startswith(
            '_IfCondition(code='))
