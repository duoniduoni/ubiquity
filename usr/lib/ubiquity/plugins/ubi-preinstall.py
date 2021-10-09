# -*- coding: utf-8; Mode: Python; indent-tabs-mode: nil; tab-width: 4 -*-

# Copyright (C) 2015 Kylin Ltd.
# Written by Kobe Lee <xiangli@ubuntukylin.com>.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.

# for skip install page

from __future__ import print_function

import locale
import os
import re
from ubiquity import plugin
import ubiquity.tz

if os.path.isfile("/usr/sbin/oem-config-prepare"):
    NAME = "preinstall"
    AFTER = 'partman'
    OEM = False
else:
    NAME = "preinstall"
    AFTER = 'usersetup'
WEIGHT = 10


class PageGtk(plugin.PluginUI):
    plugin_title = 'ubiquity/text/preinstall_label'

    def __init__(self, controller, *args, **kwargs):
        self.controller = controller
        ui_file = 'stepPreInstall.ui'
        from gi.repository import Gtk, Gio
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(
            os.environ['UBIQUITY_GLADE'], ui_file))
        builder.connect_signals(self)
        self.controller.add_builder(builder)
        self.page = builder.get_object('stepPreInstall')
        self.welcome_label = builder.get_object('preinstall_label')
        self.plugin_widgets = self.page

class Page(plugin.Plugin):
    def prepare(self, unfiltered=False):
        return [],[]

    def run(self, priority, question):
        self.done = True
        return True
