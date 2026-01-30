from . import binary, text
from .program import Program
from .sic import binary as sic_binary, text as sic_text
from pathlib import Path
import os

def _scan():
    programs = {}
    for parent in map(Path, os.environ['PATH'].split(os.pathsep)):
        if parent.is_dir():
            for path in parent.iterdir():
                if path.name not in programs:
                    programs[path.name] = path
    _scaninto(text, binary, sic_text, sic_binary, programs)

def _scaninto(textmodule, binarymodule, sictext, sicbinary, programs):
    for name, path in programs.items():
        textprogram = Program.text(path)
        binaryprogram = Program.binary(path)
        if '_' in name:
            key = None
        elif '-' not in name:
            key = name
        else:
            key = name.replace('-', '_')
            if not key.isidentifier():
                key = None
        if key is None:
            setattr(sictext, name, textprogram)
            setattr(sicbinary, name, binaryprogram)
        else:
            setattr(textmodule, key, textprogram)
            setattr(binarymodule, key, binaryprogram)

_scan()
