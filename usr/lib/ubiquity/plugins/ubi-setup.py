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

import os
import re

from ubiquity import keyboard_names, misc, osextras, plugin

# kobe
import ubiquity.tz

# no show this page
NAME = None
# NAME = 'setup'
AFTER = 'partman'
WEIGHT = 10


class PageGtk(plugin.PluginUI):
    plugin_title = 'ubiquity/text/keyboard_heading_label'

    def __init__(self, controller, *args, **kwargs):
        self.controller = controller
        try:
            from gi.repository import Gtk
            builder = Gtk.Builder()
            self.controller.add_builder(builder)
            builder.add_from_file(os.path.join(
                os.environ['UBIQUITY_GLADE'], 'stepSetup.ui'))
            builder.connect_signals(self)
            self.page = builder.get_object('stepSetup')
            self.msg_label = builder.get_object('message_label')
            self.msg_label.set_markup('<span size="large">接下来将进行键盘、时区等设置，并进行系统文件的拷贝过程</span>')
        except Exception as e:
            self.debug('Could not create default setup page: %s', e)
            self.page = None
        self.plugin_widgets = self.page


class PageDebconf(plugin.PluginUI):
    plugin_title = 'ubiquity/text/keyboard_heading_label'


#class PageNoninteractive(plugin.PluginUI):
    #def set_keyboard_choices(self, choices):
    #    """Set the available keyboard layout choices."""
    #    pass

    #def set_keyboard(self, layout):
    #    """Set the current keyboard layout."""
    #    #self.current_layout = layout
    #    pass

    #def get_keyboard(self):
    #    """Get the current keyboard layout."""
    #    pass
    #    #return self.current_layout

    #def set_keyboard_variant_choices(self, choices):
    #    """Set the available keyboard variant choices."""
    #    pass

    #def set_keyboard_variant(self, variant):
    #    """Set the current keyboard variant."""
    #    #self.keyboard_variant = variant
    #    pass

    #def get_keyboard_variant(self):
    #    #pass
    #    #return self.keyboard_variant


