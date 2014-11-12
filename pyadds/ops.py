from functools import wraps
import operator


def opsame(op):
    """ checks for type mismatch between first and second argument"""
    @wraps(op)
    def checked(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return op(self, other)
    return checked


def get_op(name):
    if '_' not in name:
        name = '__{}__'.format(name)
    return getattr(operator, name), name


def mkop_wraped(cls, name, by=None):
    """
    forward operator with first argument wraped inside cls instances

    Parameters
    ----------
    cls : type
        class to wrap create wrapping
    name : str
        name of the operator

    Return
    ------
    op : method
        forward operator implementation
    """
    op, name = get_op(name)

    @wraps(getattr(cls, name))
    def fwd_op(self, *args):
        wrapped = getattr(self, by) if by else cls(self)
        return op(wrapped, *args)
    return fwd_op


def mkop_reflect(cls, name, by=None):
    """
    reflected forward operator with second argument wraped inside cls instance

    Parameters
    ----------
    cls : type
        class to wrap create wrapping
    name : str
        name of the non-reflected operator

    Return
    ------
    op : method
        forward operator implementation
    """
    op, name = get_op(name)

    @wraps(getattr(cls, name))
    def reflect_op(self, other):
        wrapped = getattr(self, by) if by else cls(self)
        return op(other, wrapped)
    return reflect_op


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
    ops = {}
    special = set(dir(object))
    for name in dir(operator):
        if (name in special or
                not name.startswith('__') or not name.endswith('__')):
            continue
        rname = '__r{}__'.format(name.strip('_'))

        if hasattr(cls, name):
            ops[name] = mkop_wraped(cls, name, by=by)
            if reflect:
                ops[rname] = mkop_reflect(cls, name, by=by)

    return type('Fwd' + cls.__name__, (object,), ops)
