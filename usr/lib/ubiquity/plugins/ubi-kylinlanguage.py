# -*- coding: utf-8; Mode: Python; indent-tabs-mode: nil; tab-width: 4 -*-

# Copyright (C) 2006, 2007, 2008 Canonical Ltd.
# Written by Colin Watson <cjwatson@ubuntu.com>.
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from __future__ import print_function

import locale
import os
import re

import debconf

from ubiquity import auto_update, i18n, misc, osextras, plugin
import firstboot_utils as ff
import platform

# change from language page, just to page simple
# NAME = None
# NAME = 'language'
NAME = 'welcome'
AFTER = None
WEIGHT = 10

_release_notes_url_path = '/cdrom/.disk/release_notes_url'


class PageBase(plugin.PluginUI):
    def set_language_choices(self, unused_choices, choice_map):
        """Called with language choices and a map to localised names."""
        self.language_choice_map = dict(choice_map)

    def set_language(self, language):
        """Set the current selected language."""
        pass

    def get_language(self):
        """Get the current selected language."""
        return 'C'
        # return 'zh_CN'

    def set_oem_id(self, text):
        pass

    def get_oem_id(self):
        return ''


class PageGtk(PageBase):
    plugin_is_language = True
    plugin_title = 'ubiquity/text/language_heading_label'

    def __init__(self, controller, *args, **kwargs):
        self.controller = controller
        self.timeout_id = None
        self.wget_retcode = None
        self.wget_proc = None
        #if self.controller.oem_user_config:
        #    ui_file = 'stepLanguageOnly.ui'
        #    self.only = True
        #else:
        ui_file = 'stepKylinLanguage.ui'
        self.only = False
        from gi.repository import Gtk, Gio
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(
            os.environ['UBIQUITY_GLADE'], ui_file))
        builder.connect_signals(self)
        self.controller.add_builder(builder)
        self.page = builder.get_object('stepLanguage')
        self.iconview = builder.get_object('language_iconview')
        self.treeview = builder.get_object('language_treeview')

        self.welcome_label = builder.get_object('welcome_label')
        # self.welcome_label.set_markup('<span size="xx-large">本向导将帮助您完成银河麒麟系统的安装和初始化设置</span>')

        self.plugin_widgets = self.page
        self.arch_version = platform.machine()
        #if self.arch_version == "aarch64":
        #    settings = Gio.Settings.new('org.mate.Marco.global-keybindings')
        #    settings.set_string('run-command-terminal', '')

    def set_language_choices(self, choices, choice_map):
        from gi.repository import Gtk, GObject
        PageBase.set_language_choices(self, choices, choice_map)
        list_store = Gtk.ListStore.new([GObject.TYPE_STRING])
        longest_length = 0
        longest = ''
        for choice in choices:
            list_store.append([choice])
            # Work around the fact that GtkIconView wraps at 50px or the width
            # of the icon, which is nonexistent here. See adjust_wrap_width ()
            # in gtkiconview.c for the details.
            if self.only:
                length = len(choice)
                if length > longest_length:
                    longest_length = length
                    longest = choice
        # Support both iconview and treeview
        if self.only:
            self.iconview.set_model(list_store)
            self.iconview.set_text_column(0)
            pad = self.iconview.get_property('item-padding')
            layout = self.iconview.create_pango_layout(longest)
            self.iconview.set_item_width(layout.get_pixel_size()[0] + pad * 2)
        else:
            if len(self.treeview.get_columns()) < 1:
                column = Gtk.TreeViewColumn(
                    None, Gtk.CellRendererText(), text=0)
                column.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
                self.treeview.append_column(column)
                selection = self.treeview.get_selection()
                selection.connect(
                    'changed', self.on_language_selection_changed)
            self.treeview.set_model(list_store)

    def set_language(self, language):
        # Support both iconview and treeview
        if self.only:
            model = self.iconview.get_model()
            iterator = model.iter_children(None)
            while iterator is not None:
                if misc.utf8(model.get_value(iterator, 0)) == language:
                    path = model.get_path(iterator)
                    self.iconview.select_path(path)
                    self.iconview.scroll_to_path(path, True, 0.5, 0.5)
                    break
                iterator = model.iter_next(iterator)
        else:
            model = self.treeview.get_model()
            iterator = model.iter_children(None)
            while iterator is not None:
                if misc.utf8(model.get_value(iterator, 0)) == language:
                    path = model.get_path(iterator)
                    self.treeview.get_selection().select_path(path)
                    self.treeview.scroll_to_cell(
                        path, use_align=True, row_align=0.5)
                    break
                iterator = model.iter_next(iterator)

    def get_language(self):
        # Support both iconview and treeview
        if self.only:
            model = self.iconview.get_model()
            items = self.iconview.get_selected_items()
            if not items:
                return None
            iterator = model.get_iter(items[0])
        else:
            selection = self.treeview.get_selection()
            (model, iterator) = selection.get_selected()
        if iterator is None:
            return None
        else:
            value = misc.utf8(model.get_value(iterator, 0))
            return self.language_choice_map[value][1]

    def on_language_activated(self, *args, **kwargs):
        self.controller.go_forward()

    def on_language_selection_changed(self, *args, **kwargs):
        lang = self.get_language()
        self.controller.allow_go_forward(bool(lang))
        if not lang:
            return
        if 'UBIQUITY_GREETER' in os.environ:
            misc.set_indicator_keymaps(lang)
        # strip encoding; we use UTF-8 internally no matter what
        lang = lang.split('.')[0]
        ff.debug(lang)
        self.controller.translate(lang)
        from gi.repository import Gtk
        ltr = i18n.get_string('default-ltr', lang, 'ubiquity/imported')
        if ltr == 'default:RTL':
            Gtk.Widget.set_default_direction(Gtk.TextDirection.RTL)
        else:
            Gtk.Widget.set_default_direction(Gtk.TextDirection.LTR)

        if self.only:
            # The language page for oem-config doesn't have the fancy greeter.
            return

        # TODO: Cache these.
        release = misc.get_release()
        install_medium = misc.get_install_medium()
        install_medium = i18n.get_string(install_medium, lang)
        # Set the release name (Ubuntu 10.04) and medium (USB or CD) where
        # necessary.
        # w = self.try_install_text_label
        # text = i18n.get_string(Gtk.Buildable.get_name(w), lang)
        # text = text.replace('${RELEASE}', release.name)
        # text = text.replace('${MEDIUM}', install_medium)
        # w.set_label(text)
        w = self.welcome_label
        text = i18n.get_string(Gtk.Buildable.get_name(w), lang)
        w.set_markup(text)

        # Big buttons.
        # for w in (self.try_ubuntu, self.install_ubuntu):
        #    text = i18n.get_string(Gtk.Buildable.get_name(w), lang)
        #    text = text.replace('${RELEASE}', release.name)
        #    text = text.replace('${MEDIUM}', install_medium)
        #    w.get_child().set_markup('<span size="x-large">%s</span>' % text)

        # Make the forward button a consistent size, regardless of its text.
        install_label = i18n.get_string('install_button', lang)
        next_button = self.controller._wizard.next
        next_label = next_button.get_label()

        next_button.set_size_request(-1, -1)
        next_w = next_button.size_request().width
        next_button.set_label(install_label)
        install_w = next_button.size_request().width
        next_button.set_label(next_label)
        if next_w > install_w:
            next_button.set_size_request(next_w, -1)
        else:
            next_button.set_size_request(install_w, -1)

        for w in self.page.get_children():
            w.show()

    def plugin_on_next_clicked(self):
        from gi.repository import Gtk

        Is_server_machine = 0
        Is_desktop_os = 0

        output = os.popen('systemd-detect-virt', 'r')
        if output.read()[:-1] != "none":
            ### print("kvm")
            return False

        ### Is server machine, cpu num
        output = os.popen('cat /proc/cpuinfo | grep "^processor" | wc -l', 'r')
        cpu_num = output.read()[:-1]
        if int(cpu_num) >= 64:
            Is_server_machine = 1

        ### Is server machine, cpu port
        ### CPU part: 0x660 is FT1500
        ### CPU part: 0x661 is FT2000AHK
        ### CPU part: 0x662 is FT2000PLUS
        output = os.popen('cat /proc/cpuinfo | grep "^CPU part" | grep "0x662"', 'r')
        cpu_part_str = output.read()[:-1]
        if cpu_part_str != "":
            Is_server_machine = 1

        ### Is desktop os, kernel
        output = os.popen('uname -r | grep "\.desktop\."', 'r')
        kernel_str = output.read()[:-1]
        if kernel_str != "":
            Is_desktop_os = 1

        ### Is desktop os, some pkg
        output = os.popen('dpkg -l  | grep "kylin-user-guide"', 'r')
        desktop_guide_str = output.read()[:-1]
        if desktop_guide_str != "":
            Is_desktop_os = 1

        ### Is desktop os, kyinfo
        if os.path.exists("/etc/.kyinfo"):
            output = os.popen('cat /etc/.kyinfo | grep "^dist_id=" | grep "\-desktop\-"', 'r')
            kyinfo_has_desktop_str = output.read()[:-1]
            if kyinfo_has_desktop_str != "":
                Is_desktop_os = 1

        ### error 
        if Is_server_machine == 1 and Is_desktop_os == 1:
            kyerror_title_template = 'ubiquity/text/smachine_dos_error_title'
            kyerror_title = self.controller.get_string(kyerror_title_template)
            kyerror_msg_template = 'ubiquity/text/smachine_dos_error_info'
            kyerror_msg = self.controller.get_string(kyerror_msg_template)
            dlg = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, None)
            dlg.set_position(Gtk.WindowPosition.CENTER)
            dlg.set_modal(True)
            dlg.set_title(kyerror_title)
            dlg.set_markup(kyerror_msg)
            dlg.run()
            dlg.destroy()
            os.system("killall ubiquity")
            return True
        else:
            return False


