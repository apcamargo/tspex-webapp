# tspex-webapp

## Build and launch

```
$ docker-compose up -d --build
```

This will expose the app on port 80 and a Flower server for monitoring Celery workers on port 5555.

To add more Celery workers, start the compose with multiple `worker` containers:

```
$ docker-compose up -d --build --scale worker=3
```

To shut down:

```
$ docker-compose down
```

## Services

- `webapp`: The tspex app, powered by the Flask framework.
- `cleanup`: Executes a script to delete files generated by tspex after 7 days.
- `monitor`: A Flower instance to monitor Celery workers.
- `worker`: A Celery worker to manage asynchronous tasks.
- `redis`: A Redis message broker.

## Options

The following environment variables should be edited in the `docker-compose.yml` file before starting `tspex-webapp` in a production environment:
- `FLASK_SECRET_KEY`: [Secret key](http://flask.pocoo.org/docs/1.0/quickstart/#sessions) used by [Flask](http://flask.pocoo.org/).
- `GUNICORN_CMD_ARGS`: [Settings](http://docs.gunicorn.org/en/stable/settings.html) for [Gunicorn](https://gunicorn.org/), such as number of workers.
- `FLOWER_BASIC_AUTH`: [HTTP Basic Authentication](https://flower.readthedocs.io/en/latest/auth.html#basic-auth) for [Flower](https://flower.readthedocs.io/).
