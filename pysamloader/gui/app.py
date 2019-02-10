
import os
os.environ['SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR'] = '0'

import kivy
kivy.require('1.10.1')  # replace with your current kivy version !

from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')

from kivy.core.window import Window
from kivy.app import App

from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout

from serial.tools import list_ports
from pysamloader import __version__
from pysamloader.pysamloader import get_supported_devices
from pysamloader.pysamloader import get_device
from pysamloader.pysamloader import read_chipid
from pysamloader.pysamloader import read_unique_identifier
from pysamloader.pysamloader import write
from pysamloader.pysamloader import verify
from pysamloader.pysamloader import set_boot
from pysamloader.samba import SamBAConnection
from pysamloader.samba import SamBAConnectionError

from .widgets import DropHandler
from .widgets import ColorBoxLayout
from .widgets import MessageBox
from .widgets import SpinnerOptionCard
from .widgets import FileOptionCard
from pysamloader.terminal import ProgressBar


class FirmwareLoader(App, DropHandler):
    _color1 = (226.0/255, 225.0/255, 224.0/255, 255.0/255)
    _color2 = (170.0/255, 169.0/255, 168.0/255, 255.0/255)
    _tcolor = (0.1, 0.1, 0.1, 1)

    def __init__(self, **kwargs):
        self._root = None
        self._footer = None
        self._footer_structure = None
        self._content = None
        DropHandler.__init__(self)
        super(FirmwareLoader, self).__init__(**kwargs)

    def _build_footer(self):
        self._footer = AnchorLayout(anchor_y='bottom', anchor_x='center')
        self._footer_structure = ColorBoxLayout(bgcolor=self._color1,
                                                orientation='horizontal',
                                                size_hint_y=0.15)
        self._footer_structure.add_widget(
            Image(source='pysamloader/assets/logo-full.png'))
        self._footer_structure.add_widget(
            Label(text='[b]pysamloader[/b]\n[size=12]v{0}[/size]'.format(__version__),
                  halign='right', markup=True, color=self._tcolor))
        self._footer.add_widget(self._footer_structure)
        self._root.add_widget(self._footer)

    def _device_options(self):
        return (d[0] for d in get_supported_devices())

    def _device_infomsg(self):
        return "{0}\n[size=10]UID: {1}[/size]" \
               "".format(self._device_card.selected, self._uid)

    def _device_extended_info(self):
        _root = BoxLayout(orientation='vertical', padding=10, spacing=10)
        _table = GridLayout(cols=2, spacing=(10, 5))

        def _set_height(*args):
            _table.height = args[1]
        _table.bind(minimum_height=_set_height)

        for tag, handle in self._chipid.fields:
            tag_label = Label(text=tag, font_size='11sp',
                              halign='right', valign='middle')
            tag_label.bind(size=tag_label.setter('text_size'))
            _table.add_widget(tag_label)

            value = getattr(self._chipid, handle)
            if isinstance(value, tuple):
                value = value[1]
            value_label = Label(text=str(value), font_size='11sp',
                                halign='left', valign='middle')
            value_label.bind(size=value_label.setter('text_size'))
            _table.add_widget(value_label)

        _root.add_widget(_table)
        return "ChipID MCU Information", _root

    def _port_options(self):
        return (x.device for x in list_ports.comports())

    def _port_infomsg(self):
        p = list(list_ports.grep(self._port_card.selected))[0]
        return "{0}\n[size=10]{1} {2} {3}[/size]" \
               "".format(self._port_card.selected, str(p.manufacturer),
                         str(p.product), str(p.serial_number))

    def _binary_infomsg(self):
        return "{0}\n[size=10]{1} bytes[/size]" \
               "".format(
                    os.path.split(self._file_card.selected)[1],
                    os.path.getsize(self._file_card.selected))

    def _binary_extended_info(self):
        _root = BoxLayout(orientation='vertical', padding=10, spacing=10)
        path_label = Label(text=self._file_card.selected, font_size='11sp',
                           valign='middle')
        path_label.bind(size=path_label.setter('text_size'))
        _root.add_widget(path_label)
        return "Binary File Information", _root

    def _write_flash(self, _):
        self._content.remove_widget(self._write_button)
        write(self._samba, self._device, self._file_card.selected, progress_class=ProgressBar)

    def _make_connection(self, _):
        self._connect_button.text = 'Connecting ...'
        try:
            self._device = get_device(self._device_card.selected)
        except FileNotFoundError as e:
            popup = MessageBox(
                title="Device Not Supported",
                msg="Did not find a supported device selected. Make sure you have "
                    "selected a valid device. If you have, check your installation.")
            self._connect_button.text = 'Test Connection'
            popup.open()
            return
        try:
            self._samba = SamBAConnection(port=self._port_card.selected, device=self._device)
        except SamBAConnectionError as e:
            popup = MessageBox(
                title='SAM-BA Connection Error',
                msg="Got the following error when trying to connect "
                    "to SAM-BA : \n{0}".format(e.msg))
            self._connect_button.text = 'Test Connection'
            popup.open()
            return

        self._connect_button.text = "Reading ChipID ..."
        self._chipid = read_chipid(samba=self._samba)

        self._connect_button.text = "Reading UID ..."
        self._uid = read_unique_identifier(samba=self._samba)

        self._device_card.lock()
        self._port_card.lock()

        self._content.remove_widget(self._connect_button)

        self._file_card = FileOptionCard(
            msg="Select Binary File", icon='pysamloader/assets/binary.png',
            info_msg=self._binary_infomsg,
            extended_info=self._binary_extended_info
        )
        self._content.add_widget(self._file_card)

        self._write_button = Button(text="Write to Flash",
                                    size_hint=(1, 0.1))
        self._write_button.bind(on_release=self._write_flash)
        self._content.add_widget(self._write_button)

    def _build_content(self):
        self._content = StackLayout(orientation='tb-lr',
                                    padding=(10, 10),
                                    spacing=(10, 10))

        self._device_card = SpinnerOptionCard(
            msg="Select Device", options=self._device_options,
            icon='pysamloader/assets/sam-ic.png',
            info_msg=self._device_infomsg,
            extended_info=self._device_extended_info
        )
        self._content.add_widget(self._device_card)

        self._port_card = SpinnerOptionCard(
            msg="Select Port", options=self._port_options,
            icon='pysamloader/assets/connectors.png',
            info_msg=self._port_infomsg)
        self._content.add_widget(self._port_card)

        self._connect_button = Button(text="Test Connection",
                                      size_hint=(1, 0.1))
        self._connect_button.bind(on_release=self._make_connection)
        self._content.add_widget(self._connect_button)

        self._root.add_widget(self._content)

    def build(self):
        Window.clearcolor = self._color2
        DropHandler.build(self)
        self._root = FloatLayout()
        self._build_content()
        self._build_footer()
        return self._root


def main():
    FirmwareLoader().run()


if __name__ == '__main__':
    main()
