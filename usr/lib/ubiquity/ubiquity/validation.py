# -*- coding: utf-8; Mode: Python; indent-tabs-mode: nil; tab-width: 4 -*-

# «validation» - miscellaneous validation of user-entered data
#
# Copyright (C) 2005 Junta de Andalucía
# Copyright (C) 2005, 2006, 2007, 2008 Canonical Ltd.
#
# Authors:
#
# - Antonio Olmo Titos <aolmo#emergya._info>
# - Javier Carranza <javier.carranza#interactors._coop>
# - Juan Jesús Ojeda Croissier <juanje#interactors._coop>
# - Colin Watson <cjwatson@ubuntu.com>
# - Evan Dandrea <ev@ubuntu.com>
#
# This file is part of Ubiquity.
#
# Ubiquity is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or at your option)
# any later version.
#
# Ubiquity is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with Ubiquity; if not, write to the Free Software Foundation, Inc., 51
# Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# Validation library.
# Created by Antonio Olmo <aolmo#emergya._info> on 26 jul 2005.

# from ctypes import *
import os
import re
# import commands#python2
import subprocess

# import pwquality
# pwsetting = pwquality.PWQSettings()
# pwsetting.read_config()

# CLIB = False
# try:
#    kobetest = cdll.LoadLibrary('libkylinpassword.so')
#    CLIB = True
#except Exception as e:
#    CLIB = False

def against_cracklib(password):
    cmd = 'echo %s | cracklib-check' %(password)
    org_result = password + ': OK'
    p = subprocess.Popen([cmd], stdin=subprocess.PIPE,stdout=subprocess.PIPE,shell=True)
    try:
        output = p.stdout.readlines()[0].strip().decode('utf-8')
        if output == org_result:
            hint = 'good password'
            color = 'darkgreen'
        else:
            hint = 'bad password'
            color = 'darkred'
    except Exception as e:
         hint = 'bad password'
         color = 'darkred'
    # (status, output) = commands.getstatusoutput(cmd)
    # if status != 0:
    #    hint = 'bad password'
    #    color = 'darkred'
    # else:
    #    if output == org_result:
    #        hint = 'good password'
    #        color = 'darkgreen'
    #    else:
    #        hint = 'bad password'
    #        color = 'darkred'
    return (hint, color)


def check_grub_device(device):
    """Check that the user entered a valid boot device.
        @return True if the device is valid, False if it is not."""
    regex = re.compile(r'^/dev/([a-zA-Z0-9]+|mapper/[a-zA-Z0-9_]+)$')
    if regex.search(device):
        if not os.path.exists(device):
            return False
        return True
    # (device[,part-num])
    regex = re.compile(r'^\((hd|fd)[0-9]+(,[0-9]+)*\)$')
    if regex.search(device):
        return True
    else:
        return False


HOSTNAME_LENGTH = 1
HOSTNAME_BADCHAR = 2
HOSTNAME_BADHYPHEN = 3
HOSTNAME_BADDOTS = 4


def check_hostname(name):

    """ Check the correctness of a proposed host name.

        @return empty list (valid) or list of:
            - C{HOSTNAME_LENGTH} wrong length.
            - C{HOSTNAME_BADCHAR} contains invalid characters.
            - C{HOSTNAME_BADHYPHEN} starts or ends with a hyphen.
            - C{HOSTNAME_BADDOTS} contains consecutive/initial/final dots."""

    result = set()

    if len(name) < 1 or len(name) > 63:
        result.add(HOSTNAME_LENGTH)

    regex = re.compile(r'^[a-zA-Z0-9.-]+$')
    if not regex.search(name):
        result.add(HOSTNAME_BADCHAR)
    if name.startswith('-') or name.endswith('-'):
        result.add(HOSTNAME_BADHYPHEN)
    if '..' in name or name.startswith('.') or name.endswith('.'):
        result.add(HOSTNAME_BADDOTS)

    return sorted(result)

# Based on setPasswordStrength() in Mozilla Seamonkey, which is tri-licensed
# under MPL 1.1, GPL 2.0, and LGPL 2.1.

def password_strength(password):
    letter = digit = symbol = 0
    for char in password:
        if char.isdigit():
            digit += 1
        elif char.islower():
            letter += 1
        elif char.isupper():
            letter += 1
        else:
            symbol += 1
    length = len(password)
    # added by kobe
    #pwtype = None
    #if upper == length:
    #    pwtype = 'Upper'
    #elif lower == length:
    #    pwtype = 'Lower'
    #elif digit == length:
    #    pwtype = 'Digit'
    #elif symbol == length:
    #    pwtype = 'Symbol'

    if length > 5:
        length = 5
    if digit > 3:
        digit = 3
    if letter > 3:
        letter = 3
    if symbol > 3:
        symbol = 3
    strength = (
        ((length * 0.1) - 0.2) +
        (digit * 0.1) +
        (symbol * 0.15) +
        (letter * 0.1))
    if strength > 1:
        strength = 1
    if strength < 0:
        strength = 0
    return strength
    #return (strength, pwtype)

