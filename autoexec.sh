#!/bin/bash
set -e

ARG_USERNAME=""
ARG_PASSWORD=""
ARG_URL_PREFIX=""

if [ -n "$USERNAME" ]; then
    ARG_USERNAME="--username $USERNAME"
fi

if [ -n "$PASSWORD" ]; then
    ARG_PASSWORD="--password $PASSWORD"
fi

if [ "$URL_PREFIX" != "/" ]; then
    ARG_URL_PREFIX="--url-prefix $URL_PREFIX"
fi

if [ "$1" = 'web' ]; then
    exec rq-dashboard -p $PORT -u $REDIS_URL $ARG_USERNAME $ARG_PASSWORD $ARG_URL_PREFIX
fi

exec "$@"
