FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /usr/src/app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1

# only copy the dependency manifests first so that we can cache the install step
COPY pyproject.toml uv.lock /usr/src/app/
RUN uv sync --locked

# now copy everything else
COPY . /usr/src/app/

RUN echo -n ' | Image built at' `date` >> version.txt

ENTRYPOINT ["uv", "run", "--no-sync", "python", "/usr/src/app/sweetiebot.py"]