class Page(plugin.Plugin):
    def prepare(self, unfiltered=False):
        # edit by kobe
        self.tzdb = ubiquity.tz.Database()

        self.preseed('console-setup/ask_detect', 'false')

        # We need to get rid of /etc/default/keyboard, or console-setup will
        # think it's already configured and behave differently. Try to save
        # the old file for interest's sake, but it's not a big deal if we
        # can't.
        with misc.raised_privileges():
            osextras.unlink_force('/etc/default/keyboard.pre-ubiquity')
            try:
                os.rename('/etc/default/keyboard',
                          '/etc/default/keyboard.pre-ubiquity')
            except OSError:
                osextras.unlink_force('/etc/default/keyboard')
        # Make sure debconf doesn't do anything with crazy "preseeded"
        # answers to these questions. If you want to preseed these, use the
        # *code variants.
        self.db.fset('keyboard-configuration/layout', 'seen', 'false')
        self.db.fset('keyboard-configuration/variant', 'seen', 'false')
        self.db.fset('keyboard-configuration/model', 'seen', 'false')
        self.db.fset('console-setup/codeset47', 'seen', 'false')

        # Roughly taken from console-setup's config.proto:
        di_locale = self.db.get('debian-installer/locale')
        l = di_locale.rsplit('.', 1)[0]
        if not keyboard_names.has_language(l):
            self.debug("No keyboard layout translations for locale '%s'" % l)
            l = l.rsplit('_', 1)[0]
        if not keyboard_names.has_language(l):
            self.debug("No keyboard layout translations for locale '%s'" % l)
            l = 'C'
        self._locale = l

        self.has_variants = False

        # Technically we should provide a version as the second argument,
        # but that isn't currently needed and it would require querying
        # apt/dpkg for the current version, which would be slow, so we don't
        # bother for now.
        command = [
            '/usr/lib/ubiquity/console-setup/keyboard-configuration.postinst',
            'configure',
        ]
        questions = [
            '^keyboard-configuration/layout',
            '^keyboard-configuration/variant',
            '^keyboard-configuration/model',
            '^keyboard-configuration/altgr$',
            '^keyboard-configuration/unsupported_',
        ]
        environ = {
            'OVERRIDE_ALLOW_PRESEEDING': '1',
            'OVERRIDE_USE_DEBCONF_LOCALE': '1',
            'LC_ALL': di_locale,
            'PATH': '/usr/lib/ubiquity/console-setup:' + os.environ['PATH'],
        }
        return command, questions, environ

    # keyboard-configuration has a complex model of whether to store defaults
    # in debconf, induced by its need to run well both in an installer context
    # and as a package.  We need to adjust this while we're running in order
    # that we can go back and forward without keyboard-configuration
    # overwriting our answers with default values.
    def store_defaults(self, store):
        self.preseed_bool(
            'keyboard-configuration/store_defaults_in_debconf_db', store,
            seen=False)

    def run(self, priority, question):
        if self.done:
            return self.succeeded

        if question == 'keyboard-configuration/layout':
            # TODO cjwatson 2006-09-07: no keyboard-configuration support
            # for layout choice translation yet
            #self.ui.set_keyboard_choices(
            #    self.choices_untranslated(question))
            #self.ui.set_keyboard(misc.utf8(self.db.get(question)))
            # Reset these in case we just backed up from the variant
            # question.
            self.store_defaults(True)
            self.has_variants = False
            self.succeeded = True
            return True
        elif question in ('keyboard-configuration/variant',
                          'keyboard-configuration/altgr'):
            if question == 'keyboard-configuration/altgr':
                if self.has_variants:
                    return True
                else:
                    # If there's only one variant, it is always the same as
                    # the layout name.
                    # kobe
                    pass
                    # single_variant = misc.utf8(self.db.get(
                    #     'keyboard-configuration/layout'))
                    # self.ui.set_keyboard_variant_choices([single_variant])
                    # self.ui.set_keyboard_variant(single_variant)
            else:
                # TODO cjwatson 2006-10-02: no keyboard-configuration
                # support for variant choice translation yet
                self.has_variants = True
                #self.ui.set_keyboard_variant_choices(
                #    self.choices_untranslated(question))
                #self.ui.set_keyboard_variant(misc.utf8(self.db.get(question)))
            # keyboard-configuration preseeding is special, and needs to be
            # checked by hand. The seen flag on
            # keyboard-configuration/layout is used internally by
            # keyboard-configuration, so we can't just force it to true.
            if (self.is_automatic and
                self.db.fget(
                    'keyboard-configuration/layoutcode', 'seen') == 'true'):
                return True
            else:
                return plugin.Plugin.run(self, priority, question)
        elif question == 'keyboard-configuration/model':
            # Backing up from the variant question inconveniently goes back
            # to the model question.  Catch this and go forward again so
            # that we can reach the layout question.
            return True
        elif question.startswith('keyboard-configuration/unsupported_'):
            response = self.frontend.question_dialog(
                self.description(question),
                self.extended_description(question),
                ('ubiquity/imported/yes', 'ubiquity/imported/no'))
            if response == 'ubiquity/imported/yes':
                self.preseed(question, 'true')
            else:
                self.preseed(question, 'false')
            return True
        else:
            return True

    def cancel_handler(self):
        return plugin.Plugin.cancel_handler(self)

    def ok_handler(self):
        zone = "Asia/Chongqing"
        self.preseed('time/zone', zone)
        location = self.tzdb.get_loc(zone)
        if location:
            self.preseed('debian-installer/country', location.country)
        variant = "英语(美国)"
        self.preseed('keyboard-configuration/variant', variant)

        return plugin.Plugin.ok_handler(self)

    def apply_real_keyboard(self, model, layout, variant, options):
        args = []
        if model is not None and model != '':
            args.extend(("-model", model))
        args.extend(("-layout", layout))
        if variant != '':
            args.extend(("-variant", variant))
        args.extend(("-option", ""))
        for option in options:
            args.extend(("-option", option))
        misc.execute("setxkbmap", *args)

    @misc.raise_privileges
    def rewrite_xorg_conf(self, model, layout, variant, options):
        oldconfigfile = '/etc/X11/xorg.conf'
        newconfigfile = '/etc/X11/xorg.conf.new'
        try:
            oldconfig = open(oldconfigfile)
        except IOError:
            # Did they remove /etc/X11/xorg.conf or something? Oh well,
            # better to carry on than to crash.
            return
        newconfig = open(newconfigfile, 'w')

        re_section_inputdevice = re.compile(r'\s*Section\s+"InputDevice"\s*$')
        re_driver_kbd = re.compile(r'\s*Driver\s+"kbd"\s*$')
        re_endsection = re.compile(r'\s*EndSection\s*$')
        re_option_xkbmodel = re.compile(r'(\s*Option\s*"XkbModel"\s*).*')
        re_option_xkblayout = re.compile(r'(\s*Option\s*"XkbLayout"\s*).*')
        re_option_xkbvariant = re.compile(r'(\s*Option\s*"XkbVariant"\s*).*')
        re_option_xkboptions = re.compile(r'(\s*Option\s*"XkbOptions"\s*).*')
        in_inputdevice = False
        in_inputdevice_kbd = False
        done = {'model': model == '', 'layout': False,
                'variant': variant == '', 'options': options == ''}

        for line in oldconfig:
            line = line.rstrip('\n')
            if re_section_inputdevice.match(line) is not None:
                in_inputdevice = True
            elif in_inputdevice and re_driver_kbd.match(line) is not None:
                in_inputdevice_kbd = True
            elif re_endsection.match(line) is not None:
                if in_inputdevice_kbd:
                    if not done['model']:
                        print('\tOption\t\t"XkbModel"\t"%s"' % model,
                              file=newconfig)
                    if not done['layout']:
                        print('\tOption\t\t"XkbLayout"\t"%s"' % layout,
                              file=newconfig)
                    if not done['variant']:
                        print('\tOption\t\t"XkbVariant"\t"%s"' % variant,
                              file=newconfig)
                    if not done['options']:
                        print('\tOption\t\t"XkbOptions"\t"%s"' % options,
                              file=newconfig)
                in_inputdevice = False
                in_inputdevice_kbd = False
                done = {'model': model == '', 'layout': False,
                        'variant': variant == '', 'options': options == ''}
            elif in_inputdevice_kbd:
                match = re_option_xkbmodel.match(line)
                if match is not None:
                    if model == '':
                        # hmm, not quite sure what to do here; guessing that
                        # forcing to pc105 will be reasonable
                        line = match.group(1) + '"pc105"'
                    else:
                        line = match.group(1) + '"%s"' % model
                    done['model'] = True
                else:
                    match = re_option_xkblayout.match(line)
                    if match is not None:
                        line = match.group(1) + '"%s"' % layout
                        done['layout'] = True
                    else:
                        match = re_option_xkbvariant.match(line)
                        if match is not None:
                            if variant == '':
                                continue  # delete this line
                            else:
                                line = match.group(1) + '"%s"' % variant
                            done['variant'] = True
                        else:
                            match = re_option_xkboptions.match(line)
                            if match is not None:
                                if options == '':
                                    continue  # delete this line
                                else:
                                    line = match.group(1) + '"%s"' % options
                                done['options'] = True
            print(line, file=newconfig)

        newconfig.close()
        oldconfig.close()
        os.rename(newconfigfile, oldconfigfile)

    def cleanup(self):
        # TODO cjwatson 2006-09-07: I'd use dexconf, but it seems reasonable
        # for somebody to edit /etc/X11/xorg.conf on the live CD and expect
        # that to be carried over to the installed system (indeed, we've
        # always supported that up to now). So we get this horrible mess
        # instead ...

        model = self.db.get('keyboard-configuration/modelcode')
        layout = self.db.get('keyboard-configuration/layoutcode')
        variant = self.db.get('keyboard-configuration/variantcode')
        options = self.db.get('keyboard-configuration/optionscode')
        if options:
            options_list = options.split(',')
        else:
            options_list = []
        self.apply_real_keyboard(model, layout, variant, options_list)

        plugin.Plugin.cleanup(self)

        if layout == '':
            return

        self.rewrite_xorg_conf(model, layout, variant, options)


class Install(plugin.InstallPlugin):
    def prepare(self, unfiltered=False):
        return (['/usr/share/ubiquity/console-setup-apply'], [])

    def install(self, target, progress, *args, **kwargs):
        progress.info('ubiquity/install/keyboard')
        return plugin.InstallPlugin.install(
            self, target, progress, *args, **kwargs)
