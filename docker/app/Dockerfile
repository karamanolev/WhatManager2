FROM alpine:3.6

ARG UWSGI_UID
ARG UWSGI_GID

COPY . /srv/wm/

RUN addgroup -g "$UWSGI_GID" uwsgi \
&& adduser -h /dev/null -s /sbin/nologin -g uwsgi -G uwsgi -DH \
           -u "$UWSGI_UID" uwsgi \
                                                                              \
&& apk upgrade --update-cache \
                                                                              \
# Install permanent runtime dependencies.
&& apk add \
	flac \
	lame \
	sox \
	mktorrent \
	python2 \
	mariadb-client-libs \
	libxml2 \
	libxslt \
	curl \
	libjpeg-turbo \
	uwsgi-python \
                                                                              \
# Install build dependencies required to install the PyPI packages below.
&& apk add --virtual build-deps \
	python2-dev \
	mariadb-dev \
	py2-pip \
	libxml2-dev \
	libxslt-dev \
	libjpeg-turbo-dev \
	gcc \
	musl-dev \
	linux-headers \
                                                                              \
# Fix numpy compilation.
&& ln -s /usr/include/locale.h /usr/include/xlocale.h \
                                                                              \
# Install permanent runtime dependencies from PyPI.
&& pip --disable-pip-version-check --no-cache-dir \
       install --requirement /srv/wm/requirements.txt \
                                                                              \
# Clean up.
&& rm -v /usr/include/xlocale.h \
&& apk del build-deps \
&& rm -v /var/cache/apk/*

COPY docker/app/uwsgi.ini docker/app/external-transmission.patch /srv/wm/

RUN cd /srv/wm \
&& patch -p1 -E -i external-transmission.patch \
&& rm external-transmission.patch

ENTRYPOINT uwsgi --ini /srv/wm/uwsgi.ini
