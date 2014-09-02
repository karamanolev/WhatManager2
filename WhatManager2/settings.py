import os

import djcelery


djcelery.setup_loader()

WHAT_USER_ID = 123456
WHAT_USERNAME = 'your what.cd username'
WHAT_PASSWORD = 'your what.cd password'
WHAT_PROFILE_SNAPSHOT_INTERVAL = 10 * 60  # How frequently your profile will be stored, in seconds
MIN_FREE_DISK_SPACE = 0.10  # What part of your disk is guaranteed left empty by WM
MIN_WHAT_RATIO = 1.3  # Under what ratio queued torrents won't be downloaded.
SYNC_SYNCS_FILES = False  # Whether the frequent sync will make sure ReleaseInfo is there. Leave False.
WHAT_CD_DOMAIN = 'what.cd'  # You might set this to ssl.what.cd is what.cd has a long downtime, but ssl is up.
WHAT_UPLOAD_URL = 'https://{0}/upload.php'.format(WHAT_CD_DOMAIN)
WHAT_ANNOUNCE = 'http://tracker.what.cd:34000/SET THIS TO YOUR ANNOUNCE/announce'  # Only for uploading

TRANSMISSION_PASSWORD = '9dqQQ2WW'  # Set this to something reasonable that only you know.
TRANSMISSION_FILES_ROOT = '/mnt/tank/Torrent/transmission-daemon'  # Where Transmission system files will go
TRANSMISSION_BIND_HOST = '0.0.0.0' #Transmission's ipv4 bind adress. Leave as is or changed to specific ip. 

# You only need these if you are uploading books
WHATIMG_USERNAME = 'whatimg username'
WHATIMG_PASSWORD = 'whatimg password'

# Settings for the emails that WM will send you if there is a freeleech. By default, you don't get emails.
# If you want emails, set FREELEECH_HOSTNAME to your machine's hostname. These settings are for gmail, but any
# Provider will work
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'username at gmail'
EMAIL_HOST_PASSWORD = 'password at gmail'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

FREELEECH_EMAIL_FROM = u'your own email@provider.com'
FREELEECH_EMAIL_TO = u'wherever you want to receive mail@provider.com'
FREELEECH_EMAIL_THRESHOLD = 2  # Less than this and you won't get an email.
FREELEECH_HOSTNAME = u'NO_EMAILS'  # The script will only send emails if the current hostname is equals this.

# You only need to set that if you'll be using the userscripts. Do not put a trailing slash
USERSCRIPT_WM_ROOT = 'http://hostname.com'

# You only need to set these if you are running the transcoder
TRANSCODER_ADD_TORRENT_URL = 'http://hostname.com/json/add_torrent'
TRANSCODER_HTTP_USERNAME = 'http username'
TRANSCODER_HTTP_PASSWORD = 'http password'
TRANSCODER_TEMP_DIR = '/mnt/bulk/temp/whatup.celery.{0}'.format(os.getpid())
TRANSCODER_ERROR_OUTPUT = '/mnt/bulk/temp/what_error.html'
BROKER_URL = 'amqp://guest:guest@localhost:5672/'

# You only need to set these if you are running transmission_files_sync
FILES_SYNC_HTTP_USERNAME = 'username'
FILES_SYNC_HTTP_PASSWORD = 'password'
FILES_SYNC_SSH = 'user@host.com'
FILES_SYNC_WM_ROOT = 'https://host.com/'

# Used permissions
# home_view_logentry - Viewing logs
# home_add_whattorrent - Adding torrents
# home_view_whattorrent - Viewing torrents
# what_transcode.add_transcoderequest - Adding transcode requests
# home.run_checks = Running checks
# home.view_transinstance_stats - Realtime stats viewing
# queue.view_queueitem - Viewing the queue
# queue.add_queueitem - Add to the queue
# what_profile.view_whatusersnapshot - Viewing the user profile
# home.download_whattorrent - Downloading torrent zips

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'what_manager2',  # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',  # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Sofia'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Login URL
LOGIN_URL = '/user/login'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'FvvhvjFKYRxKR9Y7xSt883Ww'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'WhatManager2.middleware.HttpBasicAuthMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'WhatManager2.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'WhatManager2.wsgi.application'

TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), '..', 'templates').replace('\\', '/'),)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djcelery',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'WhatManager2',
    'login',
    'home',
    'what_json',
    'download',
    'queue',
    'what_profile',
    'allmusic',
    'torrent_list',
    'what_transcode',
    'books',
    'bibliotik',
    'bootstrapform',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    'WhatManager2.context_processors.context_processor',
)

DATETIME_FORMAT = 'Y-m-d H:i:s'

# CACHES = {
# 'default': {
# 'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
# 'LOCATION': 'wm-cache'
# }
# }

