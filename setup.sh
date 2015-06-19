#!/bin/bash

if [ $EUID -ne 0 ]; then
	echo "This script must be run using sudo" 2>&1
	exit 1
else
	app_path=/usr/local/indicator-juniper-webvpn
	apt-get install -y python-appindicator python-keyring libc6:i386 zlib1g:i386 
	
	rm 	-Rf $app_path
	mkdir 	-p $app_path
	
	cp    vpn_indicator.py 	$app_path
	chown root:root        	$app_path/vpn_indicator.py
	chmod 755 		$app_path/vpn_indicator.py

	cp    vpn_setting.cfg 	$app_path
	chown root:root        	$app_path/vpn_setting.cfg
	chmod a+r 		$app_path/vpn_setting.cfg
	
	cp    getx509certificate.sh 	$app_path
	chown root:root        	$app_path/getx509certificate.sh
	chmod 755		$app_path/getx509certificate.sh
	
	install -m 6711 -o root ./non-free/ncsvc 	$app_path/ncsvc 
    	install -m 744 		./non-free/ncdiag 	$app_path/ncdiag

	cp    ./non-free/libncui.so	 	$app_path
	chown root:root        	$app_path/libncui.so
	chmod a+r		$app_path/libncui.so
	
	cp 	nc_version.txt 	$app_path
	chmod 	a+r 		$app_path/nc_version.txt
	cp 	*.png 		$app_path
	chmod 	a+r 		$app_path/*.png
	
	cp -f juniper_webvpn_indicator.desktop /usr/share/applications/
	chmod a+x /usr/share/applications/juniper_webvpn_indicator.desktop
fi
