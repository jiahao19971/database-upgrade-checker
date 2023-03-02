#!/bin/bash

if ! [ $(id -u) = 0 ]; then
   echo "The script need to be run as root." >&2
   exit 1
fi

start() {
    for DATABASE in "${DB[@]}"
    do
        PGPASSWORD=$PASSWORD psql -h ${SOURCE_HOST} -U ${USERNAME} postgres -c "CREATE EXTENSION plperl;"

        PGPASSWORD=$PASSWORD psql -h ${DEST_HOST} -U ${USERNAME} postgres -c "CREATE EXTENSION plperl;"

        bucardo add db ${DATABASE}_source dbhost=$SOURCE_HOST dbport=$PORT dbname=$DATABASE dbuser=$USERNAME dbpass=$PASSWORD;

        bucardo add db ${DATABASE}_dest dbhost=$DEST_HOST dbport=$PORT dbname=$DATABASE dbuser=$USERNAME dbpass=$PASSWORD;

        bucardo add table all --db=${DATABASE}_source --herd=${DATABASE}_herd;

        bucardo add sequence all --db=${DATABASE}_source --herd=${DATABASE}_herd;

        bucardo add dbgroup ${DATABASE}_group;
        bucardo add dbgroup ${DATABASE}_group ${DATABASE}_source:source;
        bucardo add dbgroup ${DATABASE}_group ${DATABASE}_dest:source;

        bucardo add sync ${DATABASE}_sync herd=${DATABASE}_herd dbs=${DATABASE}_group;
    done

    bucardo --db-pass $BUCARDO_PASSWORD start;
}

stop() {
    echo "hello"
    for DATABASE in "${DB[@]}"
    do
        bucardo deactivate sync ${DATABASE}_sync; 
    done
    bucardo --db-pass $BUCARDO_PASSWORD stop;
}

cleanup() {
    echo "remove"
    for DATABASE in "${DB[@]}"
    do
        bucardo deactivate sync ${DATABASE}_sync;
        bucardo delete sync ${DATABASE}_sync;

        echo "yes" |  bucardo delete table all --db=${DATABASE}_source;
        echo "yes" |  bucardo delete sequence all --db=${DATABASE}_source;

        bucardo delete relgroup ${DATABASE}_herd;
        bucardo delete dbgroup ${DATABASE}_group;
        
        bucardo delete db ${DATABASE}_source;
        bucardo delete db ${DATABASE}_dest;
    done
}


# Argument Handler
case "$1" in
start)
    start
;;

stop)
    stop
;;

cleanup)
    stop
    cleanup
;;

*)
    echo "Usage: $0 {start|stop|cleanup}"
    exit 1
esac








