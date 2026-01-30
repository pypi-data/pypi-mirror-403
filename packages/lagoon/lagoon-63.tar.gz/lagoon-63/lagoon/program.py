from .util import threadlocalproperty
from foyndation import singleton, solo
from itertools import chain
from parabject import Parabject, register, unmangle
from pathlib import Path
from types import SimpleNamespace
import functools, json, os, re, shlex, subprocess, sys

envnamematch = re.compile('[A-Z0-9_]+').fullmatch
textmodekeys = 'text', 'universal_newlines', 'encoding', 'errors'
unserializables = False, True, None, Ellipsis

class Program:
    'Normally import an instance from `lagoon.text` or `lagoon.binary` module instead of instantiating manually.'

    bginfo = threadlocalproperty(lambda: None)

    @staticmethod
    def _strornone(arg):
        return arg if arg is None else str(arg)

    @classmethod
    def text(cls, path):
        'Return text mode ProgramHandle for the executable at the given path.'
        return cls(path, True, None, (), {}, _fgmode, 0).handle

    @classmethod
    def binary(cls, path):
        'Return binary mode ProgramHandle for executable at given path.'
        return cls(path, False, None, (), {}, _fgmode, 0).handle

    @classmethod
    def of(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def __init__(self, path, textmode, cwd, args, kwargs, runmode, ttl):
        self.handle = register(self, ProgramHandle)
        self.path = path
        self.textmode = textmode
        self.cwd = cwd
        self.args = args
        self.kwargs = kwargs
        self.runmode = runmode
        self.ttl = ttl

    def _resolve(self, path):
        return Path(path) if self.cwd is None else self.cwd / path

    def cd(self, cwd):
        return self.of(self.path, self.textmode, self._resolve(cwd), self.args, self.kwargs, self.runmode, self.ttl).handle

    def getattr(self, name):
        return self.of(self.path, self.textmode, self.cwd, self.args + (unmangle(name).replace('_', '-'),), self.kwargs, self.runmode, self.ttl).handle

    def getitem(self, keys):
        for k in keys:
            try:
                streams = k.start, k.stop, k.step
            except AttributeError:
                self = styles[k](self)
            else:
                self = -self.handle[partial](**{name: None if stream is sys else stream for name, stream in zip(['stdin', 'stdout', 'stderr'], streams) if stream is not None})
        return self.handle

    def _mergedkwargs(self, kwargs):
        merged = {**self.kwargs, **kwargs}
        k = 'env'
        if k in self.kwargs and k in kwargs:
            d1 = self.kwargs[k]
            if d1 is not None: # Otherwise d2 wins, whatever it is.
                d2 = kwargs[k]
                merged[k] = d1 if d2 is None else {**d1, **d2}
        return merged

    def _transform(self, args, kwargs, disposition):
        kwargs = self._mergedkwargs(kwargs)
        cmd = [self._xformpath()]
        for i, arg in enumerate(chain(self.args, args)):
            if any(arg is x for x in unserializables):
                raise ValueError(f"Arg {i} is unserializable.")
            r = getattr(arg, 'readable', lambda: False)()
            w = getattr(arg, 'writable', lambda: False)()
            if r:
                if w:
                    raise ValueError(f"Arg {i} is both readable and writable.")
                if 'stdin' in kwargs:
                    raise ValueError(f"Arg {i} is readable but stdin is already occupied.")
                kwargs['stdin'] = arg
                arg = '-'
            elif w:
                if 'stdout' in kwargs:
                    raise ValueError(f"Arg {i} is writable but stdout is already occupied.")
                kwargs['stdout'] = arg
                arg = '-'
            elif not isinstance(arg, bytes):
                arg = str(arg)
            cmd.append(arg)
        if bool == kwargs.get('check'):
            kwargs['check'] = False
            mapcode = lambda rc: not rc
        else:
            kwargs.setdefault('check', True)
            mapcode = lambda rc: rc
        kwargs.setdefault('stdout', subprocess.PIPE)
        kwargs.setdefault('stderr', None)
        if self.textmode and all(kwargs.get(k) is None for k in textmodekeys):
            kwargs['text'] = True
        kwargs['cwd'] = self._strornone(self._resolve(kwargs['cwd']) if 'cwd' in kwargs else self.cwd)
        env = AbsEnv(kwargs.pop('absenv', None))
        env.patch(kwargs.get('env'))
        patch = {k: v for k, v in kwargs.items() if envnamematch(k) is not None}
        env.patch(patch or None)
        for k in patch:
            del kwargs[k]
        kwargs['env'] = env.d
        aux = kwargs.pop('aux', ())
        if disposition is None:
            resxform = None
        else:
            @list
            @singleton
            def attrxforms():
                def streamxforms(name):
                    val = kwargs[name]
                    if val == subprocess.PIPE:
                        yield ResultAttrTransform.identity(name)
                    elif val in {NOEOL, ONELINE, json.loads}:
                        kwargs[name] = subprocess.PIPE
                        yield disposition.streamxform(name, val)
                if not kwargs['check']:
                    yield disposition.checkxform(mapcode)
                if kwargs.get('stdin') == subprocess.PIPE:
                    yield ResultAttrTransform.identity('stdin')
                for stream in 'stdout', 'stderr':
                    yield from streamxforms(stream)
                for auxname in aux if isinstance(aux, tuple) else [aux]:
                    yield ResultAttrTransform.identity(auxname)
            if not attrxforms:
                resxform = lambda res: None
            elif 1 == len(attrxforms):
                resxform = attrxforms[0].apply
            else:
                def resxform(res):
                    for xform in attrxforms:
                        xform.modify(res)
                    return res
        return cmd, kwargs, resxform

    def _xformpath(self):
        try:
            is_absolute = self.path.is_absolute
        except AttributeError:
            return self.path
        return self.path if is_absolute() else f"{os.curdir}{os.sep}{self.path}"

    def call(self, args, kwargs):
        if self.ttl:
            return self.of(self.path, self.textmode, self.cwd, self.args + args, self._mergedkwargs(kwargs), self.runmode, self.ttl - 1).handle
        return self.runmode(self, *args, **kwargs)

    def str(self):
        return ' '.join(shlex.quote(str(w)) for w in [self.path, *self.args])

    def enter(self):
        assert not self.ttl
        cmd, kwargs, xform = self._transform((), {}, Background)
        check = kwargs.pop('check')
        process = subprocess.Popen(cmd, **kwargs)
        try:
            result = xform(process)
            self.bginfo = self.bginfo, cmd, check, process
            return result
        except:
            with process:
                raise

    def exit(self, exc_info):
        self.bginfo, cmd, check, process = self.bginfo
        with process:
            pass # XXX: Propagate our exc_info?
        if check and process.returncode:
            raise subprocess.CalledProcessError(process.returncode, cmd)

class AbsEnv:

    def __init__(self, d):
        self.d = d

    def patch(self, d):
        if d is not None:
            if self.d is None:
                self.d = os.environ.copy()
            for k, v in d.items():
                if v is None:
                    self.d.pop(k, None)
                else:
                    self.d[k] = v

@singleton
class Background:

    def checkxform(self, mapval):
        return ResultAttrTransform('wait', lambda wait: lambda: mapval(wait()))

    def streamxform(self, name, mapval):
        return ResultAttrTransform(name, lambda stream: SimpleNamespace(close = stream.close, read = lambda: mapval(stream.read())))

@singleton
class Foreground:

    def checkxform(self, mapval):
        return ResultAttrTransform('returncode', mapval)

    def streamxform(self, name, mapval):
        return ResultAttrTransform(name, mapval)

class ResultAttrTransform:

    @classmethod
    def identity(cls, name):
        return cls(name, lambda x: x)

    def __init__(self, name, mapval):
        self.name = name
        self.mapval = mapval

    def apply(self, res):
        return self.mapval(getattr(res, self.name))

    def modify(self, res):
        setattr(res, self.name, self.apply(res))

class ProgramHandle(Parabject):

    def __getattr__(self, name):
        'Add argument, where underscore means dash.'
        return (-self).getattr(name)

    def __getitem__(self, key):
        'Apply a style, e.g. `partial` to suppress execution or `print` to send stdout to console.'
        return (-self).getitem(key if isinstance(key, tuple) else [key])

    def __call__(self, *args, **kwargs):
        'Run program in foreground with additional args. Accepts many subprocess kwargs. Use `partial` style to suppress execution, e.g. before running in background. Otherwise return CompletedProcess, or one of its fields if the rest are redirected, or None if all fields redirected.'
        return (-self).call(args, kwargs)

    def __str__(self):
        return (-self).str()

    def __enter__(self):
        'Start program in background yielding the Popen object, or one of its fields if the rest are redirected.'
        return (-self).enter()

    def __exit__(self, *exc_info):
        return (-self).exit(exc_info)

@singleton
class NOEOL:
    'Style to strip trailing newlines from stdout, in the same way as shell does.'

    t, b = (re.compile(x(r'[\r\n]*$')) for x in [lambda s: s, lambda s: s.encode('ascii')])

    def __call__(self, text):
        return text[:(self.t if hasattr(text, 'encode') else self.b).search(text).start()]

def ONELINE(text):
    'Style to assert exactly one line of output, using `splitlines`.'
    return solo(text.splitlines())

def _boolstyle(program):
    return -program.handle[partial](check = bool)

def _partialstyle(program):
    return program.of(program.path, program.textmode, program.cwd, program.args, program.kwargs, program.runmode, program.ttl + 1)

def _fgmode(program, *args, **kwargs):
    cmd, kwargs, xform = program._transform(args, kwargs, Foreground)
    return xform(subprocess.run(cmd, **kwargs))

def _stdoutstyle(token):
    return lambda program: -program.handle[partial](stdout = token)

def _teestyle(program):
    return program.of(program.path, program.textmode, program.cwd, program.args, program.kwargs, _teemode, program.ttl)

def _teemode(program, *args, **kwargs):
    def lines():
        with program.handle[partial](*args, **kwargs) as stdout:
            while True:
                line = stdout.readline()
                if not line:
                    break
                yield line
                sys.stdout.write(line)
    return ''.join(lines())

def _execstyle(program):
    return program.of(program.path, program.textmode, program.cwd, program.args, program.kwargs, _execmode, program.ttl)

def _execmode(program, *args, **kwargs): # XXX: Flush stdout (and stderr) first?
    supportedkeys = {'cwd', 'env'}
    keys = kwargs.keys()
    if not keys <= supportedkeys:
        raise Exception("Unsupported keywords: %s" % (keys - supportedkeys))
    cmd, kwargs, _ = program._transform(args, kwargs, None)
    cwd, env = (kwargs[k] for k in ['cwd', 'env'])
    if cwd is None:
        os.execvpe(cmd[0], cmd, env)
    # First replace this program so that failure can't be caught after chdir:
    precmd = [sys.executable, '-c', 'import os, sys; cwd, *cmd = sys.argv[1:]; os.chdir(cwd); os.execvp(cmd[0], cmd)', cwd, *cmd]
    os.execve(precmd[0], precmd, os.environ if env is None else env)

bg = partial = object()
tee = object()
styles = {
    bool: _boolstyle,
    exec: _execstyle,
    functools.partial: _partialstyle,
    json: _stdoutstyle(json.loads),
    NOEOL: _stdoutstyle(NOEOL),
    ONELINE: _stdoutstyle(ONELINE),
    partial: _partialstyle,
    print: _stdoutstyle(None),
    tee: _teestyle,
}