# added by kobe
# def judge_password_type(password):
#    if re.match('^[0-9]+$', password):
#        return 0
#    elif re.match('^[a-z]+$', password):
#        return 1
#    elif re.match('^[A-Z]+$', password):
#        return 2
#    if not regex.search(name):
#def judge_password(password):
#    #libapi = cdll.LoadLibrary('libkylinpassword.so')
#    user = b'kobe'
#    #pwd = b'werakb45'
#    #print(user)
#    #print(user.decode('utf-8'))
#    #print(repr(password))
#    result = kobetest.pam_sm_chauthtok(user, password.encode('utf-8'))
#    return result
    
def human_password_strength(password):
    #(strength, pwtype) = password_strength(password)
    strength = password_strength(password)
    #if CLIB == False:
    #    return ('sorry', 'darkred')
    #result = judge_password(password)
    length = len(password)
    #ky_regex = re.compile(r'^[a-zA-Z0-9._]+$')
    #if length < 6 or length > 63:
    #    hint = 'kylin_password_error_length'
    #    color = 'darkred'
    #    complete = False
    #elif not ky_regex.search(password):
    #    hint = 'kylin_password_error_badchar'
    #    color = 'darkred'
    #    complete = False
    #elif result == 0:
    #    hint = 'strong'
    #    color = 'darkgreen'
    #elif result == 1:
    #    hint = 'other'
    #    color = 'darkred'
    #elif result == 2:
    #    hint = 'sameold'
    #    color = 'darkred'
    #elif result == 3:
    #    hint = 'memoryerror'
    #    color = 'darkred'
    #elif result == 4:
    #    hint = 'usererror'
    #    color = 'darkred'
    #elif result == 5:
    #    hint = 'palindrome'
    #    color = 'darkred'
    #elif result == 6:
    #    hint = 'simple'
    #    color = 'darkred'
    #elif result == 7:
    #    hint = 'notenough'
    #    color = 'darkred'
    #elif result == 8:
    #    hint = 'manysame'
    #    color = 'darkred'
    #elif result == 9:
    #    hint = 'sequence'
    #    color = 'darkred'
    #elif result == 10:
    #    hint = 'containuser'
    #    color = 'darkred'
    #elif result == 20:
    #    hint = 'badauthentication'
    #    color = 'darkred'
    #elif length < 6:
    #    hint = 'is_short'
    #    color = 'darkred'
    #elif pwtype is not None:
    #    if pwtype == 'Upper':
    #        hint = 'all_upper'
    #        color = 'darkred'
    #    elif pwtype == 'Lower':
    #        hint = 'all_lower'
    #        color = 'darkred'
    #    elif pwtype == 'Digit':
    #        hint = 'all_digit'
    #        color = 'darkred'
    #    elif pwtype == 'Symbol':
    #        hint = 'all_symbol'
    #        color = 'darkred'
    #elif length < 7:
    #    hint = 'too_short'
    #    color = 'darkred'

    # elif password.isdigit() or password.isalpha():
    #    hint = 'all_digit_alpha'
    #    color = 'darkred'
    if length < 6:
        hint = 'too_short'
        color = 'darkred'
        complete = True
    elif strength < 0.5:
        hint = 'weak'
        color = 'darkred'
        complete = True
    elif strength < 0.75:
        hint = 'fair'
        color = 'darkorange'
        complete = True
    elif strength < 0.9:
        hint = 'good'
        color = 'darkgreen'
        complete = True
    else:
        hint = 'strong'
        color = 'darkgreen'
        complete = True
    return (hint, color, complete)

def kylin_check_passwd(passwd):
    # fix bug 14327, 2020-07-27
    passwd_escape = ''
    for ch in passwd:
        if ch in "`~!#$&*)(\\|<> ;'\"":
            passwd_escape += "\\"
        passwd_escape += ch
   
    cmdline="kylin_checkpasswd check " + passwd_escape
    output = os.popen(cmdline, "r")
    tmp_result = output.read().split(';')
    print("========================")
    print(cmdline)
    print(tmp_result)

    if tmp_result[0] == "ok":
        # print "校验通过"
        return ("", "darkgreen", True)
    # TODO, i18n
    elif not tmp_result:
        return ("error", "dardred", False)
    else:
        # print tmp_result[1][:-1]
        return (tmp_result[1][:-1], "darkred", False)

