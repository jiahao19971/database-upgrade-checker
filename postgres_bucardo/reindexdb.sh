#!/bin/bash
export HOST=fave-staging-fnb-pg-v11-bucardo.cpjcuh9nrfdg.ap-southeast-1.rds.amazonaws.com
export PORT=5432
export USERNAME=postgres
export PASSWORD=noddy-natty-friend-torr
export BUCARDO_PASSWORD=bucardo-runner
export DB=("kfit_app_staging" "fave_admin" "fave_dealivery" "fastpay_staging")

for DATABASE in "${DB[@]}"
do
    PGPASSWORD="$PASSWORD" reindexdb --echo --verbose -U $USERNAME -h $HOST -d $DATABASE
done