class PageDebconf(PageBase):
    plugin_title = 'ubiquity/text/language_heading_label'

    def __init__(self, controller, *args, **kwargs):
        self.controller = controller


class PageNoninteractive(PageBase):
    def __init__(self, controller, *args, **kwargs):
        self.controller = controller

    def set_language(self, language):
        """Set the current selected language."""
        # Use the language code, not the translated name
        self.language = self.language_choice_map[language][1]

    def get_language(self):
        """Get the current selected language."""
        return self.language


class Page(plugin.Plugin):
    def prepare(self, unfiltered=False):
        self.language_question = None
        self.initial_language = None
        # self.initial_language = 'zh_CN'
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
            #if self.initial_language is None:
            #    self.initial_language = 'zh_CN'
                # self.initial_language = self.db.get(question)
            # current_language_index = self.value_index(question)
            ky_current_lang = os.getenv("LANG").split('.')[0]
            if ky_current_lang == "en_US":
                current_language_index = 2
                if self.initial_language is None:
                    self.initial_language = 'en_US'
            else:
                current_language_index = 1
                if self.initial_language is None:
                    self.initial_language = 'zh_CN'
            only_installable = misc.create_bool(
                self.db.get('ubiquity/only-show-installable-languages'))

            current_language, sorted_choices, language_display_map = \
                i18n.get_languages(current_language_index, only_installable)

            self.ui.set_language_choices(sorted_choices,
                                         language_display_map)
            self.ui.set_language(current_language)
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
            new_language = self.ui.get_language()
            # new_language = 'zh_CN'
            self.preseed(self.language_question, new_language)
            if (self.initial_language is None or
                    self.initial_language != new_language):
                self.db.reset('debian-installer/country')

            #kylin ubiquity config
            import configparser
            kyconfig = configparser.ConfigParser()
            kyconfig.read("/tmp/kylin_ubiquity_config")
            if "info" not in kyconfig.sections():
                kyconfig.add_section("info")
            kyconfig.set("info", "lang", new_language)
            kyconfig.write(open("/tmp/kylin_ubiquity_config",'w'))

        # if self.ui.controller.oem_config:
        #    self.preseed('oem-config/id', self.ui.get_oem_id())
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
