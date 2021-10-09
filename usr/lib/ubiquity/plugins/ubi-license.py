# -*- coding: utf-8; Mode: Python; indent-tabs-mode: nil; tab-width: 4 -*-
# kylin add
# license show page
# just agree the kylin licnese, then go on

import os
import subprocess
import tempfile

from ubiquity import plugin
from gi.repository import Gtk


# NAME = None
NAME = 'license'
AFTER = 'welcome'
WEIGHT = 12
OEM = False

class GhostPageBase(plugin.PluginUI):
    def __init__(self):
        plugin.PluginUI.__init__(self)
        self.skip = False

    def plugin_skip_page(self):
        return self.skip


class PageGtk(GhostPageBase):
    plugin_title = 'ubiquity/text/license_heading_label'

    def __init__(self, controller, *args, **kwargs):
        GhostPageBase.__init__(self)
        import dbus
        from gi.repository import Gtk

        if self.is_automatic:
            self.page = None
            return

        self.controller = controller
        builder = Gtk.Builder()
        self.controller.add_builder(builder)
        builder.add_from_file(os.path.join(
            os.environ['UBIQUITY_GLADE'], 'stepLicense.ui'))
        builder.connect_signals(self)
        self.page = builder.get_object('stepLicense')
        self.text_license = builder.get_object('textview')
        self.agree_license = builder.get_object('license_agree_box')
        self.agree_license.connect('toggled', self.agree_license_toggled)
        #self.radiobutton_agree = builder.get_object('radiobutton_agree')
        #self.radiobutton_no_agree = builder.get_object('radiobutton_no_agree')

        license_file="/usr/share/ubiquity/license/EULA"
        lines = open(license_file).readlines()
        iter = self.text_license.get_buffer().get_iter_at_offset(0)
        for line in lines:
            self.text_license.get_buffer().insert(iter, line)

        self.plugin_widgets = self.page
        self.next_normal = True
        self.back_normal = True
        self.connect_text = None
        self.stop_text = None
        self.skip = False

    def agree_license_toggled(self, unused):
        if self.agree_license.get_active():
            self.controller.allow_go_forward(True)
        else:
            self.controller.allow_go_forward(False)

    def hide_forward(self):
        if self.agree_license.get_active():
            self.controller.allow_go_forward(True)
        else:
            self.controller.allow_go_forward(False)

    def plugin_on_next_clicked(self):

        ###error
        #    return True

        # self.state = True
        # self.done = True
        # self.next_normal = True
        return False

class Page(plugin.Plugin):
    def prepare(self):
        self.ui.hide_forward()

        command = ['/usr/share/ubiquity/license/run.sh']
        questions = ['ubiquity/agree_license']
        return command, questions

    def run(self, priority, question):
        if os.path.isfile("/tmp/kylin_ubiquity_config"):
            import configparser
            kyconfig = configparser.ConfigParser()
            kyconfig.read("/tmp/kylin_ubiquity_config")
            if kyconfig.has_option("info","lang"):
                kylang = kyconfig.get("info", "lang")
                if kylang.startswith('zh'):
                    license_file="/usr/share/ubiquity/license/EULA"
                    self.ui.text_license.get_buffer().set_text("")
                    lines = open(license_file).readlines()
                    iter = self.ui.text_license.get_buffer().get_iter_at_offset(0)
                    for line in lines:
                        self.ui.text_license.get_buffer().insert(iter, line)
                else:
                    license_file="/usr/share/ubiquity/license/EULAE"
                    self.ui.text_license.get_buffer().set_text("")
                    lines = open(license_file).readlines()
                    iter = self.ui.text_license.get_buffer().get_iter_at_offset(0)
                    for line in lines:
                        self.ui.text_license.get_buffer().insert(iter, line)

        return plugin.Plugin.run(self, priority, question)
