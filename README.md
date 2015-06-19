# Juniper WebVPN indicator v 0.1

A simple ubuntu indicator for connecting to a Juniper webVPN in Ubuntu (32 bit and 64 bit) without installing JAVA or browser plugins.

##Introduction

It's a simple python script which helps you connect to a Juniper VPN server and show the status of VPN connections. It supports auto-reconnect using passwords stored in the keyring (using *python-keyring*).

Tested under Ubuntu 15.04 (64 bit) and [https://webvpn.nus.edu.sg](https://webvpn.nus.edu.sg/).


##Screenshot

![demo](Screenshots/demo.gif)

More screenshots: [connected](Screenshots/Screenshot_menu_connected.png) and [disconnected](Screenshots/Screenshot_menu_disconnected.png).

##Install

Excute **setup.sh** as root. It will install dependent packages (*python-appindicator*, *python-keyring*, *libc6:i386*, and *zlib1g:i386*) and add a menu item.  

```sh
$ chmod a+x ./setup.sh && sudo ./setup.sh
```

##How to use

#### 1. Execute **/usr/local/indicator-juniper-webvpn/vpn_indicator.py** from terminal or click the item **Juniper webVPN indicator** in the menu.
```sh
$ /usr/local/indicator-juniper-webvpn/vpn_indicator.py
```

```text
optional arguments:
  -h, --help            show this help message and exit
  -c CONFIGFILE, --configfile CONFIGFILE
                        specified configuration file other than
                        ~/.juniper_networks/network_connect/vpn_setting.cfg
```

#### 2. When necessary, modify the configuration file (default: *~/.juniper_networks/network_connect/vpn_setting.cfg*) and reload it using the menu.

#### 3. Click ***Connect*** in the menu to connect to the VPN server.

##License

MIT license for files NOT in "non-free" folder.

**Warning:** files in "non-free" folder (*libncui.so*, *ncdiag*, *ncsvc*) are non-free softwares (Copyright Juniper Network).  These binaries are exacted from ***ncLinuxApp.jar*** (Juniper Network INC). Use at you own risk. 

MD5 checksum:

> 59a4fe45da54585e5707f49e31998e87  libncui.so
> 5378f543ac9c08bdecd04c3d8eb1da21  ncdiag
> c12d10e30f913a8d5eaa0ae3f333f146  ncsvc

## Version

0.1

