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
import sys
from time import sleep
from serial import Serial

from .samdevice import SAMDevice

logger = logging.getLogger('samba')


class SamBAConnection(object):

    ser = Serial()

    def __init__(self, port='/dev/ttyUSB1', baud=115200, device=None):
        """ Opens the serial port for the SAM-BA connection """
        self.ser.baudrate = baud
        self.ser.port = port
        self.ser.timeout = 1
        try:
            self.ser.open()
        except:
            logger.critical("Unable to open serial port.\
                            \nCheck your connections and try again.")
            sys.exit(1)
        if not device:
            self._device = SAMDevice()
        else:
            self._device = device()
        if self.ser.isOpen():
            self.make_connection(auto_baud=self._device.AutoBaud)
            sleep(1)

    def retrieve_response(self):
        """ Read a response from SAM-BA, delimited by > """
        char = ''
        data = ''
        while char != '>':
            data += char
            char = self.ser.read(1).decode()
        logger.debug("Got response : {0}".format(data.strip()))
        return data

    def make_connection(self, auto_baud=False):
        """ Test connection to SAM-BA by reading its version """
        logger.debug("Connecting to SAM-BA on {0} at {1}".format(
            self.ser.port, self.ser.baudrate))
        if auto_baud is True:
            """Auto Baud"""
            logger.info("Attempting Auto-Baud with SAM-BA")
            status = 0
            while not status:
                self.ser.write('\x80')
                self.ser.write('\x80')
                self.ser.write('#')
                sleep(0.001)
                resp = self.ser.read(1).decode()
                if resp is '>':
                    status = 1
                    logger.info("SAM-BA Auto-Baud Successful")
        self.flush_all()
        self.ser.read(22).decode()
        sleep(1)
        self.write_message("V#")
        sleep(0.01)
        resp = self.retrieve_response()
        logger.info("SAM-BA Version : ")
        logger.info(resp.strip())
        if resp:
            return
        else:
            raise Exception("SAM-BA did not respond to V#")

    def flush_all(self):
        """ Flush serial communication buffers  """
        self.ser.flushInput()
        self.ser.flushOutput()

    def write_message(self, msg):
        if self.ser.isOpen():
            self.flush_all()
            logger.debug("Writing to device : {0}".format(msg.encode()))
            self.ser.write(msg.encode())
            return
        else:
            raise IOError("Serial port does not seem to be open!")

    def write_byte(self, address, contents):
        """
        Write 1 byte at a specific address.
        Both address and contents expected to be character strings

        """
        self.flush_all()
        logger.debug("Writing byte at {0} : {1}"
                     "".format(address, contents))
        self.write_message("O{0},{1}#".format(address, contents))
        return self.retrieve_response()

    def write_hword(self, address, contents):
        """
        Write 2 bytes at a specific address.
        Both address and contents expected to be character strings

        """
        self.flush_all()
        logger.debug("Writing half word at {0} : {1}"
                     "".format(address, contents))
        self.write_message("H{0},{1}#".format(address, contents))
        return self.retrieve_response()

    def write_word(self, address, contents):
        """
        Write 4 bytes at a specific address.
        Both address and contents expected to be character strings

        """
        self.flush_all()
        logger.debug("Writing word at {0} : {1}"
                     "".format(address, contents))
        self.write_message("W{0},{1}#".format(address, contents))
        return self.retrieve_response()

    def read_byte(self, address):
        """
        Read 1 byte from a specific address.
        Both address and returned contents are character strings

        """
        self.flush_all()
        msg = "o{0},#".format(address)
        logger.debug("Reading byte with command : {0}".format(msg))
        self.write_message(msg)
        return self.retrieve_response().strip()

    def read_hword(self, address):
        """
        Read 2 bytes from a specific address.
        Both address and returned contents are character strings

        """
        self.flush_all()
        msg = "h{0},#".format(address)
        logger.debug("Reading half word with command : {0}".format(msg))
        self.write_message(msg)
        return self.retrieve_response().strip()

    def read_word(self, address):
        """
        Read 4 bytes from a specific address.
        Both address and returned contents are character strings

        """
        self.flush_all()
        msg = "w{0},#".format(address)
        logger.debug("Reading word with command : {0}".format(msg))
        self.write_message(msg)
        return self.retrieve_response()

    def xm_init_sf(self, address):
        """ Initialize XMODEM file send to specified address """
        self.flush_all()
        msg = "S{0},#".format(address)
        logger.debug("Starting send file with command : {0}".format(msg))
        self.write_message(msg)
        # char = ''
        # while char is not 'C':
        #     logger.info("Waiting for CRC")
        #     char = self.ser.read(1).decode()
        return

    def xm_init_rf(self, address, size):
        """ Initialize XMODEM file read from specified address """
        pass

    def xm_getc(self, size, timeout=1):
        """ getc function for the xmodem protocol """
        return self.ser.read(size).decode()

    def xm_putc(self, data, timeout=1):
        """ putc function for the xmodem protocol """
        self.ser.write(data.encode())
        return len(data)

    def efc_wready(self):
        """ Wait for EFC to report ready """
        status = self.efc_rstat()
        while not status:
            logger.debug("Waiting for EFC")
            sleep(0.01)
            status = self.efc_rstat()
        return

    def efc_ewp(self, pno):
        """ EFC trigger write page. Pno is an integer """
        self.write_word(self._device.EFC_FCR,
                        '5A{0}{1}'.format(
                            hex(pno)[2:].zfill(4),
                            self._device.WPC
                        ))

    def efc_rstat(self):
        """
        Read EFC status.
        Returns True if EFC is ready, False if busy.

        """
        efc_status = self.read_word(self._device.EFC_FSR).strip()
        logger.debug("EFC Status : {0}".format(efc_status))
        return efc_status[9] == "1"

    def efc_cleargpnvm(self, bno):
        """
        EFC Fucntion to clear specified GPNVM bit.
        bno is an integer

        """
        self.efc_wready()
        self.write_word(self._device.EFC_FCR,
                        '5A{0}{1}'.format(
                            hex(bno)[2:].zfill(4),
                            self._device.CGPB_CMD
                        ))
        self.efc_wready()

    def efc_setgpnvm(self, bno):
        """
        EFC Fucntion to set specified GPNVM bit.
        bno is an integer

        """
        self.efc_wready()
        self.write_word(self._device.EFC_FCR,
                        '5A{0}{1}'.format(
                            hex(bno)[2:].zfill(4),
                            self._device.SGPB_CMD
                        ))
        self.efc_wready()
        return

    def efc_eraseall(self):
        """ EFC Function to Erase All """
        self.efc_wready()
        self.write_word(self._device.EFC_FCR,
                        '5A0000{0}'.format(self._device.EAC))
        self.efc_wready()
