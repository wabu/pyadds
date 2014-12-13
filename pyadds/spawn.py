from .annotate import cached
from .logging import log

import asyncio
import multiprocessing as mp

__spawner__ = None


def get_spawner(method=None):
    global __spawner__
    if __spawner__ is None:
        __spawner__ = Spawner(method=method or 'spawn')

    if method and __spawner__.method != method:
        raise ValueError('Conflicting spawner method with previous spawner')

    return __spawner__


def caller(obj, name, args=(), kws={}):
    return getattr(obj, name)(*args, **kws)


@log
class Spawner:
    def __init__(self, method='spawn'):
        self.method = method
        self.setups = []

    @cached
    def mp(self):
        return mp.get_context(self.method)

    def add_setup(self, setup):
        """ add a setup routine """
        self.setups.append(setup)

    def remove_setup(self, setup):
        """ remove a setup routine """
        self.setups.remove(setup)

    def _setup(self):
        for setup in self.setups:
            setup()

    def _entry(self, obj, name, args, kws):
        self._setup()
        res = caller(obj, name, args, kws)
        self.__log.info('%s done, returned %s', name, res)

    def _coentry(self, obj, name, args, kws):
        self._setup()
        coro = getattr(obj, name)
        main = asyncio.async(coro(*args, **kws))
        asyncio.get_event_loop().run_forever()
        if main.done():
            self.__log.info('%s done, returned %s', name, main.result())
        else:
            self.__log.info('%s canceld, asyncio loop was closed', name)

    def _do_spawn(self, entry, method, args, kws, __name__=None):
        """ calls a method inside a newly create process, returning the pid """
        obj = method.__self__
        name = method.__name__

        proc = self.mp.Process(target=caller,
                               args=(self, entry, (obj, name, args, kws)),
                               name=__name__)
        proc.start()
        return proc

    def spawn(self, method, *args, __name__=None, **kws):
        """ spawn a process and call a method inside it """
        return self._do_spawn('_entry', method, args, kws, __name__=__name__)

    @asyncio.coroutine
    def cospawn(self, coro, *args, __name__=None, **kws):
        """ spawn a process and call a coroutine inside it """
        return self._do_spawn('_coentry', coro, args, kws, __name__=__name__)