# TODO dmitrij.ledkov 2012-07-23: factor-out further into generic
# page/pagegtk/pagekde sub-widget
def gtk_password_validate(controller,
                          password,
                          verified_password,
                          password_ok,
                          password1_ok,
                          password_error_label,
                          password_strength,
                          allow_empty=False,
                          ):
    # print("lixiang-----------------")
    # print(allow_empty)#False
    complete = True
    passw = password.get_text()
    vpassw = verified_password.get_text()
    if passw != vpassw:
        complete = False
        password_ok.hide()
        if passw and (len(vpassw) / float(len(passw)) > 0.8):
            # TODO Cache, use a custom string.
            txt = controller.get_string(
                'ubiquity/text/password_mismatch')
            txt = (
                '<small>'
                '<span foreground="darkred"><b>%s</b></span>'
                '</small>' % txt)
            password_error_label.set_markup(txt)
            password_error_label.show()
    else:
        password_error_label.hide()

    if allow_empty:
        password_strength.hide()
        password1_ok.hide()
    elif not passw:
        password_strength.hide()
        password1_ok.hide()
        complete = False
    else:
#         # kobe against cracklib-check
#         #(txt, color) = against_cracklib(passw)
#         #if txt == 'bad password':
#         #    complete = False
#         #    txt = '该密码违反密码字典'
#         #    txt = '<small><span foreground="%s"><b>%s</b></span></small>' \
#         #          % (color, txt)
#         #    password_strength.set_markup(txt)
#         #    password_strength.show()
#         #    return complete           
#         (txt, color, complete) = human_password_strength(passw)
#         # TODO Cache
#         #if txt == 'other':
#         #    complete = False
#         #    txt = '密码异常组合'
#         #elif txt == 'sorry':
#         #    complete = False
#         #    txt = '密码复杂度验证库异常'
#         #    txt = '<small><span foreground="%s"><b>%s</b></span></small>' \
#         #          % (color, txt)
#         #    password_strength.set_markup(txt)
#         #    password_strength.show()
#         #    return complete
#         #elif txt == 'sameold':
#         #    complete = False
#         #    txt = '密码不应该跟上次密码太相似'
#         #elif txt == 'memoryerror':
#         #    complete = False
#         #    txt = '密码设置申请空间异常'
#         #elif txt == 'usererror':
#         #    complete = False
#         #    txt = '密码设置申请用户空间异常'
#         #elif txt == 'palindrome':
#         #    complete = False
#         #    txt = '密码不应该正反读一致'
#         #elif txt == 'simple':
#         #    complete = False
#         #    txt = '密码应至少6个字符'
#         #elif txt == 'notenough':
#         #    complete = False
#         #    txt = '密码应至少包含两类字符'
#         #elif txt == 'manysame':
#         #    complete = False
#         #    txt = '密码每个字符不应超过3个'
#         #elif txt == 'sequence':
#         #    complete = False
#         #    txt = '密码不应包含太长的单调字符序列'
#         #elif txt == 'containuser':
#         #    complete = False
#         #    txt = '密码不应该包含跟用户名一样的字符串'
#         #elif txt == 'badauthentication':
#         #    complete = False
#         #    txt = '密码异常错误'
#         #else:
#         #    txt = controller.get_string('ubiquity/text/password/' + txt)
# 
#         #if txt == 'is_short':
#         #    complete = False
#         #    txt = '密码长度应该大于等于6位'
#         #elif txt == 'all_upper':
#         #    complete = False
#         #    txt = '密码不应该全为大写字母'
#         #elif txt == 'all_lower':
#         #    complete = False
#         #    txt = '密码不应该全为小写字母'
#         #elif txt == 'all_digit':
#         #    complete = False
#         #    txt = '密码不应该全为数字'
#         #elif txt == 'all_symbol':
#         #    complete = False
#         #    txt = '密码不应该全为特殊符号'
#         #else:
#         #    txt = controller.get_string('ubiquity/text/password/' + txt)
#         txt = controller.get_string('ubiquity/text/password/' + txt)

### kylin
#         (txt, color, complete) = human_password_strength(passw)
        (txt, color, complete) = kylin_check_passwd(passw)
        if txt == "":
            password1_ok.show()
            password_strength.hide()
        else:
            txt = '<small><span foreground="%s"><b>%s</b></span></small>' \
                  % (color, txt)
            password_strength.set_markup(txt)
            password_strength.show()
            password1_ok.hide()
            complete = False
        if passw == vpassw:
            password_ok.show()
        else:
            password_ok.hide()
            complete = False

    return complete
