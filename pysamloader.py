#!/usr/bin/python

from time import sleep
from binascii import hexlify
import serial
from xmodem import *
import argparse
import logging
import sys
try:
        from cStringIO import StringIO
except:
        from StringIO import StringIO


class SamBAConnection(object):

    ser = serial.Serial()

    def __init__(self, args):
        self.ser.baudrate = args.baud
        self.ser.port = args.port
        self.ser.timeout = 5
        try:
            self.ser.open()
        except:
            logging.error("Unable to open serial port.\
                         \nCheck your connections and try again.")
            sys.exit(1)
        if self.ser.isOpen():
            self.make_connection()
            self.args = args
            sleep(1)

    def retrieve_response(self):
        char = ''
        data = ''
        while char is not '>':
            data += char
            char = self.ser.read(1)
        return data

    def make_connection(self):
        self.ser.write("V#")
        print self.retrieve_response()

    def flush_all(self):
        self.ser.flushInput()
        self.ser.flushOutput()

    def write_word(self, address, contents):
        if self.ser.isOpen():
            self.flush_all()
            logging.debug("Writing at " +address+ " : " +contents)
            self.ser.write("W"+address+','+contents+'#')
            return self.retrieve_response()
        else:
            return None

    def read_word(self, address):
        if self.ser.isOpen():
            self.flush_all()
            msg = "w"+address+',#'
            logging.debug("Reading word with command : "+msg)
            self.ser.write(msg)
            return self.retrieve_response().strip()
        else:
            return ''

    def xm_init_sf(self, address):
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
        pass

    def xm_getc(self, size, timeout=1):
        return self.ser.read(size)

    def xm_putc(self, data, timeout=1):
        self.ser.write(data)
        return len(data)

    def efc_ewp(self, pno):
        self.write_word('400E0804', '5A'+hex(pno)[2:].zfill(4)+'03')
        pass

    def efc_rstat(self):
        efstatus = self.read_word('400E0808')
        logging.debug("EFC Status : "+ efstatus[8:])
        return (efstatus[8:] == "01")

    def efc_setgpnvm(self, bno):
        if self.ser.isOpen():
            status = self.efc_rstat()
            while not status:
                sleep(0.01)
                status = self.efc_rstat()
            self.write_word('400E0804', '5A'+hex(bno)[2:].zfill(4)+'0B')
            status = self.efc_rstat()
            while not status:
                sleep(0.01)
                status = self.efc_rstat()
        return

def raw_sendf(args, samba):
    stat = 1
    pno = args.spno
    binf = open(args.filename, "r")
    while stat:
        status = samba.efc_rstat()
        while not status:
            sleep(0.01)
            status = samba.efc_rstat()

        padr = int(args.saddress, 16)+(pno*args.psize)
        logging.debug("Start Address of page " + str(pno) + " : " + hex(padr))
        stat = raw_process_page(args, samba, padr, binf)
        samba.efc_ewp(pno)
        logging.info("Page done - "+str(pno))
        pno = pno + 1
    if args.g is True:
        logging.info("Setting GPNVM bit to run from flash")
        samba.efc_setgpnvm(1)
    else:
        logging.warning("Not setting GPNVM bit.\
                         \nInvoke with -g to have that happen.")

def xmodem_sendf(args, samba):
    stat = 1
    pno = args.spno
    while stat:
        status = samba.efc_rstat()
        while not status:
            sleep(0.01)
            status = samba.efc_rstat()
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
        logging.warning("Not setting GPNVM bit.\
                         \nInvoke with -g to have that happen.")

def xm_process_page(args, samba):
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
    data = binf.read(args.psize)
    if len(data) == args.psize:
        status = 1
    else:
        if len(data) < args.psize:
            data += "\255"*(args.psize-len(data))
        status = 0
    logging.debug(len(data))
    logging.debug('Sending file chunk : \n' + hexlify(data) + 'CEND\n')
    for i in range(0, 256, 4):
        adrstr = hex(padr+i)[2:].zfill(8)
        samba.write_word(adrstr, hexlify(data[i:i+4]))
    return status

def verify(args, samba): 
    binf = open(args.filename, "r")
    errors = 0
    address = int(args.saddress, 16) + (args.spno * args.psize)
    bytes = binf.read(4)
    while bytes:
        rval = samba.read_word(hex(address)[2:].zfill(8))
        if not rval.upper()[2:] == hexlify(bytes).upper():
            logging.warning("Verification Failed at "+hex(address) + "-" + rval +' '+ hexlify(bytes))
            errors = errors + 1
        else:
            logging.debug("Verfied Word at "+ hex(address)+ "-" + rval + ' ' + hexlify(bytes))
        address = address + 4
        bytes = binf.read(4)
    logging.info ("Verification Complete. Words with Errors : " + str(errors))

def main():
    parser = argparse.ArgumentParser(description="\
            Send a program to an Atmel SAM chip using SAM-BA over UART")
    parser.add_argument('-g', action='store_true',
                        help="Set GPNVM bit when done writing")
    parser.add_argument('-v', action='store_true',
                        help="Verbose debug information")
    parser.add_argument('-c', action='store_true',
                        help="Verify Only")
    parser.add_argument('filename', metavar='file',
                        help="File to be send to the chip")
    parser.add_argument('--port', metavar='port',
                        default="/dev/ttyUSB0",
                        help="Port on which SAM-BA is listening")
    parser.add_argument('--baud', metavar='baut',
                        type=int, default=115200,
                        help="Baud rate of serial communication")
    parser.add_argument('--csize', metavar='csize',
                        type=int, default=128,
                        help="Size of the chucks used for xmodem transmission")
    parser.add_argument('--psize', metavar='psize',
                        type=int, default=256,
                        help="Size of a page to be written to at once")
    parser.add_argument('--spno', metavar='spno',
                        type=int, default=0,
                        help="Start flash page number")
    parser.add_argument('--saddress', metavar='saddress',
                        default='00080000',
                        help="Start address of flash plane")
    args = parser.parse_args()
    if args.v:
        logging.basicConfig(format='%(levelname)s:%(message)s',
                            level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s',
                            level=logging.INFO)
    samba = SamBAConnection(args)
    if args.c is False:
        raw_sendf(args, samba)
    samba.make_connection()
    errors = verify(args, samba)

if __name__ == "__main__":
    main()
