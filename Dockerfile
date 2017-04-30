FROM python:3

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# copy just requirements.txt first so that we can cache the pip install step
COPY requirements.txt /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

# now copy everything else
COPY . /usr/src/app/

ENTRYPOINT ["/bin/bash", "/usr/src/app/run-bot-and-watch.sh"]