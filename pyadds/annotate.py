from functools import wraps
import weakref

from asyncio import coroutine, gather


class Named:
    def __init__(self, *args, name, **kws):
        super().__init__(*args, **kws)
        self.name = name


class Annotate(Named):
    """ annotation that is transformed to a class """

    def __new__(cls, definition):
        return wraps(definition)(super().__new__(cls))

    def __init__(self, definition):
        super().__init__(name=definition.__name__)
        self.definition = definition


class Conotate(Annotate):
    """ annotation that is defined as a coroutine """
    def __init__(self, definition, *args, **kws):
        definition = coroutine(definition)
        super().__init__(definition, *args, **kws)


class Descr(Named):
    """ base for building descriptors """
    def lookup(self, obj):
        """ abstract method that returns the dict and key to access/store the value """
        raise NotImplementedError

    def has_entry(self, obj):
        """ check if descriptor is set on an object """
        dct, key = self.lookup(obj)
        return key in dct


class ObjDescr(Descr):
    """ decriptor mixin to putting values in objects dict """

    def __init__(self, name):
        super().__init__(name=name)
        self.entry = '_' + name

    def lookup(self, obj):
        return obj.__dict__, self.entry


class RefDescr(Descr):
    """ descriptor mixin based on weak reference from objects """

    def __init__(self, name):
        super().__init__(name=name)
        self.refs = weakref.WeakKeyDictionary()

    def lookup(self, obj):
        return self.refs, obj


class Get(Descr):
    """ get descriptor calling using provided lookup and falling back to __default__ """
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        dct, key = self.lookup(obj)
        try:
            return dct[key]
        except KeyError:
            return self.__default__(obj)

    def __default__(self, obj):
        """ provider for default value of descriptor, raising NameError by default """
        raise NameError("Descriptor %s of %s object has no value set" %
                        (self.name, type(obj).__name__))

    @classmethod
    def iter(desc, obj, bind=False):
        """
        iteratete over all fields of the object of this descriptors class
        """
        cls = type(obj)
        for name in dir(cls):
            attr = getattr(cls, name)
            if isinstance(attr, desc):
                if bind:
                    yield attr.__get__(obj)
                else:
                    yield attr


class Defaults(Annotate, Descr):
    """ descriptor evaluationing definition once """
    def __default__(self, obj):
        return self.definition(obj)


class Set(Descr):
    """ set/delete descriptor """
    def __init__(self, *args, **kws):
        super().__init__(*args, **kws)
        self._post = None

    def post(self, f):
        assert callable(f)
        self._post = f
        return self

    def __set__(self, obj, value):
        dct, key = self.lookup(obj)
        dct[key] = value
        if self._post:
            self._post(obj)

    def __delete__(self, obj):
        dct, key = self.lookup(obj)
        dct.pop(key, None)


class Cache(Set, Get):
    """
    get descriptor remembering the default value for further calls to get
    """
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        dct, key = self.lookup(obj)
        try:
            return dct[key]
        except KeyError:
            val = self.__default__(obj)
            self.__set__(obj, val)
            return val


class attr(Defaults, ObjDescr, Get, Set):
    """ attribute descriptor with additional features """
    pass


class delayed(Defaults, ObjDescr, Cache):
    """ evaluate once and stored in obj dict, so values get pickled """
    pass


class refers(Defaults, RefDescr, Cache):
    """ keep values around, but reevaluate after pickling """
    pass

cached = refers


class once(Defaults, RefDescr, Cache):
    def __set__(self, obj, value):
        if obj:
            dct, key = self.lookup(obj)
            if key in dct:
                raise AttributeError(
                    "Attribute {} of {} can only be set once"
                    .format(self.name, type(obj)))
            dct[key] = value
            return value
        else:
            return self


class initialized(Conotate, RefDescr, Cache):
    """
    call coroutine once at with `initialize` with supplied kwargs to get value
    """
    pass


@coroutine
def initialize(obj, **opts):
    """ call all `@initialized` descriptors to initialize values """
    calls = []
    for desc in initialized.iter(obj):
        if desc.has_entry(obj):
            @coroutine
            def init():
                val = yield from desc.definition(obj, **opts)
                desc.__set__(obj, val)
                return desc.name, val

    return dict((yield from gather(*calls)))

