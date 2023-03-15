#!/bin/bash
# Add Environment Variable at the top 
# export HOST="Postgres database host to run vacuumdb"
# export PORT="Postgres database port"
# export USERNAME="Postgres database username"
# export PASSWORD="Postgres database password"
# export DB=("database name" "database name")

# Script to run analyze by parts
# List out all the table required to populate table and run by batches 

# Without ANALYZE trx speed around 1.9k TPS
# With ANALYZE trx speed around 3.6k TPS (2x the performance gain)

analyze() {
    for DATABASE in "${DB[@]}"
    do
        ## Check on the percentage of analyze it is performing 
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