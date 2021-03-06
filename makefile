.PHONY : install remove uninstall

install: 
	sudo cp lim /usr/bin/
	sudo chmod 755 /usr/bin/lim
	sudo mkdir -p /usr/lib/lim
	sudo cp support.py /usr/lib/lim/
	sudo chmod 755 /usr/lib/lim/support.py
	sudo cp hardware.py /usr/lib/lim/
	sudo chmod 755 /usr/lib/lim/hardware.py

remove:
	sudo rm -f /usr/bin/lim
	sudo rm -rf /usr/lib/lim

uninstall:
	sudo rm -f /usr/local/bin/lim
	sudo rm -rf /usr/local/lib/python2.7/dist-packages/littleimage
