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
