from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import local
from unittest import TestCase
import re, sys

@contextmanager
def atomic(path):
    'Context manager yielding a temporary Path for atomic write to the given path. Parent directories are created automatically. Also suitable for making a symlink atomically. Leaves the given path unchanged if an exception happens.'
    path.parent.mkdir(parents = True, exist_ok = True)
    with TemporaryDirectory(dir = path.parent) as d:
        q = Path(d, f"{path.name}.part")
        yield q
        q.rename(path) # XXX: Or replace?

class threadlocalproperty:
    'Like `property` but each thread has its own per-object values.'

    def __init__(self, defaultfactory):
        'The `defaultfactory` should return the initial value per object (per thread).'
        self.local = local()
        self.defaultfactory = defaultfactory

    def _lookup(self):
        try:
            return self.local.lookup
        except AttributeError:
            self.local.lookup = lookup = defaultdict(self.defaultfactory)
            return lookup

    def __get__(self, obj, objtype):
        return self._lookup()[obj]

    def __set__(self, obj, value):
        self._lookup()[obj] = value

@contextmanager
def mapcm(f, obj):
    'Invoke `obj` as a context manager, apply `f` to its yielded value, and yield that. For example apply `Path` to the string yielded by `TemporaryDirectory()`.'
    with obj as cm:
        yield f(cm)

def stripansi(text):
    'Remove ANSI control sequences from the given text, to make it black and white.'
    return re.sub('\x1b\\[[\x30-\x3f]*[\x20-\x2f]*[\x40-\x7e]', '', text) # XXX: Duplicated code?

class Harness:

    def __init__(self, generator):
        try:
            next(generator)
        except StopIteration:
            raise RuntimeError('Generator did not yield.')
        self.continuation = generator

    def close(self):
        try:
            next(self.continuation)
        except StopIteration:
            return
        e = RuntimeError('Generator did not stop.')
        while True:
            try:
                self.continuation.throw(e) # XXX: Or leave generator dangling in this case?
            except StopIteration:
                break

class HarnessCase(TestCase):
    'Enter context managers in setUp and exit them in tearDown.'

    def harness(self):
        'Must yield exactly once.'
        raise NotImplementedError

    def setUp(self):
        self.harnesshandle = Harness(self.harness())

    def tearDown(self):
        self.harnesshandle.close()

def wrappercli():
    'Same as sys.argv[1:] if `--` is present there, otherwise `--` is prepended. This is for sending all options to a wrapped command by default.'
    args = sys.argv[1:]
    if '--' not in args:
        args.insert(0, '--')
    return args
