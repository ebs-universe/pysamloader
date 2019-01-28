
pysamloader
===========

``pysamloader`` is a python script for writing flash on Atmel's ARM chips
via SAM-BA. Originally written years ago when Atmel's standard tools were
unavailable or unusable on Linux, the scripts have been adapted to serve
narrower but specific use cases.

Specifically, ``pysamloader`` is intended to be :

    - Simple, particularly for an end-user
    - Easily installable across platforms
    - Usable from within larger python applications or scripts

Currently, ``pysamloader`` might not satisfy any of those criteria. It seems
to be reasonably stable on a tiny set of supported devices with some
additional limitations, but that's about it.

If you happen to use ``pysamloader``, or wish to use it, let me know along
with any feedback you might have to ensure the tool is stable, reliable, and
sufficiently versatile. Device support is easy enough to add, and I will do
so as the need (and more importantly, the ability to test on other devices)
presents itself. Pull requests are also welcome.

Currently supported devices are :

.. documentedlist::
    :listobject: pysamloader.pysamloader.supported_devices
    :header: "Device" "Interface" "Support Module"

Requirements & Installation
---------------------------

``pysamloader`` should work on any platform which supports ``python``.
It is best tested on Linux followed by Windows (10 and 7).

``pysamloader`` currently supports both Python 2 and Python 3. However,
Python 2 support is likely to be removed in the near future.

Currently, ``pysamloader`` is expected to be pip-installed. It can be
safely installed into a ``virtualenv``. There are no distro-specific
packages or windows installers available.

Installing ``pysamloader`` for most users would be simply :

.. code-block:: console

    $ pip install pysamloader

If you wish to develop, modify the sources, or otherwise get the latest
version, it can be installed from a clone of the git repository (or
clone thereof) as follows :

.. code-block:: console

    $ git clone https://github.com/chintal/pysamloader.git
    $ cd pysamloader
    $ pip install -e .

Usage
-----

The primary entry point for use of ``pysamloader`` is as a console script.

For those in a hurry, the following is a quick example of how to use the
script to burn ``app.bin`` to an ``ATSAM3U4E`` whose UART SAM-BA interface
is accessible on ``\dev\ttyUSB1``:

.. code-block:: console

    $ pysamloader --device ATSAM3U4E --port \dev\ttyUSB1 -g app.bin


Script usage and arguments are listed here. This help listing can also be
obtained on the command line with ``pysamloader --help``.

.. argparse::
    :module: pysamloader.cli
    :func: _get_parser
    :prog: pysamloader
    :nodefault:

Known Issues
------------

 - Writing to multiple flash planes is not currently supported. This
   application will always write to the first flash plane and will start at
   the beginning.

Future Directions
-----------------

 - Add support for ``libftdi``/``libd2xx``/``libusb`` based backend for cases
   where the device disables ``ftdi_sio`` for its normal operation.
 - Add hooks for device auto-detection. Do not even bother to probe blindly
   for SAM-BA - that is too dangerous. Instead rely on apriori knowledge of
   signatures of device configuration, including VID, PID, Manufacturer,
   Product, Serial Number, and USB endpoint descriptors.
 - Add a clean and simple GUI.
 - Add read capability for chip signature and/or silicon serial number.

Links
-----

The latest version of the documentation, including installation, usage, and
API/developer notes can be found at
`ReadTheDocs <http://pysamloader.readthedocs.org/en/latest/index.html>`_.

The latest version of the sources can be found at
`GitHub <https://github.com/chintal/pysamloader>`_. Please use GitHub's features
to report bugs, request features, or submit pull/merge requests.

``pysamloader`` is distributed under the terms of the
`GPLv3 license <https://www.gnu.org/licenses/gpl-3.0-standalone.html>`_ .
A copy of the text of the license is included along with the sources.

I can be reached directly by email at shashank at chintal dot in.
