
for DATABASE in "${DB[@]}"
do
    PGPASSWORD="$PASSWORD" vacuumdb -U $USERNAME -h $HOST -e -j 100 --analyze-in-stages -d $DATABASE
done