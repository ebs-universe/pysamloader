# encoding: utf-8

# Copyright (C) 2015-2019 Chintalagiri Shashank
#
# This file is part of tendril.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
The Terminal Utils Module (:mod:`tendril.utils.terminal`)
=========================================================

This module provides utils for rendering basic UI elements on the terminal.


:class:`TendrilProgressBar` can be used to produce animated progress bars
on the terminal. This class (and the code related to it) is essentially a
copy of pip's progressbar implementation in pip.utils.ui.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os
import shlex
import struct
import platform
import subprocess

import six
from progress.bar import Bar
from progress.bar import IncrementalBar

try:
    import colorama
# Lots of different errors can come from this, including SystemError and
# ImportError.
except (ImportError, SystemError):
    colorama = None

WINDOWS = (sys.platform.startswith("win") or
           (sys.platform == 'cli' and os.name == 'nt'))


def get_terminal_width():
    return get_terminal_size()[0]


def colortext(string, color):
    return ''.join([color, string, colorama.Fore.RESET])


def render_hline(color=None):
    width = get_terminal_width()
    hline = '-' * width
    if color:
        hline = colortext(hline, color)
    print(hline)


def get_terminal_size():
    """
    getTerminalSize()

    - get width and height of console
    - works on linux,os x,windows,cygwin(windows)

    Taken from https://gist.github.com/jtriley/1108174
    """
    current_os = platform.system()
    tuple_xy = None
    if current_os == 'Windows':
        tuple_xy = _get_terminal_size_windows()
        if tuple_xy is None:
            tuple_xy = _get_terminal_size_tput()
            # needed for window's python in cygwin's xterm!
    if current_os in ['Linux', 'Darwin'] or current_os.startswith('CYGWIN'):
        tuple_xy = _get_terminal_size_linux()
    if tuple_xy is None:
        tuple_xy = (80, 25)      # default value
    return tuple_xy


def _get_terminal_size_windows():
    try:
        from ctypes import windll, create_string_buffer
        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (bufx, bufy, curx, cury, wattr,
             left, top, right, bottom,
             maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            sizex = right - left + 1
            sizey = bottom - top + 1
            return sizex, sizey
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        pass


def _get_terminal_size_tput():
    # get terminal width
    try:
        cols = int(subprocess.check_call(shlex.split('tput cols')))
        rows = int(subprocess.check_call(shlex.split('tput lines')))
        return cols, rows
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        pass


def _get_terminal_size_linux():
    def ioctl_GWINSZ(fd):
        try:
            import fcntl
            import termios
            cr = struct.unpack('hh',
                               fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
            return cr
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass
    if not cr:
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            return None
    return int(cr[1]), int(cr[0])


def _select_progress_class(preferred, fallback):
    encoding = getattr(preferred.file, "encoding", None)

    # If we don't know what encoding this file is in, then we'll just assume
    # that it doesn't support unicode and use the ASCII bar.
    if not encoding:
        return fallback

    # Collect all of the possible characters we want to use with the preferred
    # bar.
    characters = [
        getattr(preferred, "empty_fill", six.text_type()),
        getattr(preferred, "fill", six.text_type()),
    ]
    characters += list(getattr(preferred, "phases", []))

    # Try to decode the characters we're using for the bar using the encoding
    # of the given file, if this works then we'll assume that we can use the
    # fancier bar and if not we'll fall back to the plaintext bar.
    try:
        six.text_type().join(characters).encode(encoding)
    except UnicodeEncodeError:
        return fallback
    else:
        return preferred


_BaseBar = _select_progress_class(IncrementalBar, Bar)


class WindowsMixin(object):

    def __init__(self, *args, **kwargs):
        # The Windows terminal does not support the hide/show cursor ANSI
        # codes even with colorama. So we'll ensure that hide_cursor is False
        # on Windows.
        # This call neds to go before the super() call, so that hide_cursor
        # is set in time. The base progress bar class writes the "hide cursor"
        # code to the terminal in its init, so if we don't set this soon
        # enough, we get a "hide" with no corresponding "show"...
        if WINDOWS and self.hide_cursor:
            self.hide_cursor = False

        super(WindowsMixin, self).__init__(*args, **kwargs)

        # Check if we are running on Windows and we have the colorama module,
        # if we do then wrap our file with it.
        if WINDOWS and colorama:
            self.file = colorama.AnsiToWin32(self.file)
            # The progress code expects to be able to call self.file.isatty()
            # but the colorama.AnsiToWin32() object doesn't have that, so
            # we'll add it.
            self.file.isatty = lambda: self.file.wrapped.isatty()
            # The progress code expects to be able to call self.file.flush()
            # but the colorama.AnsiToWin32() object doesn't have that, so
            # we'll add it.
            self.file.flush = lambda: self.file.wrapped.flush()


class ProgressBar(WindowsMixin, _BaseBar):
    file = sys.stdout
    message = "%(percent)3d%%"
    suffix = "ETA %(eta_td)s"

    def __init__(self, *args, **kwargs):
        super(ProgressBar, self).__init__(*args, **kwargs)
        self._note = None
        self._term_width = get_terminal_width()

    @property
    def term_width(self):
        return self._term_width

    def next(self, n=1, note=None):
        self._note = str(note)
        super(_BaseBar, self).next(n)

    def writeln(self, line):
        if self.file.isatty():
            self.clearln()
            if self._note is not None:
                line = ' '.join([line, self._note])
                if len(line) > self.term_width:
                    line = line[:self.term_width]
            print(line, end='', file=self.file)
            self.file.flush()
