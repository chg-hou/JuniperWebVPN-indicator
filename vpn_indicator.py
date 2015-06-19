#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# A simple indicator to help connect to a Juniper vpn
#
# Author: chg-hou <chg.hou@gmail.com>
# Homepage: https://github.com/chg-hou/JuniperWebVPN-indicator
# License: MIT
#
# version 0.1

__author__ = 'chg-hou'

import sys
import threading
import time
import os
import subprocess
import keyring
import ConfigParser
# import collections
# VPNLOG = collections.deque('', 1000)

from gi.repository import GObject as gobject
from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify
gobject.threads_init()

import argparse

arg_parser = argparse.ArgumentParser(description='Juniper webVPN Indicator')
arg_parser.add_argument('-c','--configfile',type=str,default='~/.juniper_networks/network_connect/vpn_setting.cfg',
                    help='specified configuration file other than ~/.juniper_networks/network_connect/vpn_setting.cfg')
CFG_PATH = os.path.expanduser(arg_parser.parse_args().configfile)


Notify.init('Juniper webVPN indicator')
notification = Notify.Notification.new('Title', 'message', 'dialog-information')
notification.set_timeout(4000)

NCLOG_PATH = os.path.expanduser('~/.juniper_networks/network_connect/')
app_path = os.path.dirname(os.path.abspath(__file__))

icon_connected = "connected_1"
icon_disconnected = "disconnected_1"

log_path = os.path.expanduser('~/.juniper_networks/network_connect/ncsvc.log')

if not os.path.exists(NCLOG_PATH):
    os.makedirs(NCLOG_PATH)
if not os.path.exists(CFG_PATH):
    import shutil
    shutil.copy(os.path.join(app_path, 'vpn_setting.cfg'), CFG_PATH)
if not os.path.exists(log_path):
    with open(log_path, 'w') as f:
        pass

config = ConfigParser.SafeConfigParser()
config.read(CFG_PATH)

global open_and_connect, webVPN, ncsvc_path
webVPN = {'url': config.get('VPN server', 'url'),
          'username': config.get('VPN server', 'username'),
          'realm': config.get('VPN server', 'realm'),
          'loglevel': '3'
          }
webVPN['certpath'] = os.path.join(NCLOG_PATH, webVPN['url'] + '.crt')
ncsvc_path = os.path.expanduser(config.get('ncsvc setting', 'ncsvc_path'))
auto_reconnect = config.getboolean('main', 'auto_reconnect')
open_and_connect = config.getboolean('main', 'open_and_connect')

log_process = subprocess.Popen(['tail', '-f', log_path],
                               stdout=subprocess.PIPE)
MANUAL_STOP = False


def reload_config(widget):
    global webVPN, auto_reconnect, ncsvc_path
    print webVPN
    config.read(CFG_PATH)
    webVPN = {'url': config.get('VPN server', 'url'),
              'username': config.get('VPN server', 'username'),
              'realm': config.get('VPN server', 'realm'),
              'loglevel': '3'
              }
    ncsvc_path = os.path.expanduser(config.get('ncsvc setting', 'ncsvc_path'))
    webVPN['certpath'] = os.path.join(NCLOG_PATH, webVPN['url'] + '.crt')
    print webVPN
    auto_reconnect = config.getboolean('main', 'auto_reconnect')
    if auto_reconnect:
        app.auto_reconnect_check.set_active(True)
    else:
        app.auto_reconnect_check.set_active(False)

    notification.update('webVPN', 'Config reloaded.', 'edit-redo')
    notification.show()


