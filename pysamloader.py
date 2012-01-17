#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Chintalagiri Shashank
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

from time import sleep
from binascii import hexlify
import serial
from xmodem import *
import argparse
import logging
import sys, os
import devices
from progressbar.progressbar import ProgressBar
try:
        from cStringIO import StringIO
except:
        from StringIO import StringIO


class SamBAConnection(object):

    ser = serial.Serial()

    def __init__(self, args):
        """ Opens the serial port for the SAM-BA connection """
        self.ser.baudrate = args.baud
        self.ser.port = args.port
        self.ser.timeout = 1
        try:
            self.ser.open()
        except:
            logging.critical("Unable to open serial port.\
                         \nCheck your connections and try again.")
            sys.exit(1)
        if self.ser.isOpen():
            self.make_connection(args)
            self.args = args
            sleep(1)

    def retrieve_response(self):
        """ Read a response from SAM-BA, delimited by > """
        char = ''
        data = ''
        while char is not '>':
            data += char
            char = self.ser.read(1)
        return data

    def make_connection(self, args):
        """ Test connection to SAM-BA by reading its version """
        if args.ab is True:
            """Auto Baud"""
            logging.info("Attempting Auto-Baud with SAM-BA")
            status = 0
            while not status:
                self.ser.write('\x80')
                self.ser.write('\x80')
                self.ser.write('#')
                sleep(0.001)
                resp = self.ser.read(1)
                if resp is '>':
                    status = 1
                    logging.info("SAM-BA Auto-Baud Successful")
        self.flush_all()
        self.ser.read(22)
        sleep(1)
        self.ser.write("V#")
        sleep(0.01)
        resp = self.retrieve_response()
        logging.info("SAM-BA Version : ")
        logging.info(resp)
        if resp:
            return
        else:
            raise Exception("SAM-BA did not respond to V#")

    def flush_all(self):
        """ Flush serial communication buffers  """
        self.ser.flushInput()
        self.ser.flushOutput()

    def write_byte(self, address, contents):
        """ 
        Write 1 byte at a specific address. 
        Both address and contents expected to be character strings
        
        """
        if self.ser.isOpen():
            self.flush_all()
            logging.debug("Writing byte at " +address+ " : " +contents)
            self.ser.write("O"+address+','+contents+'#')
            return self.retrieve_response()
        else:
            return None

    def write_hword(self, address, contents):
        """ 
        Write 2 bytes at a specific address. 
        Both address and contents expected to be character strings
        
        """
        if self.ser.isOpen():
            self.flush_all()
            logging.debug("Writing half word at " +address+ " : " +contents)
            self.ser.write("H"+address+','+contents+'#')
            return self.retrieve_response()
        else:
            return None

    def write_word(self, address, contents):
        """ 
        Write 4 bytes at a specific address. 
        Both address and contents expected to be character strings
        
        """
        if self.ser.isOpen():
            self.flush_all()
            logging.debug("Writing at " +address+ " : " +contents)
            self.ser.write("W"+address+','+contents+'#')
            sleep(0.01)
            return self.retrieve_response()
        else:
            return None

    def read_byte(self, address):
        """ 
        Read 1 byte from a specific address. 
        Both address and returned contents are character strings
        
        """
        if self.ser.isOpen():
            self.flush_all()
            msg = "o"+address+',#'
            logging.debug("Reading byte with command : "+msg)
            self.ser.write(msg)
            return self.retrieve_response().strip()
        else:
            return ''

    def read_hword(self, address):
        """ 
        Read 2 bytes from a specific address. 
        Both address and returned contents are character strings
        
        """
        pass
        if self.ser.isOpen():
            self.flush_all()
            msg = "h"+address+',#'
            logging.debug("Reading half word with command : "+msg)
            self.ser.write(msg)
            return self.retrieve_response().strip()
        else:
            return ''

    def read_word(self, address):
        """ 
        Read 4 bytes from a specific address. 
        Both address and returned contents are character strings
        
        """
        if self.ser.isOpen():
            self.flush_all()
            msg = "w"+address+',#'
            logging.debug("Reading word with command : "+msg)
            self.ser.write(msg)
            return self.retrieve_response().strip()
        else:
            return ''

    def xm_init_sf(self, address):
        """ Initialize XMODEM file send to specified address """
        if self.ser.isOpen():
            self.flush_all()
            msg = "S"+address+',#'
            logging.debug("Starting send file with command : "+ msg)
            self.ser.write(msg)
            char = ''
            while char is not 'C':
                logging.info("Waiting for CRC")
                char = self.ser.read(1)
            return

    def xm_init_rf(self, address, size):
        """ Initialize XMODEM file read from specified address """
        pass

    def xm_getc(self, size, timeout=1):
        """ getc function for the xmodem protocol """
        return self.ser.read(size)

    def xm_putc(self, data, timeout=1):
        """ putc function for the xmodem protocol """
        self.ser.write(data)
        return len(data)

    def efc_wready(self):
        """ Wait for EFC to report ready """
        status = self.efc_rstat()
        while not status:
            sleep(0.01)
            status = self.efc_rstat()
        return

    def efc_ewp(self, pno):
        """ EFC trigger write page. Pno is an integer """
        self.write_word(self.args.EFC_FCR, '5A'+hex(pno)[2:].zfill(4)+self.args.WPC)
        pass

    def efc_rstat(self):
        """ 
        Read EFC status. 
        Returns True if EFC is ready, False if busy. 
        
        """
        efstatus = self.read_word(self.args.EFC_FSR)
        logging.debug("EFC Status : "+ efstatus[8:])
        return (efstatus[9:] == "1")

    def efc_cleargpnvm(self, bno):
        """
        EFC Fucntion to clear specified GPNVM bit.
        bno is an integer

        """
        if self.ser.isOpen():
            self.efc_wready()
            self.write_word(self.args.EFC_FCR, '5A'+hex(bno)[2:].zfill(4)+self.args.CGPB_CMD)
            self.efc_wready()

    def efc_setgpnvm(self, bno):
        """
        EFC Fucntion to set specified GPNVM bit.
        bno is an integer

        """
        if self.ser.isOpen():
            self.efc_wready()
            self.write_word(self.args.EFC_FCR, '5A'+hex(bno)[2:].zfill(4)+self.args.SGPB_CMD)
            self.efc_wready()
        return

    def efc_eraseall(self):
        """ EFC Function to Erase All """
        if self.ser.isOpen():
            self.efc_wready()
            self.write_word(self.args.EFC_FCR, '5A0000'+self.args.EA_COMMAND)
            self.efc_wready()

