#!/bin/bash
# Add Environment Variable at the top 
# export HOST="Postgres database host to run vacuumdb"
# export PORT="Postgres database port"
# export USERNAME="Postgres database username"
# export PASSWORD="Postgres database password"
# export DB=("database name" "database name")

for DATABASE in "${DB[@]}"
do
    PGPASSWORD="$PASSWORD" reindexdb --echo --verbose -U $USERNAME -h $HOST -d $DATABASE
done