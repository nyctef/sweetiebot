FROM python:3.8

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1

# only copy pipfile first so that we can cache the pip install step
COPY Pipfile Pipfile.lock /usr/src/app/
RUN pip install pipenv && pipenv install --three --deploy --ignore-pipfile

# now copy everything else
COPY . /usr/src/app/

RUN echo -n ' | Image built at' `date` >> version.txt

VOLUME /usr/src/app/data

ENTRYPOINT ["python", "/usr/src/app/sweetiebot.py"]