def raw_sendf(args, samba):
    """ Function to burn file onto flash without using XMODEM transfers """
    stat = 1
    if args.ea is True:
        samba.efc_eraseall()
    pno = args.spno
    binf = open(args.filename, "r")
    npages = int((os.fstat(binf.fileno())[6]+128)/256)
    p = ProgressBar('red', block='▣', empty='□')
    while stat:
        p.render(pno*100/npages, "Page %s of %s\nWriting to Flash" % (pno, npages))
        samba.efc_wready()
        padr = int(args.saddress, 16)+(pno*args.psize)
        logging.debug("Start Address of page " + str(pno) + " : " + hex(padr))
        stat = raw_process_page(args, samba, padr, binf)
        samba.efc_ewp(pno)
        logging.debug("Page done - "+str(pno))
        pno = pno + 1
    if args.g is True:
        logging.info("Setting GPNVM bit to run from flash")
        for i in range(3):
            if args.SGP[i] == 1:
                samba.efc_setgpnvm(i)
            else:
                samba.efc_cleargpnvm(i)
    else:
        logging.warning("Not setting GPNVM bit.")
        logging.warning("Invoke with -g to have that happen.")

def xmodem_sendf(args, samba):
    """ 
    Function to burn file onto flash using XMODEM transfers 
    This does not work on the AT91SAM3U4E, atleast.

    """
    stat = 1
    pno = args.spno
    while stat:
        samba.efc_wready()
        adr = int(args.saddress, 16)+pno*args.psize
        adrstr = hex(adr)[2:].zfill(8)
        logging.info("Start Address of page " + str(pno) + " : " + adrstr)
        samba.xm_init_sf(adrstr)
        stat = xm_process_page(args, samba)
        samba.efc_ewp(pno)
        logging.info("Page done - " + str(pno))
        pno = pno + 1
    if args.g is True:
        logging.info("Setting GPNVM bit to run from flash")
        samba.efc_setgpnvm(1)
    else:
        logging.warning("Not setting GPNVM bit.")
        logging.warning("Invoke with -g to have that happen.")

def xm_process_page(args, samba):
    """
    Send a single page worth of data from the file to the chip.
    Returns 1 as long as data remains.
    Returns 0 when end of file is reached.
    Uses XMODEM. Does not work on AT91SAM3U4E.

    """
    data = args.filename.read(args.psize)
    if len(data) == args.psize:
        status = 1
    else:
        if len(data) < args.psize:
            data += "\255"*(args.psize-len(data))
        status = 0
    logging.debug(len(data))
    logging.debug('Sending file chunk : \n'+ hexlify(data)+ ' CEND\n')
    sendbuf = StringIO(data)
    modem = XMODEM(samba.xm_getc, samba.xm_putc)
    modem.send(sendbuf, quiet=1)
    sendbuf.close()
    return status

