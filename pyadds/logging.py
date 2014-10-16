import logging
import types

def get_logger(name, **extra):
    logger = logging.getLogger(name)
    if extra:
        logger = logging.LoggerAdapter(logger, extra=extra)
    return logger


def log(cls=None, **extra):
    def annotate(cls):
        name = '.'.join((cls.__module__, cls.__name__))
        attr = '_%s__log' % cls.__qualname__

        logger = get_logger(name, **extra)
        setattr(cls, attr, logger)
        setattr(cls, 'logger', logger)
        return cls

    if cls is not None:
        if not isinstance(cls, type):
            raise TypeError('annotation only works on classes')
        return annotate(cls)
    else:
        return annotate

