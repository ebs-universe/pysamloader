from time import sleep
from binascii import hexlify
import serial
from xmodem import *
import argparse
import logging
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
            print "Unable to open serial port.\
                   \nCheck your connections and try again."
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
            print "Writing at " +address+ " : " +contents
            self.ser.write("W"+address+','+contents+'#')
            return self.retrieve_response()
        else:
            return None

    def read_word(self, address):
        if self.ser.isOpen():
            self.flush_all()
            msg = "w"+address+',#'
            print msg
            self.ser.write(msg)
            sleep(1)
            return self.retrieve_response().strip()
        else:
            return ''

    def xm_init_sf(self, address):
        if self.ser.isOpen():
            self.flush_all()
            msg = "S"+address+',#'
            print msg
            self.ser.write(msg)
            char = ''
            while char is not 'C':
                print "Waiting for CRC"
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
        print efstatus[8:]
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
        print "Start Address of page " + str(pno) + " : " + adrstr
        samba.xm_init_sf(adrstr)
        stat = process_page(args, samba)
        samba.efc_ewp(pno)
        print "Page done - " + str(pno)
        pno = pno + 1
    if args.g is True:
        print "Setting GPNVM bit to run from flash"
        samba.efc_setgpnvm(1)
    else:
        print "Not setting GPNVM bit. Invoke with -g to have that happen."

def process_page(args, samba):
    data = args.filename.read(args.psize)
    if len(data) == args.psize:
        status = 1
    else:
        print len(data)
        if len(data) < args.psize:
            data += "\255"*(args.psize-len(data))
        status = 0
    print len(data)
    print hexlify(data) + ' CEND\n'
    sendbuf = StringIO(data)
    modem = XMODEM(samba.xm_getc, samba.xm_putc)
    modem.send(sendbuf, quiet=1)
    sendbuf.close()
    return status

def main():
    parser = argparse.ArgumentParser(description="\
            Send a program to an Atmel SAM chip using SAM-BA over UART")
    parser.add_argument('-g', action='store_true',
                        help="Set GPNVM bit when done writing")
    parser.add_argument('filename', metavar='file',
                        type=file,
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
    samba = SamBAConnection(args)
    #print(samba.read_word('400E0800'))
    xmodem_sendf(args, samba)

if __name__ == "__main__":
    logging.basicConfig()
    main()
