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

Go to the [docker](.) directory in the cloned repository, and copy
[docker-compose.orig.yaml](docker-compose.orig.yaml) to `docker-compose.yaml`,
then edit it. This is the file that the `docker-compose` command reads by
default.

Every setting that has a comment before it should be configured.

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
Compose file. In this example later on we're going to use Docker's embedded DNS
to resolve running Transmission containers' names (wm_red1, wm_red2, wm_red3)
to their IP address.

Go to the service named `red1` in your `docker-compose.yaml` file, this is a
service definition for a single Transmission daemon.  All [Transmission
options](https://github.com/transmission/transmission/wiki/Editing-Configuration-Files#options)
are configurable as environment variables by uppercasing them, replacing dashes
with underscores and prepending them with `TR_`, as you can see in your YAML
file which we're going to customize now.

Make sure you configure these when editing your first instance:
- 2nd entry in `volumes`: your download directory.
- `TRPASSWD`: management password, also to be entered later in the app's
`settings.py`.
- `USERID`, `GROUPID`: must have read/write access to the download directory.
- `TZ`: timezone, same as with the `db` service before.
- `TR_DOWNLOAD_DIR`: your download directory path inside of the container,
  doesn't really matter if you set this or not because WhatManager will specify
  the exact path when adding torrents instead of using the default one, but
  it's good to keep track of what directory this client's supposed to use.
- `TR_RPC_PORT`: in this example, 9001 is the management port you can connect
  to with a Transmission client.
- `ports`, `TR_PEER_PORT`: 20001 is the BitTorrent port that your torrent peers
  can initiate connections to. You can leave them as is, if you like.
- Speed limits, alt speed limits, queue size to your liking, or you can delete
  any line to use defaults.

You can go ahead and use just the one instance for now and add more later, or
you can add some more right now by copy-pasting the entire `red1` entry in
`docker-compose.yaml`.

Note that port numbers don't have to be sequential or systematic at all, they
can be any random port.

Checklist when copying a Transmission service definition to add a new torrent
client:
- Increment "red1" everywhere (red2, red3), 3 replacements total
- Increment "9001" everywhere (9002, 9003), 3 replacements total
- Increment "20001" everywhere (20002, 20003), 5 replacements total
- Add new volumes (red2, red3) to `volumes` at the very end of the file.

Once they are configured, issue `docker-compose up -d --no-deps red1 red2 red3`
in the [docker](.) directory to start up only these services for testing.

`transmission-remote-gtk` can be set up to connect to the daemons and verify
they're working. Also, the current way to delete torrents from WhatManager is
to remove them from Transmission, so setting this up will come in handy later.

1. Options -> Local Preferences
2. Name: red1
3. Host: localhost
4. Port: 9001
5. Username: transmission
6. Password: `TRPASSWD`'s value from the Docker Compose YAML file

Click on "Connect", in the statusbar you should see "Connected: red1".  Repeat
for the other clients, create a new profile for each of them so you can easily
switch between them later on.  You can also edit
`~/.config/transmission-remote-gtk/config.json` after creating your first
profile and copy-paste it there.

### Nginx configuration

Go to `docker/webserver/conf/`, copy `default.orig.conf.template` to
`default.conf.template`.

Edit `default.conf.template` to suit your needs.

The two commented sections are the main area of focus here. If you leave it as
it is, you'll be able to access WhatManager on the /wm/ location later (e.g.
http://localhost:8080/wm/).

### App configuration

#### Initialize config files

You don't need to edit the unused ones, but copying them is necessary.

``` Shell
cd WhatManager2 # Repository's root directory.
cp WhatManager2/settings.example.py docker/app/conf/settings.py
cp bibliotik/settings.example.py docker/app/conf/bibliotik-settings.py
cp myanonamouse/settings.example.py docker/app/conf/myanonamouse-settings.py
cp qobuz2/settings.example.py docker/app/conf/qobuz2-settings.py
```

#### settings.py

Edit `docker/app/conf/settings.py`.

Variables that need configuring at a minimum to get going:

``` Python
WHAT_USER_ID
WHAT_USERNAME
WHAT_PASSWORD # 2FA needs to be disabled so that WhatManager can log in.
TRANSMISSION_PASSWORD # From docker-compose.yaml.
# Rest of the TRANSMISSION variables aren't used at all in the Docker version.
USERSCRIPT_WM_ROOT = 'https://example.com' # Or plain 'http://'.
DEBUG = False # Only ever set to True if the server isn't available publicly.
DATABASES = {
  'default': {
    'NAME' = 'wm' # Used later for the 'CREATE DATABASE' SQL command.
    'PASSWORD' = '<mysql-password>' # From docker-compose.yaml.
    'HOST' = 'wm_db' # This is the hostname of the database container.
  }
}
# It's necessary to allow "wm_app" because the "sync" service will use that.
ALLOWED_HOSTS = ['example.com', '<some-ip>', 'wm_app']
TIME_ZONE
STATIC_ROOT = '/mnt/static'
```

Also set the following if hosting on e.g. the /wm/ location instead of root:

``` Python
USERSCRIPT_WM_ROOT = 'https://example.com/wm'
STATIC_URL = '/wm/static/'
LOGIN_URL = '/wm/user/login/'
```

"example.com" can be "localhost" if this is a local installation only.

### Starting up containers

TL;DR `cd docker; docker-compose up -d`

We could start up everything by the command above, but we can also take a more
step-by-step approach to see what's happening.

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

If the "STATUS" column doesn't say "Up" for a container, that's not good, you
should investigate why the program running inside it has stopped. You can refer
to the container by its "CONTAINER ID" or "NAME".

    docker logs <name>

### SQL database initial setup (wm_db container)

The database container is running and listening for commands. We're going to
create an empty database that the WhatManager webapp will then use to store
persistent data.

Launch a new container which will be used as a temporary MariaDB client to
connect to the wm_db container. It will ask for a password, enter
MYSQL_ROOT_PASSWORD defined in the docker-compose file earlier.

``` Shell
docker run --rm -it --network wm_app mariadb:10.2 \
sh -c 'exec mysql -h wm_db -uroot -p'
```

Issue these commands, `CREATE DATABASE` needs the database name we chose
earlier in `settings.py`.

``` SQL
SET character_set_server = 'utf8';
SET collation_server = 'utf8_unicode_ci';
CREATE DATABASE wm;
QUIT;
```

That's it, the container will self-destruct after you exit the mysql client.

### WhatManager initial setup (wm_app container)

We have a running container of the Django app and a working database at this
point. Start with launching a shell inside the running wm_app container:

    docker exec -it wm_app ash

Next, populate the wm_static volume with WhatManager's static data. These are
non-changing files like images, CSS and JavaScript files, which will be served
directly from the webserver, and not by WhatManager.  We'll use the wm_static
docker volume to share this content from the wm_app container with the
wm_webserver container. It will ask for confirmation, make sure the export
directory is "/mnt/static", like we set earlier in "settings.py":

    python /srv/wm/manage.py collectstatic

Now we're going to have the WhatManager app create its database schema inside
the database we created earlier:

    python /srv/wm/manage.py migrate

Create a superuser:

    python /srv/wm/manage.py createsuperuser

Exit the shell running inside the container:

    exit

### Log in

Log in with your superuser, take a look around.

URL depends on how you set it up. If you exposed the `webserver` service on TCP
port 8080 in `docker-compose.yaml`, you've set up your location as /wm/ in
`webserver/conf/conf.d/default.conf` and in `settings.py` you either defined
`DEBUG = True` or added `'localhost'` to `ALLOWED_HOSTS`, then it should be
available here:

http://localhost:8080/wm/

There isn't very much to see yet, Stats page is empty because we don't have any
torrent clients added yet, Profile page might be empty because a successful user
profile synchronization hasn't run yet.

### Add a download location

1. Django Administration (/admin/ or e.g. /wm/admin/) 
2. Download locations: Add
3. Zone: redacted.ch 
4. Path: /mnt/music-dl (as set in the Docker Compose file)
5. Preferred: Check 
6. Save

### Add Transmission instances

Once Transmission is running and the administration port is connectable, open a
shell inside the wm_app container:

    docker exec -it wm_app ash

Then add each Transmission instance to WhatManager:

    python /srv/wm/manage.py transmission_new <zone> <ip> <management-port> <bittorrent-port>

For example:

    python /srv/wm/manage.py transmission_new redacted.ch wm_red1 9001 20001
    python /srv/wm/manage.py transmission_new redacted.ch wm_red2 9002 20002
    python /srv/wm/manage.py transmission_new redacted.ch wm_red3 9003 20003

Now, after getting WhatManager to syncronize information with the Transmission
instances manually by visiting /json/sync (e.g.
http://localhost:8080/wm/json/sync) in your web browser, you should see no
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
    docker volume rm wm_mariadb_data wm_static
	docker volume rm wm_red{1,2,3} # Optionally remove Transmission data.

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
# server running on the "wm_db" host, and saves its current state into a file.
docker run --rm \
	--network wm_app \
	--mount type=bind,src="$BACKUP_DIR",dst=/backup \
	-e MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" \
	-e TZ="$TZ" \
	mariadb:10 \
	sh -c \
		'mysqldump -h wm_db -u root -p"$MYSQL_ROOT_PASSWORD" \
		--single-transaction --routines --triggers --all-databases |
		gzip > '"/backup/$BACKUP_NAME_PREFIX-wm_db_data.sql.gz"

# Torrent clients backup.
backup_transmission_volume 'wm_red1'
backup_transmission_volume 'wm_red2'
backup_transmission_volume 'wm_red3'

# Configuration files backup.
tar czf "$BACKUP_DIR/$BACKUP_NAME_PREFIX-settings.tar.gz" \
	-C "$WM_DIR" \
	--exclude .gitignore \
	'docker/docker-compose.yaml' \
	'docker/app/conf/' \
	'docker/webserver/conf'
```

You can save the above to a file, say `/usr/local/bin/backup-wm`, and make it
executable: `chmod +x /usr/local/bin/backup-wm`.

Now the backup script should be tested: `backup-wm`

It should create the files in the "/mnt/backup/YYYY-mm-dd" directory:
- HH-MM-SS-red1.tar.gz
- HH-MM-SS-red2.tar.gz
- HH-MM-SS-red3.tar.gz
- HH-MM-SS-settings.tar.gz
- HH-MM-SS-wm_db_data.sql.gz

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

#### Transmission restore

Next we'll restore Transmission daemons' data (includes settings, torrent
files, torrent statistics). For each of your Transmission instances, do:

``` Shell
# Name it "wmtest_" + volume's name from end of your Compose file.
docker volume create wmtest_red1

# Restore data to the volume.
docker run --rm \
	--mount type=volume,src=wmtest_red1,dst=/var/lib/transmission-daemon \
	--mount type=bind,src=/mnt/backup,dst=/backup,readonly \
	alpine \
	tar xvzf '/backup/YYYY-mm-dd/HH-MM-SS-wm_red1.tar.gz' -C /
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

#### Populate "static" volume

Start the app:

    COMPOSE_PROJECT_NAME=wmtest docker-compose up -d

Every service should be `Up` when you list cointainers with `docker ps -a`.

Next, populate the wmtest_static volume:

    docker exec -it wm_app ash
    python /srv/wm/manage.py collectstatic
    exit

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
