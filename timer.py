#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Timer for checking speed of code block.
Wrap blocks of code that you want to time with Python's with keyword and this Timer context manager. It will take care
of starting the timer when your code block begins execution and stopping the timer when your code block ends.

Adapted from: http://www.huyng.com/posts/python-performance-analysis/ (Mar 19, 2015)

=== Example ===
from timer import Timer
from redis import Redis
rdb = Redis()

with Timer() as t:
    rdb.lpush("foo", "bar")
print "=> elasped lpush: %s s" % t.secs

with Timer() as t:
    rdb.lpop("foo")
print "=> elasped lpop: %s s" % t.secs
"""

import time

__author__ = 'Marc Schulder'


class Timer(object):
    """
    Timer for checking speed of code block.
Wrap blocks of code that you want to time with Python's with keyword and this Timer context manager. It will take care
of starting the timer when your code block begins execution and stopping the timer when your code block ends.
    """
    def __init__(self, info=None, verbose=False):
        self.verbose = verbose
        self.info = info

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *_):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # milliseconds
        if self.verbose:
            print self.getSummary(self.info)

    def getSummary(self, info=None):
        if info is None:
            info = self.info
        if info is None:
            return 'Elapsed time: %s' % getTimeString(self.secs)
        else:
            return '%s %s' % (info, getTimeString(self.secs))


def getTimeString(seconds):
    """
    Get a pretty time string, using hours, minutes, seconds and milliseconds as required.
    :param seconds: The desired time span, given in seconds. Can be an int or a float.
    :return: A string representing the desired time span, given in hours, minutes, seconds and milliseconds.
    """
    units = list()
    msecs = (seconds % 1) * 1000
    if msecs >= 1:
        units.append('{0}ms'.format(int(msecs % 60)))
    units.append('{0}s'.format(int(seconds % 60)))
    minutes = seconds/60
    if minutes >= 1:
        units.append('{0}m'.format(int(minutes % 60)))
        hours = minutes/60
        if hours >= 1:
            units.append('{0}h'.format(int(hours % 60)))
    return ' '.join(units[::-1])
