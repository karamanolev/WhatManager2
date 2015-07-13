Celery Init script
==================
Having installed all the requirements for transcoding within WhatManager2, follow these steps to setup the init script for Ubuntu or Debian:

 1. Install screen:

		sudo apt-get install screen

 2. Replace USERNAME in wm2celery with the username you wish Celery to run from.


 3. Copy wm2celery to /etc/init.d/

 4. Make sure it has execution rights:

		sudo chmod +x /etc/init.d/wm2celery

 5. Set the init script for boot time:

		sudo update-rc.d wm2celery defaults



Once installed, the service will be handled the usual way:

	sudo service wm2celery start | stop | restart


You will be able to reattach to the screen session that is running Celery using screen normally.