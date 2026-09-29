
quick start:

```powershell
pipenv --python 3.8
pipenv install --dev
pipenv shell
./run-tests.ps1

docker run -d --name sbpostgres -e POSTGRES_PASSWORD=password1234 -p 5432:5432 postgres:11
$env:SB_PG_DB="host=localhost user=postgres password=password1234"

./run-slow-tests.ps1
./run-e2e-tests.ps1

python sweetiebot.py
```

## Configuration

environment variables (see `config.py`):

| Variable       | Required | Default                        | Description                                     |
|----------------|----------|--------------------------------|-------------------------------------------------|
| `SB_PG_DB`     | yes      | _(none)_                       | libpq connection string for pg database         |
| `SB_JID`       | no       | `bot_user@jabberserver`        | Jabber account                                  |
| `SB_PASSWORD`  | no       | `password1234`                 | Jabber password                                 |
| `SB_CHATROOM`  | no       | `test_room@conference.jabberserver`  | MUC room to join                          |
| `SB_NICKNAME`  | no       | `Sweetiebot`                   | Nickname to use in the room                     |
| `SB_HOSTNAME`  | no       | _(none)_                       | Server to connect to, if distinct from `SB_JID` |
| `SB_PORT`      | no       | `5222`                         | Port to connect to (when `SB_HOSTNAME` is set)  |
| `SB_DEBUG`     | no       | _(off)_                        | Any non-empty value turns on debug logging      |
| `SB_APPINSIGHTS_KEY` | no | _(none)_                       | Azure Monitor / App Insights instrumentation    |

## Running in docker

`compose.test.yaml` runs sweetiebot against a test jabber server and postgres database:

```bash
docker compose -f compose.test.yaml up --build -d
docker compose -f compose.test.yaml logs --follow sweetiebot

docker compose -f compose.test.yaml exec sbpostgres psql -U postgres -d sweetiebot

docker compose -f compose.test.yaml down -v
```

Log in as `normal_user@jabberserver` / `password1234` on `localhost:5222` and join `test_room@conference.jabberserver` to talk to the bot.

## Legacy stuff

Redis is dead in production, but lives on in the tests, since the `FakeRedis` class is a handy in-memory storage layer for unit tests to depend on.
- eg unit tests in `tests/Pings.py` depends on `PingStorageRedis(FakeRedis())`
- then `slow_tests/PingStorageTests.py` tries to prove that `PingStorageRedis` behaves the same as `PingStoragePg`, so that the unit tests are also valid in the real code.

The instructions for running with `pipenv` above should probably be replaced with `uv`