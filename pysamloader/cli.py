#!/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012-2019 Chintalagiri Shashank
#
# This file is part of pysamloader.

# pysamloader is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pysamloader is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pysamloader.  If not, see <http://www.gnu.org/licenses/>.


import logging
import argparse

from serial.tools import list_ports

from .terminal import ProgressBar
from .pysamloader import get_device
from .pysamloader import get_supported_devices
from .pysamloader import write_and_verify
from .pysamloader import read_chipid
from .pysamloader import read_flash_descriptors
from .pysamloader import read_unique_identifier
from .pysamloader import set_boot_from_flash
from . import __version__

logger = logging.getLogger('cli')


def print_supported_devices():
    print("Supported devices : ")
    for d in get_supported_devices():
        print(" - {0}".format(d[0]))


def print_serial_ports():
    print("Detected serial ports : ")
    for p in list_ports.comports():
        print(" - {0:15} {1:20} {2:18} {3:18}"
              "".format(str(p.device), str(p.manufacturer),
                        str(p.product), str(p.serial_number)))


def print_chipid(*args, **kwargs):
    chipid = read_chipid(*args, **kwargs)
    print(chipid)


def print_flash_descriptors(*args, **kwargs):
    descriptors = read_flash_descriptors(*args, **kwargs)
    print(descriptors)


def print_unique_identifier(*args, **kwargs):
    uid = read_unique_identifier(*args, **kwargs)
    print(uid)


def _get_parser():
    parser = argparse.ArgumentParser(
        description="Write an Atmel SAM chip's Flash using SAM-BA over UART")

    parser.add_argument('-v', action='store_true',
                        help="Verbose debug information")
    parser.add_argument('-P', '--port', metavar='port', default="/dev/ttyUSB1",
                        help="Port on which SAM-BA is listening. Default /dev/ttyUSB1"),
    parser.add_argument('-b', '--baud', metavar='baud', type=int, default=115200,
                        help="Baud rate of serial communication. Default 115200"),
    parser.add_argument('-d', '--device', metavar='device',
                        help="Atmel SAM Device. Default ATSAM3U4E")

    action = parser.add_mutually_exclusive_group(required=False)
    action.add_argument('-V', action='store_true',
                        help="Show version information and exit")
    action.add_argument('--lp', '--list-ports', action='store_true',
                        help="List available serial ports and exit")
    action.add_argument('--ld', '--list-devices', action='store_true',
                        help="List supported devices and exit")
    action.add_argument('--rc', '--read-chipid', action='store_true',
                        help="Read Chip ID and exit")
    action.add_argument('--rd', '--read-descriptor', action='store_true',
                        help="Read flash descriptors and exit")
    action.add_argument('--ri', '--read-identifier', action='store_true',
                        help="Read unique identifier and exit")

    parser.add_argument('-g', action='store_true', help="Set GPNVM bit(s) "
                        "to switch device boot from SAM-BA ROM to Flash. If "
                        "provided with a file to write, will be set after "
                        "successful write/verify.")
    parser.add_argument('--nv', '--no-verify', action='store_true',
                        help="Do not verify after write.")
    parser.add_argument('--nw', '--no-write', action='store_true',
                        help="Do not write only. Verify only.")
    parser.add_argument('filename', metavar='file', nargs='?',
                        help="Binary file to be burnt into the chip")
    return parser


def main():
    parser = _get_parser()
    arguments = parser.parse_args()

    if arguments.v:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('pysamloader').setLevel(logging.DEBUG)
        logging.getLogger('samba').setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        logging.getLogger('pysamloader').setLevel(logging.INFO)
        logging.getLogger('samba').setLevel(logging.INFO)

    if arguments.V:
        print("pysamloader {0}".format(__version__))
        return

    if arguments.lp:
        return print_serial_ports()

    if arguments.ld:
        return print_supported_devices()

    if not arguments.device:
        logger.info("Device not specified. Assuming ATSAM3U4E.")
        arguments.device = 'ATSAM3U4E'

    try:
        dev = get_device(arguments.device)
    except ImportError:
        from .samdevice import SAMDevice
        dev = SAMDevice
        logger.warning("Device is not supported!")
        print_supported_devices()

    arguments.device = dev

    if arguments.rc:
        return print_chipid(port=arguments.port,
                            baud=arguments.baud,
                            device=arguments.device)

    if arguments.rd:
        return print_flash_descriptors(port=arguments.port,
                                       baud=arguments.baud,
                                       device=arguments.device)

    if arguments.ri:
        return print_unique_identifier(port=arguments.port,
                                       baud=arguments.baud,
                                       device=arguments.device)

    if arguments.g and not arguments.filename:
        return set_boot_from_flash(port=arguments.port,
                                   baud=arguments.baud,
                                   device=arguments.device)

    if not arguments.filename:
        print("No bin file provided and no list actions requested.")
        parser.print_help()
        return

    write_and_verify(arguments, progress_class=ProgressBar)


if __name__ == "__main__":
    main()
