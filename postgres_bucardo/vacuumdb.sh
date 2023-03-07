#!/bin/bash
# Add Environment Variable at the top 
# export HOST="Postgres database host to run vacuumdb"
# export PORT="Postgres database port"
# export USERNAME="Postgres database username"
# export PASSWORD="Postgres database password"
# export DB=("database name" "database name")

for DATABASE in "${DB[@]}"
do
    PGPASSWORD="$PASSWORD" vacuumdb -U $USERNAME -h $HOST -e -j 100 --analyze-in-stages -d $DATABASE
done