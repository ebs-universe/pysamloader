

import os
import re
from itertools import chain

from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.filechooser import FileChooserListView

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.properties import ListProperty
from kivy.properties import NumericProperty
from kivy.graphics.texture import Texture
from kivy.animation import Animation

from kivy.graphics.opengl import glGetIntegerv
from kivy.graphics.opengl import GL_MAX_TEXTURE_SIZE
_image_max_size = glGetIntegerv(GL_MAX_TEXTURE_SIZE)[0]


class BackgroundColorMixin(object):
    bgcolor = ListProperty([1, 1, 1, 1])

    def __init__(self, bgcolor=None):
        self.bgcolor = bgcolor or [1, 1, 1, 1]
        self._render_bg()
        self.bind(size=self._render_bg, pos=self._render_bg)
        self.bind(bgcolor=self._render_bg)

    def _render_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bgcolor)
            Rectangle(pos=self.pos, size=self.size)


class ColorLabel(BackgroundColorMixin, Label):
    def __init__(self, **kwargs):
        bgcolor = kwargs.pop('bgcolor')
        Label.__init__(self, **kwargs)
        BackgroundColorMixin.__init__(self, bgcolor=bgcolor)


class ColorBoxLayout(BackgroundColorMixin, BoxLayout):
    def __init__(self, **kwargs):
        bgcolor = kwargs.pop('bgcolor')
        BoxLayout.__init__(self, **kwargs)
        BackgroundColorMixin.__init__(self, bgcolor=bgcolor)


class MarqueeLabel(ScrollView):
    spacer_width = NumericProperty(None)

    def __init__(self, **kwargs):
        bgcolor = kwargs.pop('bgcolor')
        ScrollView.__init__(self, bar_width=0)

        self._layout = ColorBoxLayout(size_hint_x=None,
                                      bgcolor=bgcolor,
                                      orientation='horizontal')
        self._mainlabels = []
        self._lspacer = Widget(size_hint_x=None, width=Window.width)
        self._rspacer = Widget(size_hint_x=None, width=Window.width)
        self.add_widget(self._layout)

        text = kwargs.pop('text')
        self._label_params = kwargs
        self.text = text

    def update_widths(self):
        width = self._lspacer.width + \
                self._rspacer.width + \
                sum([x.width for x in self._mainlabels])
        self._layout.width = width
        self.width = width

    def _set_spacer_width(self, _, size):
        self._lspacer.width = size[0]
        self._rspacer.width = size[0]
        self.update_widths()

    def on_parent(self, _, parent):
        if parent:
            parent.bind(size=self._set_spacer_width)

    @property
    def text(self):
        return ' '.join([x.text for x in self._mainlabels])

    def _set_mainlabel_width(self, l, size):
        l.width = size[0]
        self.update_widths()

    @text.setter
    def text(self, value):
        self.remove_widget(self._layout)

        texts = split_string(value, 64)
        self._layout.clear_widgets()
        self._layout.add_widget(self._lspacer)

        self._mainlabels = []
        for t in texts:
            l = Label(text=t, size_hint_x=None,
                      text_size=(None, None), **self._label_params)
            self._layout.add_widget(l)
            l.bind(texture_size=self._set_mainlabel_width)
            l.texture_update()
            self._mainlabels.append(l)

        self._layout.add_widget(self._rspacer)
        self.add_widget(self._layout)
        self.update_widths()

    def start(self, loop=True):
        speed = 75
        scroll_distance = self._layout.width - self._lspacer.width
        duration = scroll_distance / speed
        # print("Scroll was", self.scroll_x)
        self.scroll_x = 0
        # print("Using duration", duration)
        self._animation = Animation(scroll_x=1, duration=duration)
        if loop:
            self._animation.bind(on_complete=self._check_complete)
            pass
        self._animation.start(self)

    def _check_complete(self, animation, instance):
        # print(instance.scroll_x)
        # print(self._mainlabels[-1].x + self._mainlabels[-1].width)
        if instance.scroll_x > 0.95:
            # print("Repeating")
            self._animation.unbind(on_scroll=self._check_complete)
            animation.stop(self)
            self.start()

    def stop(self):
        self._animation.unbind(on_scroll=self._check_complete)
        self._animation.stop(self)
        self.clear_widgets()


class Gradient(object):

    @staticmethod
    def horizontal(*args):
        texture = Texture.create(size=(len(args), 1), colorfmt='rgba')
        buf = bytes([int(v * 255) for v in chain(*args)])  # flattens
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture

    @staticmethod
    def vertical(*args):
        texture = Texture.create(size=(1, len(args)), colorfmt='rgba')
        buf = bytes([int(v * 255) for v in chain(*args)])  # flattens
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture


def color_set_alpha(color, alpha):
    cl = list(color[:3])
    cl.append(alpha)
    return cl


def split_string(text, limit):
    words = re.split('(\W)', text)
    if max(map(len, words)) > limit:
        raise ValueError("limit is too small")
    result = []
    cpart = ''
    for word in words:
        if len(word) > limit - len(cpart):
            result.append(cpart)
            cpart = word
        else:
            cpart += word
    if cpart:
        result.append(cpart)
    return result


