from .text import tput
from foyndation import singleton
from itertools import islice
from multifork import Tasks
from subprocess import CalledProcessError
import sys

class Style:

    pending = object()
    running = object()
    normal = object()
    abrupt = object()

class Terminal:

    class Section:

        height = 0

    def __init__(self, width):
        self.sections = []
        self.width = width

    def _common(self, index, tonewh):
        # FIXME LATER: Solution for content that has scrolled off the top of the sceeen.
        dy = sum(s.height for s in islice(self.sections, index + 1, None))
        section = self.sections[index]
        oldh = section.height
        section.height = newh = tonewh(oldh)
        if dy:
            tput.cuu[:sys.stderr](dy)
        if newh > oldh:
            tput.il[:sys.stderr](newh - oldh)
        return dy, oldh, newh

    def head(self, index, obj, style):
        for _ in range(len(self.sections), index + 1):
            self.sections.append(self.Section())
        dy, oldh, newh = self._common(index, lambda h: max(1, h))
        if oldh:
            tput.cuu[:sys.stderr](oldh)
        if Style.pending == style:
            ansi = tput.setaf(0)
        elif Style.running == style:
            ansi = tput.rev()
        elif Style.abrupt == style:
            ansi = tput.setab(1) + tput.setaf(7)
        else:
            ansi = ''
        sys.stderr.write(f"{ansi}[{obj}{ansi}]{tput.sgr0()}\n")
        sys.stderr.write('\n' * (newh - 1 + dy))

    def log(self, index, stream, line):
        dy, oldh, newh = self._common(index, lambda h: h + 1)
        noeol, = line.splitlines()
        eol = line[len(noeol):]
        if noeol:
            # FIXME: Account for non-printing characters.
            chunks = [noeol[i:i + self.width] for i in range(0, len(noeol), self.width)]
            stream.write(chunks[0])
            for c in islice(chunks, 1, None):
                stream.flush()
                tput.hpa[:sys.stderr](0)
                sys.stderr.flush()
                stream.write(c)
        if eol:
            stream.write(eol)
        else:
            stream.flush()
        sys.stderr.write('\n' * ((not eol) + dy))

@singleton
class LogFile:

    words = {
        Style.running: 'Damp',
        Style.normal: 'Soaked',
        Style.abrupt: 'Failed',
    }

    def head(self, index, obj, style):
        try:
            word = self.words[style]
        except KeyError:
            return
        print(f"{word}:", obj, file = sys.stderr)

    def log(self, index, stream, line):
        stream.write(line)

def _getterminal():
    try:
        width = int(tput.cols())
    except CalledProcessError:
        return LogFile
    return Terminal(width)

class TerminalTasks(Tasks):

    class Task:

        def __init__(self, index, title, taskimpl):
            self.index = index
            self.title = title
            self.taskimpl = taskimpl

        def __call__(self):
            return self.taskimpl()

    def __init__(self):
        super().__init__()
        self.terminal = _getterminal()

    def add(self, title, taskimpl):
        self.append(task := self.Task(len(self), title, taskimpl))
        self.terminal.head(task.index, task.title, Style.pending)

    def started(self, task):
        self.terminal.head(task.index, task.title, Style.running)

    def stdout(self, task, line):
        self.terminal.log(task.index, sys.stdout, line)

    def stderr(self, task, line):
        self.terminal.log(task.index, sys.stderr, line)

    def stopped(self, task, code):
        self.terminal.head(task.index, task.title, Style.abrupt if code else Style.normal)
