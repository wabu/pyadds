from contextlib import contextmanager
import time

class Timing:
    def __init__(self, info=''):
        self.reset()
        self.info = info

    def reset(self):
        self.traces = []
        self.end = None
        self.start = time.time()

    def trace(self, info='trace'):
        self.traces.append((info, time.time()))

    def stop(self):
        self.end = time.time()

    def __str__(self):
        return 'timing(%s)' % self.info

    def __repr__(self):
        steps = ['{}:'.format(self.info)]
        last = self.start
        for info, tr in self.traces:
            steps.append('{}:{:.2f}'.format(info, tr-last))
            last = tr
        return '..'.join(steps)
        

@contextmanager
def timing(info=''):
    timing = Timing(info)
    try:
        yield timing
    finally:
        timing.stop()
