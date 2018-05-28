FROM alpine

RUN apk upgrade --update-cache \
&& apk add curl \
&& rm -v /var/cache/apk/*

ADD wm-sync /usr/local/bin/

ENTRYPOINT wm-sync
