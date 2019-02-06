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


class EFCFlashDescriptor(object):
    def __init__(self, samba):
        self._samba = samba
        self.id = samba.efc_readfrr()
        self.size = self._read_number()
        self.page_size = self._read_number()

        self.plane_count = self._read_number()
        self.planes = {}
        for plane in range(self.plane_count):
            self.planes[plane] = self._read_number()

        self.lock_count = self._read_number()
        self.locks = {}
        for lock in range(self.lock_count):
            self.locks[lock] = self._read_number()

    def _read_number(self):
        return int(self._samba.efc_readfrr().strip(), 0)

    def __repr__(self):
        rstr = "Flash Descriptor : \n"
        rstr += "                 ID : {0}\n".format(self.id.strip())
        rstr += "               Size : {0} bytes\n".format(self.size)
        rstr += "          Page Size : {0} bytes\n".format(self.page_size)

        rstr += "       No of Planes : {0}\n".format(self.plane_count)
        for plane in range(self.plane_count):
            rstr += "       Plane {0} Size : {1} bytes\n" \
                    "".format(plane, self.planes[plane])

        rstr += "    No of Lock Bits : {0}\n".format(self.lock_count)
        for lock in range(self.lock_count):
            rstr += "Lock Region {0:>2} Size : {1} bytes\n" \
                    "".format(lock, self.locks[lock])
        return rstr
