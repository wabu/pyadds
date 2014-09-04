from collections import OrderedDict
import types

__all__ = ['Case']

class CaseDict(OrderedDict):
    def __getitem__(self, name):
        if name not in self and not name.startswith('_'):
            self[name] = ...
        return super().__getitem__(name)


class Case(type):
    """ 
    Case-class meta type

    The Case meta class helps you to define data contains with default values easily:
    >>> class Foo:
    ...     bar
    ...     baz = 42
    >>> Foo(bar=23)
        Foo(bar=23, baz=42)
    >>> Foo(13,37)
        Foo(bar=13, baz=37)
    >>> bar,baz = Foo(23)
    """
    @classmethod
    def __prepare__(metacls, name, bases):
        return CaseDict()

    def __new__(cls, name, bases, attrs):
        names = tuple(name for name,val in attrs.items()
                if not isinstance(val, types.FunctionType) and not name.startswith('_'))
        fields = {name: attrs.pop(name) for name in names}
    
        attrs = dict(attrs)
        attrs['fields'] = names

        class CaseBase:
            def __init__(self, *args, **kws):
                for i, name in enumerate(names):
                    if i < len(args):
                        val = args[i]
                    elif name in kws:
                        val = kws.pop(name)
                    elif fields[name] != ...:
                        val = fields[name]
                    else:
                        raise TypeError('no value for field %s (%d) given' % (name, i))
                    setattr(self, name, val)

                super().__init__(*args[i+1:], **kws)

            def __iter__(self):
                return iter(getattr(self, name) for name in fields)

            def __repr__(self):
                return '{}({})'.format(type(self).__name__, ', '.join(
                        '{}={}'.format(name, getattr(self, name)) for name in type(self).fields))

            def __str__(self):
                return '{}({})'.format(type(self).__name__, 
                        ', '.join(str(getattr(self, name)) for name in type(self).fields))

        return super().__new__(cls, name, (CaseBase,) + bases, attrs)
