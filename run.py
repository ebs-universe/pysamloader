#!/bin/python

# This file exists only to provide a script like target for pyinstaller
# or other freeze mechanisms. Users should generally just use the
# provided setuptools script entry-point in cli.py when the package
# is pip-installed.
#
# If you're using a binary distribution, I'm assuming you're never going
# to see this comment or the specifics of the internal structure.
#
# Binary distributions are intended to be made using
#
#  $ pyinstaller run.py -n pysamloader
#
# Note that this needs the environment's python to be compiled for shared
# library use. If you're using pyenv / virtualenv, you will probably have
# to specify the LD_LIBRARY_PATH to point to the correct python lib to
# link against.

from pysamloader import cli
cli.main()
