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

import os
import argparse
import logging
import importlib

from xmodem import XMODEM
from binascii import hexlify
from six import StringIO
from serial.tools import list_ports

from .terminal import ProgressBar
from .samba import SamBAConnection

logging.basicConfig(format='[%(levelname)8s][%(name)s] %(message)s')
logger = logging.getLogger('pysamloader')


def raw_write_page(samba, page_address, data):
    for i in range(0, 256, 4):
        wbytes = "".join(byte for byte in reversed(data[i:i+4]))
        adrstr = hex(page_address + i)[2:].zfill(8)
        samba.write_word(adrstr, hexlify(wbytes))


def xm_write_page(samba, page_address, data):
    adrstr = hex(page_address)[2:].zfill(8)
    samba.xm_init_sf(adrstr)
    sendbuf = StringIO(data)
    modem = XMODEM(samba.xm_getc, samba.xm_putc)
    modem.send(sendbuf, quiet=True)
    sendbuf.close()


def _page_writer(_writer, samba, device, page_address, bin_file):
    """
        Send a single page worth of data from the file to the chip.
        Returns 1 as long as data remains.
        Returns 0 when end of file is reached.
    """
    data = bin_file.read(device.PAGE_SIZE)
    if len(data) == device.PAGE_SIZE:
        status = 1
    else:
        if len(data) < device.PAGE_SIZE:
            data += "\255" * (device.PAGE_SIZE - len(data))
        status = 0
    logger.debug(len(data))
    logger.debug('Sending file chunk : \n {0}CEND'.format(hexlify(data)))
    _writer(samba, page_address, data)
    return status


def _file_writer(_writer, samba, device, filename,
                 start_page=0, set_boot=True):
    stat = 1
    if device.FullErase:
        samba.efc_eraseall()
    page_no = start_page
    bin_file = open(filename, "r")
    num_pages = int((os.fstat(bin_file.fileno())[6] + 128) / 256)
    p = ProgressBar(max=num_pages)

    logger.info("Writing to Flash")
    while stat:
        samba.efc_wready()
        page_address = int(device.FS_ADDRESS, 16) + (page_no * device.PAGE_SIZE)
        adrstr = hex(page_address)[2:].zfill(8)
        logger.debug("Start Address of page {0} : {1}".format(page_no, adrstr))
        stat = _writer(samba, device, page_address, bin_file)
        samba.efc_ewp(page_no)
        logger.debug("Page done : {0}".format(page_no))
        page_no = page_no + 1
        p.next(note="Page {0}/{1}".format(page_no, num_pages))
    logger.info("Writing to Flash Complete")

    if set_boot:
        logger.info("Setting GPNVM bit to boot from flash")
        for i in range(3):
            if device.SGP[i] == 1:
                samba.efc_setgpnvm(i)
            else:
                samba.efc_cleargpnvm(i)
    else:
        logger.warning("Not setting GPNVM bit.")
        logger.warning("Invoke with -g to have that happen.")


def xmodem_sendf(*args, **kwargs):
    """ Function to burn file onto flash using XMODEM transfers """
    return _file_writer(xm_write_page, *args, **kwargs)


def raw_sendf(*args, **kwargs):
    """ Function to burn file onto flash without using XMODEM transfers """
    return _file_writer(raw_write_page, *args, **kwargs)


def verify(samba, device, filename, start_page=0):
    """
    Verify the contents of flash against the contents of the file.
    Returns the total number of words with errors. 

    """
    bin_file = open(filename, "r")
    len_bytes = os.fstat(bin_file.fileno())[6]
    address = int(device.FS_ADDRESS, 16) + (start_page * device.PAGE_SIZE)
    errors = 0
    byte_address = 0
    p = ProgressBar(max=len_bytes)
    logger.info("Verifying Flash")
    reversed_word = bin_file.read(4)
    word = "".join(byte for byte in reversed(reversed_word))
    while reversed_word:
        p.next(note="{0} of {1} Bytes".format(byte_address, len_bytes))
        result = samba.read_word(hex(address)[2:].zfill(8))
        if not result.upper()[2:] == hexlify(word).upper():
            logger.error("Verification Failed at {0} - {1} {2}"
                         "".format(hex(address), result, hexlify(word)))
            errors = errors + 1
        else:
            logger.debug("Verified Word at {0} - {1} {2}"
                         "".format(hex(address), result, hexlify(word)))
        address = address + 4
        reversed_word = bin_file.read(4)
        word = "".join(byte for byte in reversed(reversed_word))
        byte_address = byte_address + 4
    logger.info("Verification Complete. Words with Errors : " + str(errors))
    return errors


