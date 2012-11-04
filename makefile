.PHONY : install remove

install: 
	sudo cp lim /usr/bin/
	sudo chmod 755 /usr/bin/lim
	sudo mkdir -p /usr/lib/lim
	sudo cp support.py /usr/lib/lim/
	sudo chmod 755 /usr/lib/lim/support.py

remove:
	-sudo rm /usr/bin/lim
	-sudo rm -rf /usr/lib/lim
