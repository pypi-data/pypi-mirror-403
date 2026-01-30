#!/bin/bash
set -e

# Remap localhost for Docker networking
if [ -n "$ORACLE_CONNECTION_STRING" ]; then
    if [[ "$ORACLE_CONNECTION_STRING" == *"@localhost:"* ]] || [[ "$ORACLE_CONNECTION_STRING" == *"@127.0.0.1:"* ]]; then
        if [ "$(uname)" = "Linux" ]; then
            HOST_IP=$(ip route | awk '/default/ { print $3 }')
            export ORACLE_CONNECTION_STRING="${ORACLE_CONNECTION_STRING//localhost/$HOST_IP}"
            export ORACLE_CONNECTION_STRING="${ORACLE_CONNECTION_STRING//127.0.0.1/$HOST_IP}"
        else
            export ORACLE_CONNECTION_STRING="${ORACLE_CONNECTION_STRING//localhost/host.docker.internal}"
            export ORACLE_CONNECTION_STRING="${ORACLE_CONNECTION_STRING//127.0.0.1/host.docker.internal}"
        fi
    fi
fi

exec "$@"
