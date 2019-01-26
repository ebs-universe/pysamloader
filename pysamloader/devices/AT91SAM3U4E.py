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


from ..samdevice import SAMDevice


class AT91SAM3U4E(SAMDevice):
    EFC_FCR = '400E0804'
    EFC_FSR = '400E0808'
    AutoBaud = False
    FullErase = False
    WP_COMMAND = None
    EWP_COMMAND = '03'
    EA_COMMAND = None
    FS_ADDRESS = '00080000'
    PAGE_SIZE = 256
    SGPB_CMD = '0B'
    CGPB_CMD = '0C'
    SGP = [0, 1, 0]

    def __init__(self):
        super(AT91SAM3U4E, self).__init__()
