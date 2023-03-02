export HOST=fave-production-main-pg-v11.cj4a7xtkrocq.ap-southeast-1.rds.amazonaws.com
export PORT=5432
export USERNAME=postgres
export PASSWORD=Susk-yim-neG-vaD
export DB=("fave_admin" "kfit_app_production")

for DATABASE in "${DB[@]}"
do
    PGPASSWORD="$PASSWORD" vacuumdb -U $USERNAME -h $HOST -e -j 100 --analyze-in-stages -d $DATABASE
done