def write_and_verify(args):
    samba = SamBAConnection(port=args.port, baud=args.baud, device=args.device)
    if args.c is False:
        raw_sendf(samba, args.device, args.filename, set_boot=args.g)
    samba.make_connection(auto_baud=args.ab)
    verify(samba, args.device, args.filename)


def get_supported_devices():
    devices_folder = os.path.join(os.path.split(__file__)[0], 'devices')
    candidates = [f for f in os.listdir(devices_folder)
                  if os.path.isfile(os.path.join(devices_folder, f))
                  and not f.startswith('_')]
    supported_devices = []
    for candidate in candidates:
        name, ext = os.path.splitext(candidate)
        if ext == '.py':
            try:
                dev_mod = importlib.import_module('.devices.{0}'.format(name),
                                                  'pysamloader')
                getattr(dev_mod, name)()
                supported_devices.append(name)
            except ImportError:
                continue
    return supported_devices


def print_supported_devices():
    print("Supported devices : ")
    for d in get_supported_devices():
        print(" - {0}".format(d))


def print_serial_ports():
    print("Detected serial ports : ")
    for p in list_ports.comports():
        print(" - {0:15} {1:20} {2:18} {3:18}"
              "".format(str(p.device), str(p.manufacturer),
                        str(p.product), str(p.serial_number)))


def _get_parser():
    parser = argparse.ArgumentParser(
        description="Write an Atmel SAM chip's Flash using SAM-BA over UART")
    parser.add_argument('-g', action='store_true',
                        help="Set GPNVM bit when done writing. Needed to "
                             "switch device boot from SAM-BA ROM to Flash "
                             "program")
    parser.add_argument('-v', action='store_true',
                        help="Verbose debug information")
    parser.add_argument('-c', action='store_true',
                        help="Verify Only. Do not write")
    parser.add_argument('filename', metavar='file', nargs='?',
                        help="Binary file to be burnt into the chip")
    parser.add_argument('--port', metavar='port', default="/dev/ttyUSB1",
                        help="Port on which SAM-BA is listening. "
                             "Default /dev/ttyUSB1")
    parser.add_argument('--baud', metavar='baud', type=int, default=115200,
                        help="Baud rate of serial communication. "
                             "Default 115200")
    parser.add_argument('-d', '--device', metavar='device',
                        help="ARM Device. Default ATSAM3U4E")
    parser.add_argument('--lp', '--list-ports', action='store_true',
                        help="List available serial ports")
    parser.add_argument('--ld', '--list-devices', action='store_true',
                        help="List supported devices")
    return parser


def main():
    parser = _get_parser()
    arguments = parser.parse_args()

    if arguments.v:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('samba').setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        logging.getLogger('samba').setLevel(logging.INFO)

    if arguments.lp:
        return print_serial_ports()

    if arguments.ld:
        return print_supported_devices()

    if not arguments.filename:
        print("No bin file provided and no list actions requested.")
        parser.print_help()
        return

    if not arguments.device:
        logger.info("Device not specified. Assuming ATSAM3U4E.")
        arguments.device = 'ATSAM3U4E'

    try:
        dev_mod = importlib.import_module(
            '.devices.{0}'.format(arguments.device), 'pysamloader')
        dev = getattr(dev_mod, arguments.device)()
    except ImportError:
        from .samdevice import SAMDevice
        dev = SAMDevice()
        logger.warning("Device is not supported!")
        print_supported_devices()

    arguments.device = dev
    write_and_verify(arguments)


if __name__ == "__main__":
    main()
