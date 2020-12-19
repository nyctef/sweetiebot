basic running:

```
pipenv --python 3.8
pipenv shell
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
docker run --detach --network=sbnet --name jabberserver -p 5222:5222 -p 5269:5269 -p 5280:5280 -e "XMPP_DOMAIN=jabberserver" -e "EJABBERD_ADMINS=admin_user@jabberserver" -e "EJABBERD_USERS=admin_user@jabberserver:password1234 normal_user@jabberserver:password1234 bot_user@jabberserver:password1234" -e "EJABBERD_MOD_MUC_ADMIN=true" rroemhild/ejabberd
# and create a room to join
docker exec -it jabberserver ejabberdctl create_room test_room conference.jabberserver jabberserver

# run a redis instance for sweetiebot to connect to
docker run --detach --network=sbnet --name sbredis --volume "$(pwd)/data:/data" redis

# run sweetiebot
docker run --detach --network=sbnet --name sweetiebot --volume "$(pwd)/data:/usr/src/app/data" sweetiebot

# watch sweetiebot output
docker logs --follow sweetiebot
```



