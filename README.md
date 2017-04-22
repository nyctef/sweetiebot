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

# create a docker network for connecting sweetiebot with redis
docker network create sbnet

# run a redis instance for sweetiebot to connect to
docker run --detach --network=sbnet --name sbredis --volume "$(pwd)/data:/data" redis

# run sweetiebot
docker run --detach --network=sbnet --name sweetiebot sweetiebot python sweetiebot.py

# watch sweetiebot output
docker logs --follow sweetiebot
```



