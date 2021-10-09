# coding: UTF-8

import pyudev
import subprocess
import os
from gi.repository import Gtk

# for delete users from install created
# define some functions for kexin

DEBUG_WINDOW = None
DEBUG_LABEL = None
def debug(text):
    global DEBUG_WINDOW, DEBUG_LABEL
    if not DEBUG_WINDOW:
        DEBUG_WINDOW = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        DEBUG_WINDOW.set_size_request(500, 400)
        DEBUG_LABEL = Gtk.Label(None)
        DEBUG_WINDOW.add(DEBUG_LABEL)
#        DEBUG_WINDOW.show_all()

    prev_text = DEBUG_LABEL.get_label()
    DEBUG_LABEL.set_label('%s\n%s' % (prev_text, text))

def findDevice(venderID = '1111', productID = '2222'):
    ukey = None

    context = pyudev.Context()
    for device in context.list_devices(subsystem = 'block'):
        venderIDFound = False
        productIDFound = False

        for key, value in device.items():
            if key == 'ID_VENDOR_ID' and value == venderID:
                venderIDFound = True
                continue
            if key == 'ID_MODEL_ID' and value == productID: 
                productIDFound = True
                continue

        if venderIDFound and productIDFound:
            ukey = device
            # kobe
            ukey.venderID = venderID
            ukey.productID = productID
            break

    return ukey

def mountDevice(ukey):
    if not ukey or not isinstance(ukey, pyudev.Device):
        # debug('no key')
        return False

#    if not ukey.device_node.endswith('1'): # /dev/sdb
#        device_name = ukey.device_node + '1'
#    else:
#        device_name = ukey.device_node
#    device_name = '/dev/sdb1'
#    debug('device_name: %s' % device_name)
    parts = [ d for d in os.listdir('/dev') if d.startswith('sd') and d[0: 3] != 'sda' and len(d) > 3 ]
    ukey_device_name = ''
    for p in parts:
        try:
            device_name = '/dev/%s' % p
            command1 = 'udevadm info --name %s | grep ID_VENDOR_ID=%s' % (device_name, ukey.venderID)
            command2 = 'udevadm info --name %s | grep ID_MODEL_ID=%s' % (device_name, ukey.productID)
            ret1 = subprocess.call(command1, stdout = subprocess.DEVNULL, shell = True)
            ret2 = subprocess.call(command2, stdout = subprocess.DEVNULL, shell = True)
            if ret1 == 0 and ret2 == 0:
                ukey_device_name = device_name
        except Exception:
            pass
    if ukey_device_name == '':
        return False

    debug('found ukey on %s' % ukey_device_name)

    try:
        mountInfo = subprocess.check_output(['grep', ukey_device_name, '/proc/mounts'])
#        mountInfo = subprocess.check_output(['grep', device_name, '/proc/mounts'])
        mountInfo = str(mountInfo)
        mountInfo.strip()
#        mountInfo = mountInfo.strip()
        mountPoint = mountInfo.split()[1]
    except Exception:
        mountPoint = ''

    if mountPoint == '/mnt':
        return True

    if mountPoint:
        try:
            debug('mounted somewhere else, umounting ...')
            subprocess.call(['umount', mountPoint])
        except Exception:
            pass

    try:
        debug('mounting %s to /mnt' % ukey_device_name)
        if subprocess.call(['mount', ukey_device_name, '/mnt']) == 0:
            return True
    except Exception:
        pass

    return False

def showErrorMessage(message):
    dlg = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, message)
    dlg.set_position(Gtk.WindowPosition.CENTER)
    dlg.set_modal(True)
    dlg.run()
    dlg.destroy()

def del_users():
    users = [ d for d in os.listdir('/home') if d != 'lost+found' ]
    for u in users:
        try:
            subprocess.call(['userdel', '-r', '-f', u])
        except Exception:
            pass


# if __name__ == '__main__':
# 
#     del_users()
