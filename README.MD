
Things to run before setting up bucardo bucardo_permission.py and check_upgrade.py and migration.py

Migration to be done on BE level to swap all table and alter id 

```
REMOTE_HOST=<tunnel host>
REMOTE_PORT=<tunnel port>
REMOTE_KEY=<name of ssh key>
REMOTE_USERNAME=<name of user>
USERNAME=<username for postgres>
PASSWORD=<password for postgres>
OLD_INSTANCE=<old rds db instance>
NEW_INSTANCE=<new rds db instance that u migrated>
DATABASE=<all the database that u need to check the index on (use , to separate each database)>
```


TO DO LIST
- Create a centralize class to call the tunnel and postgres
- Update single operation script to a cluster 