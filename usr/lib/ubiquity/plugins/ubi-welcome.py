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

from __future__ import print_function

import locale
import os
# import subprocess
import re
# import debconf
from ubiquity import i18n, misc, osextras, plugin
import platform

NAME = None
# NAME = 'welcome'
AFTER = None
WEIGHT = 10


class PageBase(plugin.PluginUI):
    def set_language_choices(self, unused_choices, choice_map):
        """Called with language choices and a map to localised names."""
        self.language_choice_map = dict(choice_map)

    def set_language(self, language):
        """Set the current selected language."""
        pass

    def get_language(self):
        """Get the current selected language."""
        return 'zh_CN'

    def set_oem_id(self, text):
        pass

    def get_oem_id(self):
        return ''


class PageGtk(PageBase):
    plugin_title = 'ubiquity/text/home_heading_label'

    def __init__(self, controller, *args, **kwargs):
        self.controller = controller
        ui_file = 'stepWelcome.ui'
        from gi.repository import Gtk, Gio
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(
            os.environ['UBIQUITY_GLADE'], ui_file))
        builder.connect_signals(self)
        self.controller.add_builder(builder)
        self.page = builder.get_object('stepWelcome')
        self.welcome_label = builder.get_object('welcome_label')
        self.welcome_label.set_markup('<span size="large">本向导将帮助您完成银河麒麟系统的安装和初始化设置</span>')
        self.plugin_widgets = self.page
        self.arch_version = platform.machine()
        if self.arch_version == "aarch64":
            settings = Gio.Settings.new('org.mate.Marco.global-keybindings')
            settings.set_string('run-command-terminal', '')


class PageDebconf(PageBase):
    plugin_title = 'ubiquity/text/home_heading_label'

    def __init__(self, controller, *args, **kwargs):
        self.controller = controller


class Page(plugin.Plugin):
    def prepare(self, unfiltered=False):
        self.language_question = None
        self.initial_language = None
        self.db.fset('localechooser/languagelist', 'seen', 'false')
        with misc.raised_privileges():
            osextras.unlink_force('/var/lib/localechooser/preseeded')
            osextras.unlink_force('/var/lib/localechooser/langlevel')

        localechooser_script = '/usr/lib/ubiquity/localechooser/localechooser'
        if ('UBIQUITY_FRONTEND' in os.environ and
                os.environ['UBIQUITY_FRONTEND'] == 'debconf_ui'):
            localechooser_script += '-debconf'

        questions = ['localechooser/languagelist']
        environ = {
            'PATH': '/usr/lib/ubiquity/localechooser:' + os.environ['PATH'],
        }
        if ('UBIQUITY_FRONTEND' in os.environ and
                os.environ['UBIQUITY_FRONTEND'] == "debconf_ui"):
            environ['TERM_FRAMEBUFFER'] = '1'
        else:
            environ['OVERRIDE_SHOW_ALL_LANGUAGES'] = '1'
        return localechooser_script, questions, environ

    def run(self, priority, question):
        if question == 'localechooser/languagelist':
            self.language_question = question
            if self.initial_language is None:
                #self.initial_language = self.db.get(question)
                self.initial_language = 'zh_CN'
            # current_language_index = self.value_index(question)
            # edit by kobe: found in i18.py
            # current_language_index, is English
            # current_language_index = 12, is Chinese (Simplified)
            current_language_index = 12
            only_installable = misc.create_bool(
                self.db.get('ubiquity/only-show-installable-languages'))

            current_language, sorted_choices, language_display_map = \
                i18n.get_languages(current_language_index, only_installable)
            if len(sorted_choices) == 1:
                self.done = True
                return True
        return plugin.Plugin.run(self, priority, question)

    def cancel_handler(self):
        # Undo effects of UI translation.
        self.ui.controller.translate(just_me=False, not_me=True)
        plugin.Plugin.cancel_handler(self)

    def ok_handler(self):
        if self.language_question is not None:
            new_language = 'zh_CN'
            self.preseed(self.language_question, new_language)
            if (self.initial_language is None or
                    self.initial_language != new_language):
                self.db.reset('debian-installer/country')
        plugin.Plugin.ok_handler(self)

    def cleanup(self):
        plugin.Plugin.cleanup(self)
        i18n.reset_locale(self.frontend)
        self.frontend.stop_debconf()
        self.ui.controller.translate(just_me=False, not_me=True, reget=True)


class Install(plugin.InstallPlugin):
    def prepare(self, unfiltered=False):
        if 'UBIQUITY_OEM_USER_CONFIG' in os.environ:
            command = ['/usr/share/ubiquity/localechooser-apply']
        else:
            command = [
                'sh', '-c',
                '/usr/lib/ubiquity/localechooser/post-base-installer ' +
                '&& /usr/lib/ubiquity/localechooser/finish-install',
            ]
        return command, []

    def _pam_env_lines(self, fd):
        """Yield a sequence of logical lines from a PAM environment file."""
        buf = ""
        for line in fd:
            line = line.lstrip()
            if line and line[0] != "#":
                if "#" in line:
                    line = line[:line.index("#")]
                for i in range(len(line) - 1, -1, -1):
                    if line[i].isspace():
                        break
                if line[i] == "\\":
                    # Continuation line.
                    buf = line[:i]
                else:
                    buf += line
                    yield buf
                    buf = ""
        if buf:
            yield buf

    def _pam_env_parse_file(self, path):
        """Parse a PAM environment file just as pam_env does.

        We use this for reading /etc/default/locale after configuring it.
        """
        try:
            with open(path) as fd:
                for line in self._pam_env_lines(fd):
                    line = line.lstrip()
                    if not line or line[0] == "#":
                        continue
                    if line.startswith("export "):
                        line = line[7:]
                    line = re.sub(r"[#\n].*", "", line)
                    if not re.match(r"^[A-Z_]+=", line):
                        continue
                    # pam_env's handling of quoting is crazy, but in this
                    # case it's better to imitate it than to fix it.
                    key, value = line.split("=", 1)
                    if value.startswith('"') or value.startswith("'"):
                        value = re.sub(r"[\"'](.|$)", r"\1", value[1:])
                    yield key, value
        except IOError:
            pass

    def install(self, target, progress, *args, **kwargs):
        progress.info('ubiquity/install/locales')
        rv = plugin.InstallPlugin.install(
            self, target, progress, *args, **kwargs)
        if not rv:
            locale_file = "/etc/default/locale"
            if 'UBIQUITY_OEM_USER_CONFIG' not in os.environ:
                locale_file = "/target%s" % locale_file
            for key, value in self._pam_env_parse_file(locale_file):
                if key in ("LANG", "LANGUAGE") or key.startswith("LC_"):
                    os.environ[key] = value
            # Start using the newly-generated locale, if possible.
            try:
                locale.setlocale(locale.LC_ALL, '')
            except locale.Error:
                pass
        return rv
