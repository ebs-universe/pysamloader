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
from six import PY2
from io import BytesIO

from .samba import SamBAConnection
from . import log

if sys.version_info.major == 3 and sys.version_info.minor >= 5:
    import importlib.util
elif sys.version_info.major == 3 and 3 <= sys.version_info.minor <= 4:
    import importlib.machinery
else:
    import imp

logger = logging.getLogger('pysamloader')
log.loggers.append(logger)


def raw_write_page(samba, page_address, data):
    for i in range(0, 256, 4):
        wbytes = bytearray(data[i:i+4])
        wbytes.reverse()
        if PY2:
            wbytes = hexlify(wbytes)
        else:
            wbytes = wbytes.hex()
        adrstr = hex(page_address + i)[2:].zfill(8)
        samba.write_word(adrstr, wbytes)


def xm_write_page(samba, page_address, data):
    adrstr = hex(page_address)[2:].zfill(8)
    samba.xm_init_sf(adrstr)
    sendbuf = BytesIO(data)
    modem = XMODEM(samba.xm_getc, samba.xm_putc)
    if not modem.send(sendbuf, quiet=True):
        raise IOError("XMODEM Transfer Failure")
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
            if PY2:
                padding = "\255"
            else:
                padding = bytes("\255".encode())
            data += padding * (device.PAGE_SIZE - len(data))
        status = 0
    logger.debug('Sending file chunk : \n {0}CEND'.format(hexlify(data)))
    _writer(samba, page_address, data)
    return status


def _file_writer(_writer, samba, device, filename,
                 start_page=0, progress_class=None):
    stat = 1
    if device.FullErase:
        samba.efc_eraseall()
    page_no = start_page
    bin_file = open(filename, "rb")
    num_pages = int((os.fstat(bin_file.fileno())[6] + 128) / 256)
    if progress_class:
        p = progress_class(max=num_pages)
    else:
        p = None

    logger.info("Writing to Flash")
    while stat:
        samba.efc_wready()
        page_address = int(device.FS_ADDRESS, 16) + \
            (page_no * device.PAGE_SIZE)
        adrstr = hex(page_address)[2:].zfill(8)
        logger.debug("Start Address of page {0} : {1}".format(page_no, adrstr))
        stat = _page_writer(_writer, samba, device, page_address, bin_file)
        samba.efc_ewp(page_no)
        logger.debug("Page done : {0}".format(page_no))
        page_no = page_no + 1
        if p:
            p.next(note="Page {0}/{1}".format(page_no, num_pages))
    if p:
        p.finish()
    logger.info("Writing to Flash Complete")


def xmodem_sendf(*args, **kwargs):
    """ Function to burn file onto flash using XMODEM transfers """
    return _file_writer(xm_write_page, *args, **kwargs)


def raw_sendf(*args, **kwargs):
    """ Function to burn file onto flash without using XMODEM transfers """
    return _file_writer(raw_write_page, *args, **kwargs)


def write(samba, device, filename, progress_class=None):
    if isinstance(device, str):
        device = get_device(device)
    enable_xmodem = False
    if enable_xmodem:
        # See device errata in 3U4E datasheet
        _ = samba.efc_readfmr().strip()[2:]
        samba.efc_setfmr('00000600')
        xmodem_sendf(samba, device, filename,
                     progress_class=progress_class)
    else:
        raw_sendf(samba, device, filename,
                  progress_class=progress_class)


def verify(samba, device, filename, start_page=0, progress_class=None):
    """
    Verify the contents of flash against the contents of the file.
    Returns the total number of words with errors.
    """
    bin_file = open(filename, "rb")
    len_bytes = os.fstat(bin_file.fileno())[6]
    address = int(device.FS_ADDRESS, 16) + (start_page * device.PAGE_SIZE)
    errors = 0
    byte_address = 0
    if progress_class:
        p = progress_class(max=len_bytes)
    else:
        p = None
    logger.info("Verifying Flash")
    reversed_word = bytearray(bin_file.read(4))
    word = reversed_word
    word.reverse()
    while reversed_word:
        if p:
            p.next(n=4, note="{0}/{1} Bytes".format(byte_address, len_bytes))
        actual = samba.read_word(hex(address)[2:].zfill(8)).strip()
        if PY2:
            expected = hexlify(word)
        else:
            expected = word.hex()
        if not actual.upper()[2:] == expected.upper():
            logger.error("\nVerification Failed at {0} - {1} {2}"
                         "".format(hex(address), actual, expected))
            errors = errors + 1
        else:
            logger.debug("Verified Word at {0} - {1} {2}"
                         "".format(hex(address), actual, expected))
        address = address + 4
        reversed_word = bytearray(bin_file.read(4))
        word = reversed_word
        word.reverse()
        byte_address = byte_address + 4
    if p:
        p.finish()
    logger.info("Verification Complete. Words with Errors : " + str(errors))
    return errors


def set_boot(samba, device):
    logger.info("Setting GPNVM bit to boot from flash")
    for i in range(3):
        if device.SGP[i] == 1:
            samba.efc_setgpnvm(i)
        else:
            samba.efc_cleargpnvm(i)


def read_chipid(*args, **kwargs):
    samba = kwargs.pop('samba', None)
    if not samba:
        samba = SamBAConnection(*args, **kwargs)
    return samba.getchipid()


def read_flash_descriptors(*args, **kwargs):
    samba = kwargs.pop('samba', None)
    if not samba:
        samba = SamBAConnection(*args, **kwargs)
    return samba.efc_getflashdescriptor()


def read_unique_identifier(*args, **kwargs):
    samba = kwargs.pop('samba', None)
    if not samba:
        samba = SamBAConnection(*args, **kwargs)
    return samba.efc_getuid()


def _get_device_folder():
    devices_folder_candidates = [
        os.path.join(appdirs.user_config_dir('pysamloader',
                                             appauthor='Quazar Technologies',
                                             roaming=True),
                     'devices'),
        os.path.join(os.path.split(__file__)[0], 'devices')
    ]
    for candidate in devices_folder_candidates:
        if os.path.exists(candidate):
            return candidate
    else:
        raise FileNotFoundError("Devices folder not found!")


def get_device(name):
    # See : https://stackoverflow.com/a/67692/1934174
    devices_folder = _get_device_folder()
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
    return getattr(dev_mod, name)


def get_supported_devices():
    devices_folder = _get_device_folder()

    candidates = [f for f in os.listdir(devices_folder)
                  if os.path.isfile(os.path.join(devices_folder, f))
                  and not f.startswith('_')]
    _supported_devices = []
    for candidate in candidates:
        name, ext = os.path.splitext(candidate)
        if ext == '.py':
            try:
                _ = get_device(name)
                _supported_devices.append((name, "SAM-BA UART"))
            except ImportError:
                continue
    return _supported_devices


supported_devices = get_supported_devices()
