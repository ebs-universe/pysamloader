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


from pysamloader.samdevice import SAMDevice


class AT91SAM7X512(SAMDevice):
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
    SGP = [0, 0, 1]

    def __init__(self):
        super(AT91SAM7X512, self).__init__()
