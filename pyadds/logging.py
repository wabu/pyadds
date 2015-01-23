import logging


class lazy(tuple):
    """
    >>> logger.debug('%s', lazy(lambda: 'complex stuff')
    complex stuff
    """
    def __new__(cls, lam):
        return super().__new__(cls, (lam,))

    def __str__(self):
        lam, = self
        return str(lam())

    def __repr__(self):
        lam, = self
        return repr(lam())


def log(cls):
    name = '.'.join((cls.__module__, cls.__name__))
    attr = '_%s__log' % cls.__qualname__

    logger = logging.getLogger(name)
    setattr(cls, attr, logger)
    setattr(cls, 'logger', logger)
    return cls
