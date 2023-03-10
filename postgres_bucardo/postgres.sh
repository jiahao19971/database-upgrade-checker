#!/bin/bash
# Add Environment Variable at the top 
# export HOST="Postgres database host to run vacuumdb"
# export PORT="Postgres database port"
# export USERNAME="Postgres database username"
# export PASSWORD="Postgres database password"
# export DB=("database name" "database name")

analyze() {
    for DATABASE in "${DB[@]}"
    do
        PGPASSWORD="$PASSWORD" vacuumdb -U $USERNAME -h $HOST -e -j 100 --analyze-in-stages -d $DATABASE
    done
}

vacuum() {
    for DATABASE in "${DB[@]}"
    do
        PGPASSWORD="$PASSWORD" vacuumdb -U $USERNAME -h $HOST -e -j 100 -d $DATABASE
    done
}

reindex() {
    for DATABASE in "${DB[@]}"
    do
        PGPASSWORD="$PASSWORD" reindexdb --echo --verbose -U $USERNAME -h $HOST -d $DATABASE
    done
}

# Argument Handler
case "$1" in
analyze)
    analyze
;;

vacuum)
    vacuum
;;

check)
    check
;;

reindex)
    reindex
;;

*)
    echo "Usage: $0 {analyze|check|vacuum|reindex}"
    exit 1
esac