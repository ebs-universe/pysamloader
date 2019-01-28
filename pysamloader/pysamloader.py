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
import sys
import logging
import appdirs

from xmodem import XMODEM
from binascii import hexlify
from six import StringIO

from .samba import SamBAConnection

if sys.version_info.major == 3 and sys.version_info.minor >= 5:
    import importlib.util
elif sys.version_info.major == 3 and 3 <= sys.version_info.minor <= 4:
    import importlib.machinery
else:
    import imp


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
                 start_page=0, set_boot=True, progress_class=None):
    stat = 1
    if device.FullErase:
        samba.efc_eraseall()
    page_no = start_page
    bin_file = open(filename, "r")
    num_pages = int((os.fstat(bin_file.fileno())[6] + 128) / 256)
    p = progress_class(max=num_pages)

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


def verify(samba, device, filename, start_page=0, progress_class=None):
    """
    Verify the contents of flash against the contents of the file.
    Returns the total number of words with errors. 

    """
    bin_file = open(filename, "r")
    len_bytes = os.fstat(bin_file.fileno())[6]
    address = int(device.FS_ADDRESS, 16) + (start_page * device.PAGE_SIZE)
    errors = 0
    byte_address = 0
    p = progress_class(max=len_bytes)
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


def write_and_verify(args, progress_class=None):
    samba = SamBAConnection(port=args.port, baud=args.baud, device=args.device)
    if args.c is False:
        raw_sendf(samba, args.device, args.filename,
                  set_boot=args.g, progress_class=progress_class)
    samba.make_connection(auto_baud=args.ab)
    verify(samba, args.device, args.filename, progress_class=progress_class)


def get_supported_devices():
    devices_folder_candidates = [
        os.path.join(appdirs.user_config_dir('pysamloader'), 'devices'),
        os.path.join(os.path.split(__file__)[0], 'devices')
    ]
    for candidate in devices_folder_candidates:
        if os.path.exists(candidate):
            devices_folder = candidate
            break
    else:
        raise FileNotFoundError("Devices folder not found!")

    candidates = [f for f in os.listdir(devices_folder)
                  if os.path.isfile(os.path.join(devices_folder, f))
                  and not f.startswith('_')]
    _supported_devices = []
    for candidate in candidates:
        name, ext = os.path.splitext(candidate)
        if ext == '.py':
            try:
                # See : https://stackoverflow.com/a/67692/1934174
                if sys.version_info.major == 3 and sys.version_info.minor >= 5:
                    spec = importlib.util.spec_from_file_location(
                        'pysamloader.devices.{}'.format(name),
                        os.path.join(devices_folder, '{0}.py'.format(name))
                    )
                    dev_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(dev_mod)
                elif sys.version_info.major == 3 and 3 <= sys.version_info.minor <= 4:
                    dev_mod = importlib.machinery.SourceFileLoader(
                        'pysamloader.devices.{}'.format(name),
                        os.path.join(devices_folder, '{0}.py'.format(name))
                    ).load_module()
                else:
                    dev_mod = imp.load_source(
                        'pysamloader.devices.{}'.format(name),
                        os.path.join(devices_folder, '{0}.py'.format(name))
                    )
                getattr(dev_mod, name)
                _supported_devices.append((name, "SAM-BA UART",
                                           "{0}.{1}".format(dev_mod.__name__, name)))
            except ImportError:
                continue
    return _supported_devices


supported_devices = get_supported_devices()
