import re

class Match(object):
    def __init__(self, ctx=None):
        if ctx is None:
            ctx = {}
        self.ctx = ctx
    def __eq__(self, other):
        return isinstance(other, Match) and other.ctx == self.ctx
    def __repr__(self):
        return 'Match(%s)' % self.ctx

class Pattern(object):
    def __init__(self):
        self.bound_name = None

    def match(self, other, ctx=None):
        if self._does_match(other):
            if self.bound_name:
                if ctx is None:
                    ctx = {}
                try:
                    previous = ctx[self.bound_name]
                    if previous != other:
                        return None
                except KeyError:
                    ctx[self.bound_name] = other
            return Match(ctx)
        return None
    def __lshift__(self, other):
        return self.match(other)

    def bind(self, name):
        self.bound_name = name
        return self
    def __mod__(self, name):
        return self.bind(name)

    def length(self):
        return 1

    def set_length(self, length):
        return RangePattern(self, length)
    def __mul__(self, length):
        return self.set_length(length)
    def __rmul__(self, length):
        return self.set_length(length)

    def set_infinite(self):
        return self.set_length(RangePattern.INFINITE)
    def __pos__(self):
        return self.set_infinite()

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.__dict__ == other.__dict__)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                ', '.join('='.join(map(str, (k, v))) for (k, v) in
                    self.__dict__.items() if v))

class AnyPattern(Pattern):
    def _does_match(self, other):
        return True

class EqualsPattern(Pattern):
    def __init__(self, obj):
        super(EqualsPattern, self).__init__()
        self.obj = obj

    def _does_match(self, other):
        return self.obj == other

class InstanceOfPattern(Pattern):
    def __init__(self, cls):
        super(InstanceOfPattern, self).__init__()
        self.cls = cls

    def _does_match(self, other):
        return isinstance(other, self.cls)

class RegexPattern(Pattern):
    def __init__(self, regex):
        super(RegexPattern, self).__init__()
        if not isinstance(regex, re.RegexObject):
            regex = re.compile(regex)
        self.regex = regex
    # TODO: finish this, must improve Pattern._do_match

class RangePattern(Pattern):
    INFINITE = -1
    def __init__(self, pattern=AnyPattern(), length=None):
        super(RangePattern, self).__init__()
        self.pattern = pattern
        self._length = length

    def set_length(self, length):
        return RangePattern(self.pattern, length)

    def length(self):
        return self._length

    def _does_match(self, other):
        if self.pattern.bound_name:
            raise ValueError("inner pattern in a range can't be bound")
        l = self.length()
        if l is None:
            raise ValueError('range length unset')
        if l == 1:
            raise ValueError('range length must be higher than 1')
        if l != RangePattern.INFINITE and len(other) != l:
            return None
        for item in other:
            if not self.pattern._does_match(item):
                return None
        return True

class ListPattern(Pattern):
    def __init__(self, *patterns):
        super(ListPattern, self).__init__()
        self.patterns = patterns

    def match(self, other, ctx=None):
        remaining = other
        for pattern in self.patterns:
            l = pattern.length()
            if len(remaining) < l:
                return None
            if l == 1:
                match = pattern.match(remaining[0], ctx)
            elif l == RangePattern.INFINITE:
                match = pattern.match(remaining, ctx)
            else:
                match = pattern.match(remaining[:l], ctx)
            if not match:
                return None
            if ctx is None:
                ctx = match.ctx
            if l != RangePattern.INFINITE:
                remaining = remaining[l:]
            else:
                remaining = tuple()
        if len(remaining):
            return None
        return Match(ctx)

class CasePattern(Pattern):
    def __init__(self, casecls, *initpatterns):
        super(CasePattern, self).__init__()
        self.casecls_pattern = InstanceOfPattern(casecls)
        self.initargs_pattern = ListPattern(*initpatterns)

    def match(self, other, ctx=None):
        if not self.casecls_pattern.match(other, ctx):
            return None
        match = self.initargs_pattern.match(other._case_args, ctx)
        if match and self.bound_name:
            match.ctx[self.bound_name] = other
        return match

def build(*args):
    arglen = len(args)
    if arglen > 1:
        return ListPattern(*map(build, args))
    if arglen == 0:
        return AnyPattern()
    (arg,) = args
    if isinstance(arg, Pattern):
        return arg
    if hasattr(arg, '_case_args'):
        return CasePattern(arg.__class__,
                *map(build, arg._case_args))
    if isinstance(arg, type):
        return InstanceOfPattern(arg)
    if isinstance(arg, (tuple, list)):
        if len(arg) == 0:
            return RangePattern(length=0)
        return build(*arg)
    return EqualsPattern(arg)