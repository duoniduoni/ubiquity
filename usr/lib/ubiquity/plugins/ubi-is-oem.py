# -*- coding: utf-8; Mode: Python; indent-tabs-mode: nil; tab-width: 4 -*-

# kylin add oem configure page
# provides create user  on install or the new os firstboot 

import os
import subprocess
import tempfile

from ubiquity import plugin
from gi.repository import Gtk


# NAME = None
NAME = 'isoem'
# AFTER = 'welcome'
AFTER = 'partman'
WEIGHT = 12
OEM = False

class IsOEMPageBase(plugin.PluginUI):
    def __init__(self):
        plugin.PluginUI.__init__(self)
        self.skip = False

    def plugin_skip_page(self):
        return self.skip


class PageGtk(IsOEMPageBase):
    plugin_title = 'ubiquity/text/isoem_heading_label'

    def __init__(self, controller, *args, **kwargs):
        IsOEMPageBase.__init__(self)
        from gi.repository import Gtk

        # if autoinstall mode, then skip this page
        if self.is_automatic:
            self.page = None
            return

        # if oem-config-prepare not found, then skip this page
        if not os.path.isfile("/usr/sbin/oem-config-prepare"):
            self.page = None
            return

        # ghost install mode, skip this page
        if os.path.isfile("/tmp/.kylin_ghost"):
            self.page = None
            return

        self.controller = controller
        builder = Gtk.Builder()
        self.controller.add_builder(builder)
        builder.add_from_file(os.path.join(
            os.environ['UBIQUITY_GLADE'], 'stepIsOEM.ui'))
        builder.connect_signals(self)
        self.page = builder.get_object('stepIsOEM')
        self.no_oem = builder.get_object('no_oem')
        self.yes_oem = builder.get_object('yes_oem')
        self.plugin_widgets = self.page
        self.next_normal = True
        self.back_normal = True
        self.connect_text = None
        self.stop_text = None
        self.skip = False


    # to set oem flag
    def plugin_on_next_clicked(self):
        if self.yes_oem.get_active():
            open("/tmp/.kylin_reboot_go_oem", "w").write("1")
        else:
            os.system("rm -f /tmp/.kylin_reboot_go_oem")

        # self.state = True
        # self.done = True
        # self.next_normal = True
        return False