class StatusUpdate:
    def __init__(self):
        pass

    def check(self):
        vpn_info = subprocess.Popen(['ifconfig', 'tun'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return vpn_info.stdout.read().replace('\n\n', '').replace('\r\r', ''), vpn_info.stderr.read()


class StatusUpdateThread(threading.Thread):
    def __init__(self, app1, indi1):
        threading.Thread.__init__(self)
        self._stop = False
        self.indi = indi1
        self.app = app1
        self.obj = StatusUpdate()

    def update_ind(self, if_info, if_err):
        # self.indi.set_label(rec_val)
        global open_and_connect
        if 'Device not found' in if_err:
            if_info = 'Disconnected.'
            self.app.set_status_discoonected()
            if open_and_connect:
                open_and_connect = False
                thread_connect.connect()
                # uncomment the following 3 lines, to detect disconnection using ifconfig
                # global MANUAL_STOP
                # if (not MANUAL_STOP) and self.app.auto_reconnect_check.get_active():
                #    self.app.connect(None)
        else:
            if open_and_connect:
                open_and_connect = False
            self.app.set_status_connected()
        if_info = ''.join(['Server:\t\t', webVPN['url'],
                           '\nUsername:\t', webVPN['username'],
                           '\nRealm:\t\t', webVPN['realm'], '\n\n']) + if_info
        self.app.info_item.set_label(if_info)

    def stop(self):
        self._stop = True

    def run(self):
        while not self._stop:
            if_info, if_err = self.obj.check()
            gobject.idle_add(self.update_ind, if_info, if_err)
            time.sleep(1)


class LogUpdateThread(threading.Thread):
    def __init__(self, app1, ind1):
        threading.Thread.__init__(self)
        self.app = app1
        self.ind = ind1
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        time_start = time.time()
        self.reset_flag = False
        while not self._stop:
            line = log_process.stdout.readline()
            if not self.reset_flag:
                if time.time() - time_start > 0.5:
                    self.reset_flag = True
                else:
                    continue
            if 'session.info Connected to' in line:
                print line
                # subprocess.Popen(['notify-send','-t','1000','webVPN','VPN connected.'])
                notification.update('webVPN', 'VPN connected.', 'network-vpn')
                notification.show()
                self.app.set_status_connected()
            if 'session.info disconnected from' in line:
                print line
                # subprocess.Popen(['notify-send','-t','1000','webVPN','VPN disconnected.'])
                notification.update('webVPN', 'VPN disconnected.', 'network-offline-symbolic')  # user-offline
                notification.show()
                self.app.set_status_discoonected()
                global MANUAL_STOP
                if (not MANUAL_STOP) and self.app.auto_reconnect_check.get_active():
                    thread_connect.connect()
            if 'ncapp.error Failed to authenticate with' in line:
                print line
                # subprocess.Popen(['notify-send','-t','1000','webVPN','Failed to authenticate with IVE. Wrong username or password.'])
                notification.update('webVPN', 'Failed to authenticate with IVE. Wrong username or password.', 'error')
                notification.show()
            # print time.time(),self.reset_flag
            # VPNLOG.append(line)

            if not line:
                print 'Log break.'
                break


class ConnectThread(threading.Thread):
    def __init__(self, app1, ind1):
        threading.Thread.__init__(self)
        self.app = app1
        self.ind = ind1
        self.sub_process = None

    def run(self):
        pass

    def disconnect(self):
        if self.sub_process:
            # self.sub_process.terminate()
            # self.sub_process = None
            # cmd=os.path.join(ncsvc_path,'ncsvc')
            # child = subprocess.Popen([cmd,"-K"])
            pass

    def connect(self):
        # self.disconnect()
        global webVPN, ncsvc_path
        while not os.path.exists(webVPN['certpath']):
            self.app.fetch_server_cert(None)
        cancled_flag = 'YES'
        password = keyring.get_password(webVPN['url'], webVPN['realm'] + '\\' + webVPN['username'])

        if password is None:
            # subprocess.Popen(['notify-send','-t','3000','Password not found in keyring.'])
            notification.update('webVPN', 'Password not found in keyring.', 'password')
            notification.show()
        message = ''.join(['Server:\t\t', webVPN['url'],
                           '\nUsername:\t', webVPN['username'],
                           '\nRealm:\t\t', webVPN['realm'], '\n\n'])
        message += 'Input your password, click YES to save password in keyring, or click NO to login without saving password.'

        while cancled_flag != 'CANCELED' and (password is None):
            (cancled_flag, password) = get_password(None, message, default='')
            print cancled_flag
        if cancled_flag == 'CANCELED':
            return
        elif cancled_flag == 'YES':
            keyring.set_password(webVPN['url'], webVPN['realm'] + '\\' + webVPN['username'], password)

        cmd = os.path.join(ncsvc_path, 'ncsvc')
        # -h webvpn.nus.edu.sg -r "NUSSTU"  -f ~/.juniper_networks/network_connect/vpn.crt -L 1 -u A1234567  -p $password
        # subprocess.Popen(['notify-send','-t','1000','webVPN','Connecting to '+webVPN['url']])
        notification.update('webVPN', 'Connecting to ' + webVPN['url'], 'process-working')
        notification.show()

        self.time_start = time.time()
        self.sub_process = subprocess.Popen([cmd, "-h", webVPN['url'],
                                             '-f', webVPN['certpath'],
                                             '-L', webVPN['loglevel'],
                                             '-u', webVPN['username'],
                                             '-r', webVPN['realm'],
                                             '-p', password])

        password = ''
        # print self.sub_process.communicate(),self.sub_process.returncode
        # webvpn_time = time.time()-self.time_start
        # print VPNLOG,webvpn_time,time.time(),thread_log.time,time.time() - thread_log.time
        # while time.time()-self.time_start<0.1 or time.time() - thread_log.time < 0.1:
        #    time.sleep(0.5)
        # print VPNLOG,webvpn_time,time.time(),thread_log.time,time.time() - thread_log.time
        # if 'ncapp.error Failed to authenticate with IVE. Error 104' in VPNLOG[-1]:
        #    subprocess.Popen(['notify-send','-t','5000','Failed to authenticate with IVE. Wrong username or password.'])


def get_password(parent, message, default=''):
    d = gtk.MessageDialog(parent,
                          gtk.DialogFlags.MODAL | gtk.DialogFlags.DESTROY_WITH_PARENT,
                          gtk.MessageType.INFO,
                          gtk.ButtonsType.YES_NO,
                          message)

    entry = gtk.Entry()
    entry.set_text(default)
    entry.set_visibility(False)
    entry.set_invisible_char('*')
    entry.show()
    d.vbox.pack_end(entry, True, True, 0)
    entry.connect('activate', lambda _: d.response(gtk.ResponseType.OK))
    d.set_default_response(gtk.ResponseType.OK)
    d.set_title('Juniper webVPN')
    r = d.run()
    text = entry.get_text()  # .decode('utf8')
    d.destroy()
    # print r
    if r == gtk.ResponseType.YES:
        return 'YES', text
    elif r == gtk.ResponseType.NO:
        return 'NO', text
    else:
        return 'CANCELED', None


class app:
    def set_status_connected(self):
        # self.ind.set_status(appindicator.STATUS_ATTENTION)     #GTK2
        self.ind.set_status(appindicator.IndicatorStatus.ATTENTION)

    def set_status_discoonected(self):
        # self.ind.set_status(appindicator.STATUS_ACTIVE)        #GTK2
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)

    def __init__(self):
        # self.ind = appindicator.Indicator("Juniper VPN Indicator","indicator-messages", appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind = appindicator.Indicator.new("Juniper VPN Indicator",
                                              "indicator-messages",
                                              appindicator.IndicatorCategory.APPLICATION_STATUS)

        # self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)

        self.ind.set_icon_theme_path(app_path)
        self.ind.set_icon(icon_disconnected)
        self.ind.set_attention_icon(icon_connected)

        self.menu_setup()
        self.ind.set_menu(self.menu)

    def menu_setup(self):
        self.menu = gtk.Menu()
        self.info_item = gtk.MenuItem('VPN status')
        self.info_item.set_sensitive(False)
        self.info_item.show()
        self.seperator_item = gtk.SeparatorMenuItem()
        self.seperator_item.show()
        # --------------------------------------------------------
        self.connect_item = gtk.MenuItem("connect")
        self.connect_item.connect("activate", self.connect)
        self.connect_item.show()

        self.disconnec_all_item = gtk.MenuItem("disconnect")
        self.disconnec_all_item.connect("activate", self.disconnec_all)
        self.disconnec_all_item.show()

        self.seperator_item_2 = gtk.SeparatorMenuItem()
        self.seperator_item_2.show()
        # --------------------------------------------------------
        self.auto_reconnect_check = gtk.CheckMenuItem("Auto reconnect?")
        self.auto_reconnect_check.connect("toggled", self.auto_reconnect_check_toggle)
        global auto_reconnect
        if auto_reconnect:
            self.auto_reconnect_check.set_active(True)
        else:
            self.auto_reconnect_check.set_active(False)
        self.auto_reconnect_check.show()

        self.fetch_cert_item = gtk.MenuItem("Get server cert")
        self.fetch_cert_item.connect("activate", self.fetch_server_cert)
        self.fetch_cert_item.show()

        self.view_log_item = gtk.MenuItem("View log")
        self.view_log_item.connect("activate", self.viewlog)
        self.view_log_item.show()

        self.configuration_item = gtk.MenuItem("Modify configuration")
        self.configuration_item.connect("activate", self.configuration)
        self.configuration_item.show()
        self.reload_config_item = gtk.MenuItem("Reload configuration")
        self.reload_config_item.connect("activate", reload_config)
        self.reload_config_item.show()

        self.clear_password_item = gtk.MenuItem("Clear saved password")
        self.clear_password_item.connect("activate", self.clear_password)
        self.clear_password_item.show()

        self.seperator_item_3 = gtk.SeparatorMenuItem()
        self.seperator_item_3.show()

        # =============================================================
        self.menu.append(self.connect_item)
        self.menu.append(self.disconnec_all_item)

        self.menu.append(self.seperator_item)

        self.menu.append(self.info_item)

        self.menu.append(self.seperator_item_2)
        self.menu.append(self.auto_reconnect_check)
        self.menu.append(self.fetch_cert_item)
        self.menu.append(self.view_log_item)
        self.menu.append(self.configuration_item)
        self.menu.append(self.reload_config_item)
        self.menu.append(self.clear_password_item)

        self.menu.append(self.seperator_item_3)

        self.quititem = gtk.MenuItem("Quit")
        self.quititem.connect("activate", self.quit)
        self.quititem.show()

        self.menu.append(self.quititem)

    def auto_reconnect_check_toggle(self, widget):
        # print widget.active
        # print widget.get_active()
        pass

    def clear_password(self, widget):
        global webVPN
        try:
            keyring.delete_password(webVPN['url'], webVPN['realm'] + '\\' + webVPN['username'])
            # subprocess.Popen(['notify-send','-t','1000','Password cleaned.'])
            notification.update('webVPN', 'Saved password deleted.', 'edit-clear')
            notification.show()
        except keyring.errors.PasswordDeleteError:
            # subprocess.Popen(['notify-send','-t','1000','Password not saved.'])
            notification.update('webVPN', 'Password not saved.', 'emblem-unreadable')
            notification.show()

    def configuration(self, widget):
        pass
        # subprocess.Popen(['notify-send','-t','1000','Pls reload new configurations after editing.'])
        notification.update('webVPN', 'Pls restart app to reload new configurations.', 'system-restart')
        notification.show()
        subprocess.call(["xdg-open", CFG_PATH])

    def viewlog(self, widget):
        pass
        # ncapp.error Failed to authenticate with IVE. Error 104
        subprocess.call(["xdg-open", log_path])

    def disconnec_all(self, widget):
        """
        ncsvc -h <ivehostname> -u <username> -p <password> [-r <realm> ] -f <ivecertificate_in_der_format> [-P <service_port>] [L <log_level>] [-g] [-y <proxy> -z <proxy_port> [-x<proxy_username> -a <proxy_password> [-d<proxy_domain>]]]
        """
        global MANUAL_STOP, ncsvc_path
        MANUAL_STOP = True
        cmd = os.path.join(ncsvc_path, 'ncsvc')
        child = subprocess.Popen([cmd, "-K"])
        # subprocess.Popen(['notify-send','-t','1000','webVPN','Disconnecting VPN...'])
        notification.update('webVPN', 'Disconnecting VPN...', 'process-working-symbolic')
        notification.show()

    def fetch_server_cert(self, widget):
        global webVPN, ncsvc_path
        cmd = os.path.join(ncsvc_path, 'getx509certificate.sh')
        # child = subprocess.Popen([cmd,webVPN['url'],webVPN['certpath']])
        output = os.popen(' '.join([cmd, webVPN['url'], webVPN['certpath']]))
        # subprocess.Popen(['notify-send','-t','1000','webVPN',output.read()])
        notification.update('webVPN', output.read(), 'application-certificate')
        notification.show()
        subprocess.call(["xdg-open", webVPN['certpath']])

    def connect(self, widget):
        global MANUAL_STOP
        MANUAL_STOP = False
        thread_connect.connect()
        pass

    def quit(self, widget, data=None):
        print "Bye."
        thread_log.stop()
        thread_status.stop()
        gtk.main_quit(widget)
        sys.exit(0)


def main():
    print('Do not Press Ctrl+C to exit! It won\'t work\n')
    gtk.main()
    return 0


app = app()
thread_log = LogUpdateThread(app, app.ind)
thread_status = StatusUpdateThread(app, app.ind)
thread_connect = ConnectThread(app, app.ind)

if __name__ == "__main__":

    thread_log.setDaemon(True)
    thread_log.start()

    thread_status.setDaemon(True)
    thread_status.start()

    thread_connect.setDaemon(True)
    thread_connect.start()
    main()
