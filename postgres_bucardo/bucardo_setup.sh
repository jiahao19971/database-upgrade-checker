#!/bin/bash
# Add Environment Variable at the top 
# export SOURCE_HOST="main intance to migrate db"
# export DEST_HOST="db migrated from main instance"
# export PORT="postgres port"
# export USERNAME="Postgres database username"
# export PASSWORD="Postgres database password"
# export BUCARDO_PASSWORD="bucardo database password"
# export DB=("database name" "database name")

if ! [ $(id -u) = 0 ]; then
   echo "The script need to be run as root." >&2
   exit 1
fi

test() {
    echo $DATABASE
}

initial() {
    PGPASSWORD=$PASSWORD psql -h $SOURCE_HOST -U $USERNAME postgres -c "CREATE EXTENSION plperl;";

    PGPASSWORD=$PASSWORD psql -h $DEST_HOST -U $USERNAME postgres -c "CREATE EXTENSION plperl;";

    for DATABASE in "${DB[@]}"
    do
        bucardo --db-pass $BUCARDO_PASSWORD add db ${DATABASE}_source dbhost=$SOURCE_HOST dbport=$PORT dbname=$DATABASE dbuser=$USERNAME dbpass=$PASSWORD;

        bucardo --db-pass $BUCARDO_PASSWORD add db ${DATABASE}_dest dbhost=$DEST_HOST dbport=$PORT dbname=$DATABASE dbuser=$USERNAME dbpass=$PASSWORD;

        bucardo --db-pass $BUCARDO_PASSWORD add table all --db=${DATABASE}_source --herd=${DATABASE}_herd;

        bucardo --db-pass $BUCARDO_PASSWORD add sequence all --db=${DATABASE}_source --herd=${DATABASE}_herd;

        bucardo --db-pass $BUCARDO_PASSWORD add dbgroup ${DATABASE}_group;
        bucardo --db-pass $BUCARDO_PASSWORD add dbgroup ${DATABASE}_group ${DATABASE}_source:source;
        bucardo --db-pass $BUCARDO_PASSWORD add dbgroup ${DATABASE}_group ${DATABASE}_dest:source;

        bucardo --db-pass $BUCARDO_PASSWORD add sync ${DATABASE}_sync herd=${DATABASE}_herd dbs=${DATABASE}_group;
    done
}

start() {
    echo "starting..."
    for DATABASE in "${DB[@]}"
    do
        bucardo --db-pass $BUCARDO_PASSWORD activate sync ${DATABASE}_sync; 
    done
    bucardo --db-pass $BUCARDO_PASSWORD start;
}

stop() {
    echo "stopping..."
    for DATABASE in "${DB[@]}"
    do
        bucardo --db-pass $BUCARDO_PASSWORD deactivate sync ${DATABASE}_sync; 
    done
    bucardo --db-pass $BUCARDO_PASSWORD stop;
}

cleanup() {
    echo "remove"
    for DATABASE in "${DB[@]}"
    do
        bucardo --db-pass $BUCARDO_PASSWORD deactivate sync ${DATABASE}_sync;
        bucardo --db-pass $BUCARDO_PASSWORD delete sync ${DATABASE}_sync;

        echo "yes" |  bucardo --db-pass $BUCARDO_PASSWORD delete table all --db=${DATABASE}_source;
        echo "yes" |  bucardo --db-pass $BUCARDO_PASSWORD delete sequence all --db=${DATABASE}_source;

        bucardo --db-pass $BUCARDO_PASSWORD delete relgroup ${DATABASE}_herd;
        bucardo --db-pass $BUCARDO_PASSWORD delete dbgroup ${DATABASE}_group;
        
        bucardo --db-pass $BUCARDO_PASSWORD delete db ${DATABASE}_source;
        bucardo --db-pass $BUCARDO_PASSWORD delete db ${DATABASE}_dest;
    done
}


# Argument Handler
case "$1" in
initial)
    initial
    start
;;

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

test)
    test
;;

*)
    echo "Usage: $0 {start|stop|cleanup|initial|test}"
    exit 1
esac








