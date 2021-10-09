# -*- coding: utf-8; Mode: Python; indent-tabs-mode: nil; tab-width: 4 -*-

# kylin add
# ghost configure page
# provides install from cdrom or select ghost image( this from yhkylin-backup-tools)

import os
import subprocess
import tempfile

from ubiquity import plugin
from gi.repository import Gtk


# NAME = None
NAME = 'ghost'
# AFTER = 'welcome'
AFTER = 'license'
WEIGHT = 12
OEM = False

class GhostPageBase(plugin.PluginUI):
    def __init__(self):
        plugin.PluginUI.__init__(self)
        self.skip = False

    def plugin_skip_page(self):
        return self.skip


class PageGtk(GhostPageBase):
    plugin_title = 'ubiquity/text/ghost_heading_label'

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
            os.environ['UBIQUITY_GLADE'], 'stepGhost.ui'))
        builder.connect_signals(self)
        self.page = builder.get_object('stepGhost')
        self.no_ghost = builder.get_object('no_ghost')
        self.use_ghost = builder.get_object('use_ghost')
        self.use_ghost.connect('toggled', self.ghost_toggled)
        self.ghost_file_chooser = builder.get_object('ghost_file_chooser_button')
        self.ghost_file_chooser.set_current_folder("/")
        self.plugin_widgets = self.page
        self.next_normal = True
        self.back_normal = True
        self.connect_text = None
        self.stop_text = None
        self.skip = False
        self.ghost_file_path = None
        os.system("rm -rf /tmp/.kylin_ghost")

    def ghost_toggled(self, unused):
        if self.use_ghost.get_active():
            self.ghost_file_chooser.set_visible(True)
            self.ghost_file_path = None
        else:
            self.ghost_file_chooser.set_visible(False)
            self.ghost_file_path = None

#    def plugin_on_back_clicked(self):
#        return True

    def plugin_on_next_clicked(self):
        print("===============================")
        print(self.ghost_file_chooser.get_filename())
        self.ghost_file_path = self.ghost_file_chooser.get_filename()

        if self.use_ghost.get_active():
            kyerror_title_template = 'ubiquity/text/ghost_error_title'
            kyerror_title = self.controller.get_string(kyerror_title_template)
            kyerror_msg_template = ""
            kyerror_msg = ""
            if not self.ghost_file_path:
                kyerror_msg_template = 'ubiquity/text/ghost_error_nofile'
                kyerror_msg = self.controller.get_string(kyerror_msg_template)
                dlg = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, None)
                dlg.set_position(Gtk.WindowPosition.CENTER)
                dlg.set_modal(True)
                dlg.set_title(kyerror_title)
                dlg.set_markup(kyerror_msg)
                dlg.run()
                dlg.destroy()
                return True

            command = "file " + self.ghost_file_path
            handle0 = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
            file_type_log = str(handle0.stdout.read())
            handle0.wait()
            if (file_type_log.find("Squashfs filesystem") == -1):
                kyerror_msg_template = 'ubiquity/text/ghost_error_nosquashfs'
                kyerror_msg = self.controller.get_string(kyerror_msg_template)
                dlg = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, None)
                dlg.set_position(Gtk.WindowPosition.CENTER)
                dlg.set_modal(True)
                dlg.set_title(kyerror_title)
                dlg.set_markup(kyerror_msg)
                dlg.run()
                dlg.destroy()
                return True

            # mountpoint = tempfile.mkdtemp()
            mountpoint = "/rofs"
            command = "mount -o loop " + self.ghost_file_path + " " + mountpoint
            handle = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
            mount_log = str(handle0.stdout.read())
            handle.wait()
            if os.path.ismount(mountpoint):
                print("mount done.")
            else:
                kyerror_msg_template = 'ubiquity/text/ghost_error_mount'
                kyerror_msg = self.controller.get_string(kyerror_msg_template)
                kyerror_msg = kyerror_msg + "\n\n" + mount_log
                dlg = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, None)
                dlg.set_position(Gtk.WindowPosition.CENTER)
                dlg.set_modal(True)
                dlg.set_title(kyerror_title)
                dlg.set_markup(kyerror_msg)
                dlg.run()
                dlg.destroy()
                return True

            if not os.path.isfile(mountpoint + "/etc/lsb-release"):
                kyerror_msg_template = 'ubiquity/text/ghost_error_os'
                kyerror_msg = self.controller.get_string(kyerror_msg_template)
                dlg = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, None)
                dlg.set_position(Gtk.WindowPosition.CENTER)
                dlg.set_modal(True)
                dlg.set_title(kyerror_title)
                dlg.set_markup(kyerror_msg)
                dlg.run()
                dlg.destroy()
                return True

            # os.system("umount %s" %(mountpoint))
            open("/tmp/.kylin_ghost", "w").write(self.ghost_file_path)
        else:
            os.system("rm -rf /tmp/.kylin_ghost")

        # self.state = True
        # self.done = True
        # self.next_normal = True
        return False

