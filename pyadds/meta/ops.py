from functools import wraps
from collections import namedtuple

import operator
import builtins


def get_op(name):
    name = name.strip('_')
    op = (getattr(builtins, name, None) or
          getattr(operator, name, None) or
          getattr(operator, '__{}__'.format(name), None))
    if op is None:
        raise AttributeError("can't reslove operator {}".format(name))
    return op


class Op(namedtuple('Op', 'name op reflect n kind format')):
    def __new__(cls, name, n, format, kind='unknown', reflect=False):
        op = get_op(name)
        if reflect:
            reflect = Reflect(name, n, format, kind, reflect=False)
        else:
            reflect = None
        return super().__new__(cls, name, op, reflect, n, kind, format)

    @property
    def method(self):
        return '__{}__'.format(self.name)

    @property
    def defines(self):
        return self.method

    def __call__(self, *args):
        return self.op(*args)

    def on(self, item):
        return getattr(item, self.op)

    def __str__(self):
        return self.format.replace(' ', '').format(*['_']*self.n)

    def __repr__(self):
        return self.format.format(*map('@{}'.format, range(self.n)))


class Reflect(Op):
    @property
    def defines(self):
        return '__r{}__'.format(self.name)

    def __call__(self, a, b):
        return self.op(b, a)

    def __repr__(self):
        return self.format.format(*map('@{}'.format, reversed(range(self.n))))


class Ops(namedtuple('Ops', 'kind ops reflect')):
    def __new__(cls, kind, ops, reflect=False):
        ops = tuple(Op(*args, kind=kind, reflect=reflect)
                    for args in ops)
        return super().__new__(cls, kind, ops, reflect)

    def __str__(self):
        return '{}-ops'.format(self.kind)

    def __repr__(self):
        return '{}-ops: {}'.format(self.kind, ', '.join(map(str, self.ops)))


class _Operators:
    def __init__(self, name, *defines):
        self.name = name
        self.defines = defines
        self.flat = [op for ops in self.defines for op in ops.ops]
        self.by_name = {op.name: op for op in self}
        self.by_kind = {ops.kind: ops for ops in self.defines}

    def __iter__(self):
        return iter(self.flat)

    def __getitem__(self, name):
        return self.by_name[name.strip('__')]

    def __getattr__(self, kind):
        return type(self)('{}.{}'.format(self.name, kind), self.by_kind[kind])

    def __str__(self):
        return '{}.{}'.format(__name__, self.name)

    def __repr__(self):
        return '{} ({})'.format(self, ', '.join(map(str, self.defines)))


operators = _Operators(
    'operators',
    Ops('compare', (('lt', 2, '{} < {}'),
                    ('le', 2, '{} <= {}'),
                    ('eq', 2, '{} == {}'),
                    ('ge', 2, '{} >= {}'),
                    ('gt', 2, '{} > {}'))),
    Ops('object', (('hash', 1, 'hash({})'),
                   ('bool', 1, 'bool({})'))),
    Ops('container', (('len',         1, 'len({})'),
                      ('length_hint', 1, 'length_hint({})'),
                      ('getitem',     2, '{}[{}]'),
                      ('setitem',     3, '{}[{}] = {}'),
                      ('delitem',     2, 'del {}[{}]'),
                      ('iter',        1, 'iter({})'),
                      ('reversed',    1, 'reversed({})'),
                      ('contains',    2, '{1} in {0}'))),
    Ops('numeric', (('add',      2, '{} + {}'),
                    ('sub',      2, '{} - {}'),
                    ('mul',      2, '{} * {}'),
                    ('truediv',  2, '{} / {}'),
                    ('floordiv', 2, '{} // {}'),
                    ('mod',      2, '{} % {}'),
                    ('divmod',   2, 'divmod({}, {})'),
                    ('pow',      2, '{} ** {}'),
                    ('lshift',   2, '{} << {}'),
                    ('rshift',   2, '{} >> {}'),
                    ('and',      2, '{} & {}'),
                    ('xor',      2, '{} ^ {}'),
                    ('or',       2, '{} | {}')), True),
    Ops('unary', (('neg',    1, '-{}'),
                  ('pos',    1, '+{}'),
                  ('abs',    1, 'abs({})'),
                  ('invert', 1, '~{}'))),
    Ops('conversion', (('complex', 1, 'complex({})'),
                       ('int',     1, 'int({})'),
                       ('float',   1, 'float({})'),
                       ('round',   1, 'round({})'))),
    Ops('indexing', (('index', 1, 'index({})'),)),
)


def iter_ops(cls, reflect=True):
    """
    iterator over all operators of a class
    """
    for op in operators:
        if hasattr(cls, op.defines):
            yield op
        if op.reflect:
            ref = op.reflect
            if (reflect and hasattr(cls, op.defines)
                    or hasattr(cls, ref.defines)):
                yield ref


def opsame(op):
    """ checks for type mismatch between first and second argument"""
    @wraps(op)
    def checked(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return op(self, other)
    return checked


def operate(by=None, reflect=True):
    """
    define a class with operators that access an attribute to work on
    """
    if isinstance(by, type):
        return autowraped_ops(by)
    else:
        def annotate(cls):
            return autowraped_ops(cls, by=by, reflect=reflect)
        return annotate


def autowraped_ops(cls, by=None, reflect=True):
    """
    Creates a dynamic mixin with operator forwarding to wraped instances

    Parameters
    ----------
    cls : type
        class that the object
    by : str
        instance attribute that is used to constructed wrapped objects
    reflect : bool
        also create reflected operator wrappings

    Return
    ------
    mixin : type
        dynamic mixin class with operator definitions
    """
    def wrapping(op):
        call = op.__call__
        if by:
            def wrap(self, *args):
                return call(getattr(self, by), *args)
        else:
            def wrap(self, *args):
                return call(cls(self), *args)
        return wraps(getattr(cls, op.method))(wrap)

    ops = {op.defines: wrapping(op)
           for op in iter_ops(cls, reflect=reflect)
           if op.name not in ['hash', 'eq']}
    ops.update({'__def__': cls})
    return type('Fwd' + cls.__name__, (object,), ops)


def bind(cls):
    def annotate(f):
        f.__bind__ = cls
        return f
    return annotate
