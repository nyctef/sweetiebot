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
docker run --detach --network=sbnet --name ejabberd --publish 5222:5222 ejabberd/ecs
# and create a user to connect as
docker exec -it ejabberd /home/p1/ejabberd-api register --endpoint=http://127.0.0.1:5280/ --jid=admin@localhost --password=passw0rd

# run a redis instance for sweetiebot to connect to
docker run --detach --network=sbnet --name sbredis --volume "$(pwd)/data:/data" redis

# run sweetiebot
docker run --detach --network=sbnet --name sweetiewatch sweetiebot python sweetiewatch.py
docker run --detach --network=sbnet --name sweetiebot   sweetiebot python sweetiebot.py

# watch sweetiebot output
docker logs --follow sweetiebot
```



