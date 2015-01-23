import logging


def log(cls):
    name = '.'.join((cls.__module__, cls.__name__))
    attr = '_%s__log' % cls.__qualname__

    logger = logging.getLogger(name)
    setattr(cls, attr, logger)
    setattr(cls, 'logger', logger)
    return cls