def raw_process_page(args, samba, padr, binf):
    """
    Send a single page worth of data from the file to the chip.
    Returns 1 as long as data remains.
    Returns 0 when end of file is reached.

    """
    data = binf.read(args.psize)
    if len(data) == args.psize:
        status = 1
    else:
        if len(data) < args.psize:
            data += "\0xFF"*(args.psize-len(data))
        status = 0
    logging.debug(len(data))
    logging.debug('Sending file chunk : \n' + hexlify(data) + 'CEND\n')
    for i in range(0, 256, 4):
        wbytes = "".join(byte for byte in reversed(data[i:i+4]))
        adrstr = hex(padr+i)[2:].zfill(8)
        samba.write_word(adrstr, hexlify(wbytes))
    return status

def verify(args, samba):
    """
    Verify the contents of flash against the contents of the file.
    Returns the total number of words with errors. 

    """
    binf = open(args.filename, "r")
    nbytes = os.fstat(binf.fileno())[6]
    p = ProgressBar('green', block='▣', empty='□')
    errors = 0
    address = int(args.saddress, 16) + (args.spno * args.psize)
    rbytes = binf.read(4)
    bytes = "".join(byte for byte in reversed(rbytes))
    progbyte = 0
    while rbytes:
        rval = samba.read_word(hex(address)[2:].zfill(8))
        if not rval.upper()[2:] == hexlify(bytes).upper():
            logging.error("Verification Failed at " +
                           hex(address) + "-" + rval +' '+ hexlify(bytes))
            errors = errors + 1
        else:
            logging.debug("Verfied Word at " +
                          hex(address)+ "-" + rval + ' ' + hexlify(bytes))
        address = address + 4
        rbytes = binf.read(4)
        bytes = "".join(byte for byte in reversed(rbytes))
        progbyte = progbyte + 4
        p.render(progbyte*100/nbytes,
                "%s of %s Bytes\nVerifying Flash" % (progbyte, nbytes))
    logging.info ("Verification Complete. Words with Errors : " + str(errors))
    return errors

def main():
    parser = argparse.ArgumentParser(description="\
            Send a program to an Atmel SAM chip using SAM-BA over UART")
    parser.add_argument('-m', action='store_true',
                        help="Manual Configuration. Overrides Device Configs")
    parser.add_argument('-ea', action='store_true',
                        help="Erase All instead of page by page. Set by Device")
    parser.add_argument('-g', action='store_true',
                        help="Set GPNVM bit when done writing")
    parser.add_argument('-v', action='store_true',
                        help="Verbose debug information")
    parser.add_argument('-c', action='store_true',
                        help="Verify Only. Do not write")
    parser.add_argument('filename', metavar='file',
                        help="Binary file to be burnt into the chip")
    parser.add_argument('--port', metavar='port',
                        default="/dev/ttyUSB0",
                        help="Port on which SAM-BA is listening. Default /dev/ttyUSB0")
    parser.add_argument('--baud', metavar='baud',
                        type=int, default=115200,
                        help="Baud rate of serial communication. Default 115200")
    parser.add_argument('--device', metavar='device',
                        default='AT91SAM3U4E',
                        help="ARM Device. Default AT91SAM3U4E")
    parser.add_argument('--csize', metavar='csize',
                        type=int, default=128,
                        help="XMODEM transmission packet size. Default 128.")
    parser.add_argument('--psize', metavar='psize',
                        type=int, default=256,
                        help="Size of ARM flash pages. Default 256 (bytes). Set by device.")
    parser.add_argument('--spno', metavar='spno',
                        type=int, default=0,
                        help="Start flash page number. Default 0")
    parser.add_argument('--saddress', metavar='saddress',
                        default='00080000',
                        help="Start address of flash plane. Default 00080000. Set by device.")
    args = parser.parse_args()
    if args.v:
        logging.basicConfig(format='%(levelname)s:%(message)s',
                            level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s',
                            level=logging.INFO)
        logging.debug("Device : " + args.device)
    if not args.m:
        if args.device == 'AT91SAM7X512':
            from devices.AT91SAM7X512 import AT91SAM7X512
            dev = AT91SAM7X512

        elif args.device == 'AT91SAM3U4E':
            from devices.AT91SAM3U4E import AT91SAM3U4E
            dev = AT91SAM3U4E

        else:
            from devices.samdevice import SAMDevice
            dev = SAMDevice
            logging.warning("Device is not supported")

        if dev.AutoBaud is True:
            args.ab = True
        if dev.FullErase is True:
            args.ea = True
            args.WPC = dev.WP_COMMAND
            args.EA_COMMAND = dev.EA_COMMAND
        else:
            args.WPC = dev.EWP_COMMAND
        args.EFC_FSR = dev.EFC_FSR
        args.EFC_FCR = dev.EFC_FCR
        args.SGPB_CMD = dev.SGPB_CMD
        args.CGPB_CMD = dev.CGPB_CMD
        args.saddress = dev.FS_ADDRESS
        args.psize = dev.PAGE_SIZE
        args.SGP = dev.SGP

    samba = SamBAConnection(args)
    if args.c is False:
        raw_sendf(args, samba)
    samba.make_connection(args)
    errors = verify(args, samba)

if __name__ == "__main__":
    main()
