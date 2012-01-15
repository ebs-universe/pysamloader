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

class AT91SAM7X512(object):
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
        pass
