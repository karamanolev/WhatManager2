FROM alpine

ARG UWSGI_UID
ARG UWSGI_GID

COPY requirements.txt /srv/wm/

RUN addgroup -g "$UWSGI_GID" uwsgi \
&& adduser -h /dev/null -s /sbin/nologin -g uwsgi -G uwsgi -DH \
           -u "$UWSGI_UID" uwsgi \
#
# Install permanent runtime dependencies.
#
&& apk add --update-cache \
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
	gettext \
#
# Install build dependencies required to install the PyPI packages below.
#
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
#
# Fix numpy compilation.
#
&& ln -s /usr/include/locale.h /usr/include/xlocale.h \
#
# Install permanent runtime dependencies from PyPI.
#
&& pip --disable-pip-version-check --no-cache-dir \
	install --requirement /srv/wm/requirements.txt \
#
# Clean up.
#
&& rm -v /usr/include/xlocale.h \
&& apk del build-deps \
&& rm -v /var/cache/apk/*

COPY docker/images/app/uwsgi.ini \
	docker/images/app/external-transmission.patch \
	/srv/wm/

COPY docker/images/app/generate-wm-config \
	docker/images/app/entrypoint \
	/usr/local/bin/

COPY . /srv/wm/

RUN cd /srv/wm \
&& patch -p1 -E -i external-transmission.patch \
&& rm external-transmission.patch \
&& rm -r docker

ENTRYPOINT entrypoint
