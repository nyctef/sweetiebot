basic running:

```
virtualenv --python=python3 env
. env/bin/activate
cp config.py.example config.py
vim config.py
./run-tests.sh
./run-e2e-tests.sh
python sweetiebot.py
python sweetiewatch.py
```

running with docker:

```
# build sweetiebot docker container
docker build -t sweetiebot .

# create a docker network
docker network create sbnet

# let's make a jabber server
docker run --detach --name ejabberd -p 5222:5222 -p 5269:5269 -p 5280:5280 -e "EJABBERD_ADMINS=admin_user@localhost" -e "EJABBERD_USERS=admin_user@localhost:password1234 normal_user@localhost" -e "EJABBERD_MOD_MUC_ADMIN=true" rroemhild/ejabberd
# and create a room to join
docker exec -it ejabberd ejabberdctl create_room test_room conference.localhost localhost

# run a redis instance for sweetiebot to connect to
docker run --detach --network=sbnet --name sbredis --volume "$(pwd)/data:/data" redis

# run sweetiebot
docker run --detach --network=sbnet --name sweetiewatch sweetiebot python sweetiewatch.py
docker run --detach --network=sbnet --name sweetiebot   sweetiebot python sweetiebot.py

# watch sweetiebot output
docker logs --follow sweetiebot
```