class MessageBox(Popup):
    def __init__(self, title, msg, **kwargs):
        kwargs['title'] = title
        content = BoxLayout(orientation='vertical', padding=10)
        msglabel = Label(text=msg, markup=True, halign='left', valign='middle')
        msglabel.bind(size=msglabel.setter('text_size'))
        content.add_widget(msglabel)
        dismissbutton = Button(text='Ok', size_hint_y=0.1)
        dismissbutton.bind(on_release=self.dismiss)
        content.add_widget(dismissbutton)
        kwargs['content'] = content
        if 'size_hint' not in kwargs.keys():
            kwargs['size_hint'] = (0.8, 0.8)
        super(MessageBox, self).__init__(**kwargs)


class ImageButton(ButtonBehavior, Image):
    pass


class OptionCard(ColorBoxLayout):
    _color1 = (226.0 / 255, 225.0 / 255, 224.0 / 255, 255.0 / 255)
    _tcolor = (0.1, 0.1, 0.1, 1)

    def __init__(self, **kwargs):
        _icon_source = kwargs.pop('icon')
        _info_msg = kwargs.pop('info_msg')
        self._extended_info = kwargs.pop('extended_info', None)
        self._icon = Image(source=_icon_source)
        self._info_msg = _info_msg
        self._info_label = None
        self._extended_info_icon = None
        super(OptionCard, self).__init__(orientation='vertical', size_hint_y=0.37,
                                         bgcolor=self._color1, padding=0, **kwargs)
        self.add_widget(self._icon)
        self.add_widget(self._selector)

    def lock(self):
        self.remove_widget(self._selector)
        self.padding = 5
        anim = Animation(size_hint_y=0.1, duration=.4)
        anim.start(self)
        anim = Animation(size_hint_x=0.3, duration=.4)
        anim.start(self._icon)
        self.orientation = 'horizontal'
        self._info_label = Label(text=self._info_msg(), color=self._tcolor,
                                 halign='right', valign='middle', markup=True)
        self._info_label.bind(size=self._info_label.setter('text_size'))
        self.add_widget(self._info_label)
        if self._extended_info:
            self._extended_info_icon = ImageButton(
                source='pysamloader/assets/info.png',
                size_hint_x=0.2)
            title, content = self._extended_info()
            dismissbutton = Button(text='OK', size_hint_y=0.2)
            content.add_widget(dismissbutton)
            _msg_box = Popup(title=title, content=content, size_hint=(1, 0.5))
            dismissbutton.bind(on_release=_msg_box.dismiss)
            self._extended_info_icon.bind(on_release=_msg_box.open)
        else:
            self._extended_info_icon = Widget(size_hint_x=0.2)
        self.add_widget(self._extended_info_icon)

    @property
    def selected(self):
        raise NotImplementedError


class SpinnerOptionCard(OptionCard):
    def __init__(self, **kwargs):
        self._make_selector(kwargs.pop('msg'), kwargs.pop('options'))
        super(SpinnerOptionCard, self).__init__(**kwargs)

    def _make_selector(self, msg, options):
        self._selector = Spinner(text=msg, size_hint_y=0.27, values=options())

    @property
    def selected(self):
        return self._selector.text


class FileOptionCard(OptionCard):
    def __init__(self, **kwargs):
        self._make_selector(kwargs.pop('msg'))
        self._selected = None
        super(FileOptionCard, self).__init__(**kwargs)

    def _default_location(self):
        return os.path.expanduser('~')

    def _drop_handler(self, _, filename):
        if self.collide_point(*Window.mouse_pos):
            self._selected = filename.decode('utf-8')
            self.lock()
            App.get_running_app().deregister_drop_handler(self._drop_handler)

    def _make_selector(self, msg):
        self._selector = Button(text=msg, size_hint_y=0.27)
        content = BoxLayout(orientation='vertical')

        _file_chooser = FileChooserListView(path=self._default_location())
        content.add_widget(_file_chooser)
        _button_ok = Button(text='OK', size_hint_y=0.1)
        content.add_widget(_button_ok)
        _chooser = Popup(title=msg, content=content)

        def _handle_ok(*_):
            if not len(_file_chooser.selection):
                return
            if not os.path.isfile(_file_chooser.selection[0]):
                return
            self._selected = _file_chooser.selection[0]
            _chooser.dismiss()
            self.lock()
            App.get_running_app().deregister_drop_handler(self._drop_handler)
        _button_ok.bind(on_press=_handle_ok)

        def _handle_selector(*_):
            _chooser.open()
        self._selector.bind(on_release=_handle_selector)
        App.get_running_app().register_drop_handler(self._drop_handler)

    @property
    def selected(self):
        return self._selected


class DropHandler(object):
    def __init__(self):
        self._drops = []

    def build(self):
        Window.bind(on_dropfile=self.handle_drops)

    def register_drop_handler(self, handler):
        self._drops.append(handler)

    def deregister_drop_handler(self, handler):
        self._drops.remove(handler)

    def handle_drops(self, *args):
        print(args)
        for func in self._drops:
            func(*args)
