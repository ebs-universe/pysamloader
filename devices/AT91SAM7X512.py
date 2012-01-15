
class AT91SAM7X512(object):
    EFC_FCR = 'FFFFFF64'
    EFC_FSR = 'FFFFFF68'
    AutoBaud = True
    FullErase = True
    WP_COMMAND = '01'
    EWP_COMMAND = None
    EA_COMMAND = '08'
    FS_ADDRESS = '00100000'
    PAGE_SIZE = 256
    SGPB_CMD = '0B'
    CGPB_CMD = '0D'
    def __init__(self, args):
        pass
