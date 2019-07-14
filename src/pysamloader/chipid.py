# Copyright (c) 2019 Chintalagiri Shashank
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


from bitstring import BitArray


class SamChipID(object):
    def __init__(self, cidr, exid):
        self._cidr = BitArray(cidr)
        self._exid = BitArray(exid)

    def _get_value(self, bs, be):
        return self._cidr[31-bs:32-be].uint

    @property
    def version(self):
        return self._get_value(4, 0)

    _defs_eproc = {
        1: ('ARM946ES', 'ARM946ES'),
        2: ('ARM7TDMI', 'ARM7TDMI'),
        3: ('CM3', 'Cortex-M3'),
        4: ('ARM920T', 'ARM920T'),
        5: ('ARM926EJS', 'ARM926EJS'),
        6: ('CA5', 'Cortex-A5'),
        7: ('CM4', 'Cortex-M4'),
    }

    @property
    def eproc(self):
        return self._defs_eproc[self._get_value(7, 5)]

    _defs_nvpsiz = {
        0: ('NONE', 'None'),
        1: ('8K', '8K Bytes'),
        2: ('16K', '16K Bytes'),
        3: ('32K', '32K Bytes'),
        5: ('64K', '64K Bytes'),
        7: ('128K', '128K Bytes'),
        9: ('256K', '256K Bytes'),
        10: ('512K', '512K Bytes'),
        12: ('1024K', '1024K Bytes'),
        14: ('2048K', '2048K Bytes'),
    }

    @property
    def nvpsiz(self):
        return self._defs_nvpsiz[self._get_value(11, 8)]

    @property
    def nvpsiz2(self):
        return self._defs_nvpsiz[self._get_value(15, 12)]

    _defs_sramsiz = {
        0: ('48K', '48K bytes'),
        1: ('1K', '1K bytes'),
        2: ('2K', '2K bytes'),
        3: ('6K', '6K bytes'),
        4: ('24K', '24K bytes'),
        5: ('4K', '4K bytes'),
        6: ('80K', '80K bytes'),
        7: ('160K', '160K bytes'),
        8: ('8K', '8K bytes'),
        9: ('16K', '16K bytes'),
        10: ('32K', '32K bytes'),
        11: ('64K', '64K bytes'),
        12: ('128K', '128K bytes'),
        13: ('256K', '256K bytes'),
        14: ('96K', '96K bytes'),
        15: ('512K', '512K bytes'),
    }

    @property
    def sramsiz(self):
        return self._defs_sramsiz[self._get_value(19, 16)]

    _defs_arch = {
        0x19: ('AT91SAM9xx', 'AT91SAM9xx Series'),
        0x29: ('AT91SAM9XExx', 'AT91SAM9XExx Series'),
        0x34: ('AT91x34', 'AT91x34 Series'),
        0x37: ('CAP7', 'CAP7 Series'),
        0x39: ('CAP9', 'CAP9 Series'),
        0x3B: ('CAP11', 'CAP11 Series'),
        0x40: ('AT91x40', 'AT91x40 Series'),
        0x42: ('AT91x42', 'AT91x42 Series'),
        0x55: ('AT91x55', 'AT91x55 Series'),
        0x60: ('AT91SAM7Axx', 'AT91SAM7Axx Series'),
        0x61: ('AT91SAM7AQxx', 'AT91SAM7AQxx Series'),
        0x63: ('AT91x63', 'AT91x63 Series'),
        0x70: ('AT91SAM7Sxx', 'AT91SAM7Sxx Series'),
        0x71: ('AT91SAM7XCxx', 'AT91SAM7XCxx Series'),
        0x72: ('AT91SAM7SExx', 'AT91SAM7SExx Series'),
        0x73: ('AT91SAM7Lxx', 'AT91SAM7Lxx Series'),
        0x75: ('AT91SAM7Xxx', 'AT91SAM7Xxx Series'),
        0x76: ('AT91SAM7SLxx', 'AT91SAM7SLxx Series'),
        0x80: ('SAM3UxC', 'SAM3UxC Series(100 - pin version)'),
        0x81: ('SAM3UxE', 'SAM3UxE Series(144 - pin version)'),
        0x83: ('SAM[3/4]AxC', 'SAM[3/4]AxC Series(100 - pin version)'),
        0x84: ('SAM[3/4]XxC', 'SAM[3/4]3XxC Series(100 - pin version)'),
        0x85: ('SAM[3/4]XxE', 'SAM[3/4]XxE Series(144 - pin version)'),
        0x86: ('SAM[3/4]XxG', 'SAM[3/4]XxG Series(208 / 217 - pin version)'),
        0x88: ('SAM[3/4]SxA', 'SAM[3/4]SxA Series(48 - pin version)'),
        0x89: ('SAM[3/4]SxB', 'SAM[3/4]SxB Series(64 - pin version)'),
        0x8A: ('SAM[3/4]SxC', 'SAM[3/4]SxC Series(100 - pin version)'),
        0x92: ('AT91x92', 'AT91x92 Series'),
        0x93: ('SAM3NxA', 'SAM3NxA Series(48 - pin version)'),
        0x94: ('SAM3NxB', 'SAM3NxB Series(64 - pin version)'),
        0x95: ('SAM3NxC', 'SAM3NxC Series(100 - pin version)'),
        0x99: ('SAM3SDxB', 'SAM3SDxB Series(64 - pin version)'),
        0x9A: ('SAM3SDxC', 'SAM3SDxC Series(100 - pin version)'),
        0xA5: ('SAM5A', 'SAM5A'),
        0xF0: ('AT75Cxx', 'AT75Cxx Series')
    }

    @property
    def arch(self):
        return self._defs_arch[self._get_value(27, 20)]

    _defs_nvptyp = {
        0: ('ROM', 'ROM'),
        1: ('ROMLESS', 'ROMless or on-chip Flash'),
        4: ('SRAM', 'SRAM emulating ROM'),
        2: ('FLASH', 'Embedded Flash Memory'),
        3: ('ROM_FLASH', 'ROM and Embedded Flash Memory')
    }

    @property
    def nvptyp(self):
        return self._defs_nvptyp[self._get_value(30, 28)]

    fields = [
        ('Version', 'version'),
        ('Embedded Processor', 'eproc'),
        ('Nonvolatile Program Size', 'nvpsiz'),
        ('Second Nonvolatile Program Size', 'nvpsiz2'),
        ('Internal SRAM Size', 'sramsiz'),
        ('Architecture Identifier', 'arch'),
        ('Nonvolatile Program Memory Type', 'nvptyp'),
        ('CIDR', '_cidr'),
        ('EXID', '_exid')
    ]

    def __repr__(self):
        rstr = "Chip ID : \n"
        maxlen = 0
        for tag, handle in self.fields:
            if len(tag) > maxlen:
                maxlen = len(tag)
        fmt = "{0:>" + str(maxlen + 1) + "} : {1}\n"
        for tag, handle in self.fields:
            value = getattr(self, handle)
            if isinstance(value, tuple):
                value = value[1]
            rstr += fmt.format(tag, value)
        return rstr
