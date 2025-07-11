import os

import requests
from flask import Flask, Response, g, request
from redis import Redis

from utils import deserialize_response, serialize_response

app = Flask(__name__)

PROXY_URL = os.environ.get("PROXY_URL")
PROXY_EXPIRY = int(os.environ.get("PROXY_EXPIRY"))  # Seconds

REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")


@app.before_request
def setup_database():
    g.r = Redis(host=REDIS_HOST, password=REDIS_PASSWORD, port=REDIS_PORT, db=0)


@app.route("/", defaults={"path": ""}, methods=["GET"])
@app.route("/<path:path>", methods=["GET"])
def caching_proxy(path):

    cache = g.r.get(request.full_path)

    if cache is not None:
        response = deserialize_response(cache)
        response.headers["X-Cache"] = "HIT"
    else:
        full_uri = f"{PROXY_URL}{request.full_path}"
        new_response = requests.get(full_uri)
        response = Response(
            new_response.content, new_response.status_code, new_response.headers.items()
        )
        response.headers["X-Cache"] = "MISS"
        g.r.set(request.full_path, serialize_response(response), ex=PROXY_EXPIRY)

    return response
