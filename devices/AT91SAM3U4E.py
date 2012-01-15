
class AT91SAM7X512(SAMDevice):
    EFC_FCR = '400E0804'
    EFC_FSR = '400E0808'
    AutoBaud = False
    FullErase = False
    WP_COMMAND = None
    EWP_COMMAND = '03'
    EA_COMMAND = None
    FS_ADDRESS = '00080000'
    PAGE_SIZE = 256
    def __init__(self, args):
        SAMDevice.__init__(self)
