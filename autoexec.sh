#!/bin/bash
set -e

if [ "$1" = 'web' ]; then
    exec rq-dashboard -p $PORT -u $REDIS_URL --username $USERNAME --password $PASSWORD --url-prefix $URL_PREFIX
fi

exec "$@"
