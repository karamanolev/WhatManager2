# Dockerized WhatManager

In this document we'll go through installing WhatManager and configuring it for
RED with 3 Transmission instances on Linux, with every service involved running
in Docker containers.

## Requirements

- [Docker (Community Edition)](https://docs.docker.com/engine/installation/)
- [Docker Compose](https://docs.docker.com/compose/install/)

If you want to be able to manage Docker as a non-root user, add your user to
the `docker` group, as described
[here](https://docs.docker.com/engine/installation/linux/linux-postinstall/).

You also might want to enable the Docker service to start on boot. WhatManager
is configured to automatically start with the Docker service.

    sudo systemctl enable docker

## Installation

First of all, clone the repository:

    git clone https://github.com/karamanolev/WhatManager2.git

### Docker Compose configuration

Go to the [docker](.) directory in the cloned repository, edit
[docker-compose.yaml](docker-compose.yaml).  This is the file that the
`docker-compose` command reads by default.

Configure every setting in the `x-settings` section. Other stuff doesn't need
to be modified.

You can choose to place an existing `settings.py` file in `conf/app/` by
changing this:

```
              source: ./conf/app/settings.template.py
              target: /srv/wm/WhatManager2/settings.template.py
```

to:

```
              source: ./conf/app/settings.py
              target: /srv/wm/WhatManager2/settings.py
```

#### Transmission configuration

This Docker version of WhatManager doesn't manage (start, stop, configure)
Transmission instances for you when you add a client with `manage.py
transmission_new [...]`, you need to have the torrent client up and running
before adding it to WhatManager. Luckily though, you can create them with
Docker Compose easily. This gives you control over your clients, as you can
fully customize the settings. Long-term maintenance of dockerized Transmission
instances is painless, you can choose never to touch them again, or to update
their base Docker image every now and then to get the latest updates without
losing your settings. Containers will auto-start when the Docker service is
started on system startup.

If you want to use existing Transmission instances, then make sure they're
accessible by a static IP address or hostname different from that of the
loopback interface's address (localhost, 127.0.0.1). The WhatManager web app
runs in an isolated Docker container which has its own loopback interface, and
there aren't going to be any Transmission daemons running in that container,
listening on that interface. Entries in the Docker host's `/etc/hosts` work
inside containers, and you can also define hostname mappings using
[extra_hosts](https://docs.docker.com/compose/compose-file/#extra_hosts) in the
Compose file.

In this example we're going to set up dockerized instances and use Docker's
embedded DNS to resolve running Transmission containers' names (e.g. wm_red_1,
wm_red_2, wm_red_3) to their IP address. These Transmission instances are
independent from the WhatManager stack and will have their own Compose file.

Go to the `transmission` directory and edit `red-config.yaml`.  All
[Transmission options](https://github.com/transmission/transmission/wiki/Editing-Configuration-Files#options)
are configurable as environment variables by uppercasing them, replacing dashes
with underscores and prepending them with `TR_`, as seen in the YAML file.

The values in the `x-settings` section need to be copied from the WhatManager
`docker-compose.yaml` file. `music-path` will not be directly used by
Transmission, because WhatManager will specify the exact path when adding
torrents. Transmission still needs access to the directory, so it's mentioned
here as a reminder.

Configure the rest of the settings to your liking.

The current Transmission instance count can be saved to a file.

    echo 3 > red-count.txt

Generate the Compose file for RED Transmission instances.

    ./generate-compose -n "$(< red-count.txt)" -c red.config.yaml -t red.template.yaml > red-transmission.yaml

Start up the instances for testing.

    docker-compose -f red-transmission.yaml up -d

`transmission-remote-gtk` can be set up to connect to the daemons and verify
they're working. Also, the current way to delete torrents from WhatManager is
to remove them from Transmission, so setting this up will come in handy later.

1. Options -> Local Preferences
2. Name: e.g. red_1
3. Host: localhost
4. Port: e.g. 9001
5. Username: transmission
6. Password: `TRPASSWD`'s value from the `red-config.yaml` file

Click on "Connect", in the statusbar you should see "Connected: red_1".  Repeat
for the other clients, create a new profile for each of them in Transmission
Remote so you can easily switch between them later on.  You can also edit
`~/.config/transmission-remote-gtk/config.json` after creating your first
profile and copy-paste it there.

### App configuration

#### Initialize config files

You don't need to edit unused ones, but copying them is necessary.

``` Shell
cd WhatManager2 # Repository's root directory.
cp bibliotik/settings.example.py docker/conf/app/bibliotik-settings.py
cp myanonamouse/settings.example.py docker/conf/app/myanonamouse-settings.py
cp qobuz2/settings.example.py docker/conf/app/qobuz2-settings.py
```

This one's only necessary if you want to customize stuff beyond what the
`wm2-env` section of `docker-compose.yaml` allows.

``` Shell
cp WhatManager2/settings.example.py docker/conf/app/settings.py
```

### Starting up containers

TL;DR `cd docker; docker-compose up -d`

We could start up everything with the command above, but we can also take a
more step-by-step approach to see what's happening.

First, let's build the images that need to be built locally:

    docker-compose build

This can take about 10 minutes.  Afterwards the `wm_app` and `wm_sync` images
should show up in the local cache:

    docker images

If you have configured everything, the multi-container app can now be started.
Any  additional images that it needs will be pulled from Docker Hub.

    docker-compose up -d

Docker Compose will by default prepend the project name that is defined in the
[.env](.env) file to network and volume names used in the configuration file.
For example, when you list running containers using `docker ps`, you'll see
`wm_app`, `wm_db`.

You should see the containers spin up, you can check if any of them have crashed
by listing all containers on the host:

    docker ps -a

If the `STATUS` column doesn't say `Up` for a container, that's not good, you
should investigate why the program running inside it has stopped. You can refer
to the container by its `CONTAINER ID` or `NAME`.

    docker logs <name>

### Create WhatManager superuser

    docker exec -it wm_app python /srv/wm/manage.py createsuperuser

### Log in

Log in with your superuser, take a look around.

URL depends on how you set it up, e.g.:

http://localhost:8080/

There isn't very much to see yet, Stats page is empty because we don't have any
torrent clients added yet, Profile page might be empty because a successful user
profile synchronization hasn't run yet.

### Add a download location

1. Django Administration (e.g. /admin/ or /wm/admin/) 
2. Download locations: Add
3. Zone: redacted.ch 
4. Path: e.g. /mnt/music-dl (as set in `docker-compose.yaml`)
5. Preferred: Check 
6. Save

### Add Transmission instances

Once Transmission is running and the administration port is connectable, open a
shell inside the wm_app container:

    docker exec -it wm_app ash

Then add each Transmission instance to WhatManager using the port ranges you
specified in `red-transmission.yaml`:

    python /srv/wm/manage.py transmission_new <zone> <ip> <management-port> <bittorrent-port>

For example:

    python /srv/wm/manage.py transmission_new redacted.ch wm_red_1 9001 20001
    python /srv/wm/manage.py transmission_new redacted.ch wm_red_2 9002 20002
    python /srv/wm/manage.py transmission_new redacted.ch wm_red_3 9003 20003

Now, after getting WhatManager to syncronize information with the Transmission
instances manually by visiting /json/sync (e.g.
http://localhost:8080/json/sync) in your web browser, you should see no
recent errors when you click on "Log" on the web interface, and the torrent
clients should show up as "redacted01", "redacted02" and "redacted03" when
clicking on "Stats".

In case something went wrong, you can remove the clients from WhatManager and
start again:

    python /srv/wm/manage.py transmission_delete redacted01
    python /srv/wm/manage.py transmission_delete redacted02
    python /srv/wm/manage.py transmission_delete redacted03

When you're done, exit the shell running inside the container:

    exit

### Userscripts

Found at the "Userscripts" menu entry, set this up, it enhances user experience
dramatically. Needs the Greasemonkey / Tampermonkey browser extension.

## Management tasks, debugging

The project name is the default `wm` in these examples.

### How to stop and start the app

This command will stop and delete all containers and the network that we
created earlier. Bear in mind that persistent data is stored on a volume named
wm_db_data, this data and the config files will not be harmed:

    docker-compose down

As you can see, all of WhatManager's containers and networks have been deleted:

    docker ps -a
    docker network ls

But the persistent volumes remain:

    docker volume ls

The app can be restarted by running this command, like earlier:

    docker-compose up -d

If you feel like you made a mess of it and want to start over clean, you can
delete everything created by docker-compose as simply as this:

    docker-compose down
    docker volume rm wm_db_data wm_static
    docker volume rm wm_red_{1,2,3} # Optionally remove Transmission data.

### SQL database access

You can access the database by launching a new container which will be used as
a temporary MariaDB client to connect to the wm_db container. It will ask for a
password, enter MYSQL_ROOT_PASSWORD defined in the docker-compose file earlier.

``` Shell
docker run --rm -it --network wm_app \
-v "$PWD/conf/db/charset.cnf:/etc/mysql/conf.d/charset.cnf:ro" \
mariadb:10 sh -c 'exec mysql -h wm_db -uroot -p'
```

The container will self-destruct after you exit the mysql client.

## Backups

It is important to have an automated backup schedule to protect against
software corruption and hardware failure. Actually restoring your backups as a
test is a must too, you don't want to find out 5 years in that your backups
don't work after all.

### Make backups

Docker volumes can be listed with `docker volume ls`, I'm going to assume these
five:
- wm_db_data
- wm_red1
- wm_red2
- wm_red3
- wm_static

The data on these volumes is all of the persistent data that make up
WhatManager, together with the configuration files. As long as we have this
data saved, we can restore WhatManager to working order from scratch.
"wm_static" volume can be ignored because its contents are easily recreated,
like we've done earlier. Here's one way of creating backups, with "/mnt/backup"
as your backup destination directory:

``` Shell
#!/bin/sh

BACKUP_DIR="/mnt/backup/$(date +%F)"
BACKUP_NAME_PREFIX="$(date +%H-%M-%S)"
WM_DIR='/home/user/WhatManager2'
MYSQL_ROOT_PASSWORD='<mysql-password>'
TZ='<timezone>'
TRANSMISSION_COUNT='3' # Specify 0 to disable Transmission backup.

backup_transmission_volume() {
	if [ -z "$1" ]; then
		echo "Error: Missing parameter for backup_transmission_volume()"
		return
	fi

	docker run --rm \
		--mount type=volume,src="$1",dst=/var/lib/transmission-daemon,readonly \
		--mount type=bind,src="$BACKUP_DIR",dst=/backup \
		alpine \
		tar czf "/backup/$BACKUP_NAME_PREFIX-$1.tar.gz" \
			-C / var/lib/transmission-daemon
}

if ! mkdir -p "$BACKUP_DIR"; then
	echo "Error: Couldn't create backup directory"
	exit 1
fi

# Database backup.
# This command starts up a temporary container based on the "mariadb" image.
# It then executes the "mysqldump" command, which connects to the database
# server running on the database host, and saves its current state into a file.
docker run --rm \
	--network wm_app \
	--mount type=bind,src="$BACKUP_DIR",dst=/backup \
	-e MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" \
	-e TZ="$TZ" \
	mariadb:10 \
	sh -c \
		'mysqldump -h wm_db -u root -p"$MYSQL_ROOT_PASSWORD" \
		--single-transaction --routines --triggers --all-databases |
		gzip > '"/backup/$BACKUP_NAME_PREFIX-db-data.sql.gz"

# Configuration files backup.
tar czf "$BACKUP_DIR/$BACKUP_NAME_PREFIX-settings.tar.gz" \
	-C "$WM_DIR" \
	--exclude .gitignore \
	'docker/docker-compose.yaml' \
	'docker/conf/'

# Torrent clients backup.
for i in $(seq "$TRANSMISSION_COUNT"); do
	backup_transmission_volume "red-$i"
done
```

You can save the above to a file, say `/usr/local/bin/backup-wm`, and make it
executable: `chmod +x /usr/local/bin/backup-wm`.

Now the backup script should be tested: `backup-wm`

It should create the files in the "/mnt/backup/YYYY-mm-dd" directory:
- HH-MM-SS-red-1.tar.gz
- HH-MM-SS-red-2.tar.gz
- HH-MM-SS-red-3.tar.gz
- HH-MM-SS-settings.tar.gz
- HH-MM-SS-db-data.sql.gz

It's good practice to create a cron entry so the script runs periodically
without supervision. Edit your user's crontab by issuing `crontab -e`.  This
example will run the script at 04:00 (a.m.) every other day.  For details on
how this works see `man 5 crontab`.

    0 4 */2 * * backup-wm

Like with all backups, you should regularly synchronize the files to a
different physical machine and/or offline storage.

### Restore backups

Let's verify that we get a functional system when restoring.

You might want to note torrent counts on the web interface at Stats, and also
torrent counts reported when you connect to Transmission instances directly, so
you can verify that everything's present after the restore.

We're going to spin up a whole new stack of the application. This means
starting a fresh copy of all containers, networks, volumes. Instead of the
existing application's `wm_` prefix we'll create them using the `wmtest_`
prefix for volumes and networks. Containers will still have the `wm_` prefix
because that is hard-coded in the Docker Compose file.

#### Stop existing WhatManager

Begin with shutting down the "production" stack so it doesn't interfere with
our test setup:

``` Shell
cd WhatManager2/docker
docker-compose down
```

#### Settings restore

Now grab a fresh copy of WhatManager, and restore your settings:

``` Shell
cd /tmp
curl -L https://github.com/karamanolev/WhatManager2/archive/master.tar.gz | tar xz
cd WhatManager2-master
tar xf /mnt/backup/YYYY-mm-dd/HH-MM-SS-settings.tar.gz
```

#### Database restore

``` Shell
# Bring up only the database service.
COMPOSE_PROJECT_NAME=wmtest docker-compose up -d --no-deps db

# Restore the database.
docker run --rm \
	--network wmtest_app \
	--mount type=bind,src=/mnt/backup,dst=/backup,readonly \
	-e MYSQL_ROOT_PASSWORD='<mysql-password>' \
	-e TZ='<timezone>' \
	mariadb:10 \
	sh -c \
		'zcat "/backup/YYYY-mm-dd/HH-MM-SS-wm_db_data.sql.gz" |
		mysql -h wm_db -u root -p"$MYSQL_ROOT_PASSWORD"'
```

#### Transmission restore

Next we'll restore Transmission daemons' data (includes settings, torrent
files, torrent statistics).

``` Shell
for i in $(seq "$TRANSMISSION_COUNT"); do
	docker volume create "wmtest_red_$i"

	# Restore data to the volume.
	docker run --rm \
		--mount type=volume,src=wmtest_red_1,dst=/var/lib/transmission-daemon \
		--mount type=bind,src=/mnt/backup,dst=/backup,readonly \
		alpine \
		tar xvzf "/backup/YYYY-mm-dd/HH-MM-SS-wm-red-$i.tar.gz" -C /
done
```

#### Verify

- Connect to Transmission instances and check torrent counts.
- Log into the webapp.
- Force synchronization with Transmission instances (as well as your RED stats)
  by visiting /json/sync (e.g. http://localhost:8080/wm/json/sync)
- Check "Log" for errors.
- Check torrent counts under "Stats".

#### Clean up

Once everything looks good, let's bring down the service and delete the test
volumes. Be careful to include `-p wmtest`, or you'll delete your real volumes.

    COMPOSE_PROJECT_NAME=wmtest docker-compose down --volumes
