from functools import wraps
import inspect

from .annotate import Annotate, ObjDescr, Cache, Set


class Observable:
    """ Observable mixing so others can subscribe to an object """

    def __init__(self, *args, **kws):
        super().__init__(*args, **kws)
        self.observers = []

    def notify(self, event):
        for obs in self.observers:
            obs.notify(event)

    def subscribe(self, observer):
        self.observers.append(observer)

    def unsubscribe(self, observer):
        self.observers.remove(observer)


def emitting(f):
    """ emit event on method call """
    spec = inspect.getfullargspec(f)

    @wraps(f)
    def emit(self, *args, **kws):
        result = f(self, *args, **kws)
        event = Event(f, spec, result, self, args, kws)
        self.notify(event)
        return result

    emit.__event__ = f.__name__
    return emit


class Event:
    def __init__(self, f, spec, result, obj, args, kws):
        self.f = f
        self.spec = spec
        self.obj = obj
        self.args = args
        self.kws = kws
        self.result = result

    @property
    def __name__(self):
        return self.f.__name__

    def __getattr__(self, name):
        spec = self.spec
        args = self.args + (spec.defaults or ())

        # TODO varargs, varkw
        for dct in [self.kws,
                    # don't bind self arg
                    dict(zip(spec.args[1:], args)),
                    spec.kwonlydefaults or {}]:
            try:
                return dct[name]
            except KeyError:
                pass
        else:
            raise AttributeError('%r object has no attribute %r' % (type(self), name))

    def __str__(self):
        return '{}-event' % self.__name__

    def __repr__(self):
        # don't bind self arg
        args = self.spec.args[1:] + self.spec.kwonlyargs
        # TODO varargs, varkw
        return '{}({})->{!r}'.format(self.__name__, ', '.join('{}={!r}'.format(name, getattr(self, name))
                                                              for name in args), self.result)


class observes(Annotate, ObjDescr, Cache, Set):
    """
    annotation for an observable that an observer watches

    Example:
    ========
    >>> class Model(Observable):
    ...     @emitting
    ...     def foo(self, num, suf='bar'):
    ...         return str(num)+suf
    ...
    ...     def __str__(self):
    ...         return 'foo-model'
    ...
    ... class View:
    ...     def __init__(self, model):
    ...         self.model = model
    ...
    ...     @observes
    ...     def model(self, model : Model):
    ...         print("we are watching {}".format(model))
    ...
    ...     @model.foo
    ...     def on_foo(self, event):
    ...         print("{} emitting {!r}".format(self.model, event))
    ...
    ... m = Model()
    ... v = View(m)
    ... m.foo(42)
        we are watching foo-model
        foo-model emitting foo(num=42, suf='bar')->'42bar'
    """

    def __init__(self, definition):
        super().__init__(definition)
        try:
            self.typ, = definition.__annotations__.values()
        except ValueError:
            raise ValueError('@observes defintion should contain a type annotation')
        self.subscriptions = {}

    def __set__(self, obj, obs):
        super().__set__(obj, obs)
        self.definition(obj, obs)
        if self.subscriptions:
            class SubsCaller:
                @classmethod
                def notify(call, event):
                    subs = self.subscriptions.get(event.__name__)
                    if subs:
                        subs(obj, event)

            obs.subscribe(SubsCaller())

    def __getattr__(self, name):
        event = getattr(self.typ, name)
        if not hasattr(event, '__event__'):
            raise ValueError('%r is not an observable event of the model')

        def subscribe(f):
            self.subscriptions[name] = f
            return f

        return subscribe

