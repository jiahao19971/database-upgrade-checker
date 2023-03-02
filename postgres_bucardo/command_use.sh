export SOURCE_HOST=fave-production-main-pg-v10.cj4a7xtkrocq.ap-southeast-1.rds.amazonaws.com
export DEST_HOST=fave-production-main-pg-v11.cj4a7xtkrocq.ap-southeast-1.rds.amazonaws.com
export PORT=5432
export USERNAME=postgres
export PASSWORD=Susk-yim-neG-vaD
export DB=("kfit_app_production" "fave_admin")

for DATABASE in "${DB[@]}"
do
    bucardo add db ${DATABASE}_source dbhost=$SOURCE_HOST dbport=$PORT dbname=$DATABASE dbuser=$USERNAME dbpass=$PASSWORD;

    bucardo add db ${DATABASE}_dest dbhost=$DEST_HOST dbport=$PORT dbname=$DATABASE dbuser=$USERNAME dbpass=$PASSWORD;

    bucardo add table all --db=${DATABASE}_source --herd=${DATABASE}_herd;

    bucardo add sequence all --db=${DATABASE}_source --herd=${DATABASE}_herd;

    bucardo add dbgroup ${DATABASE}_group;
    bucardo add dbgroup ${DATABASE}_group ${DATABASE}_source:source;
    bucardo add dbgroup ${DATABASE}_group ${DATABASE}_dest:source;

    bucardo add sync ${DATABASE}_sync herd=${DATABASE}_herd dbs=${DATABASE}_group;
done




