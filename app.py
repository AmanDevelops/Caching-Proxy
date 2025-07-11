import gzip
import os
import pickle
from concurrent.futures import ThreadPoolExecutor

import requests
from flask import Flask, Response, g, request
from redis import ConnectionPool, Redis


app = Flask(__name__)

PROXY_URL = os.environ.get("PROXY_URL")
PROXY_EXPIRY = int(os.environ.get("PROXY_EXPIRY"))  # Seconds

REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")


redis_pool = ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=0,
    max_connections=20,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
)


executor = ThreadPoolExecutor(max_workers=10)


@app.before_request
def setup_database():
    """Setup the database"""
    g.r = Redis(connection_pool=redis_pool)


def fetch_from_upstream(url):
    """Fetch data from upstream server"""
    try:
        response = requests.get(
            url,
            timeout=(3, 10),
            stream=True,
            headers={
                "User-Agent": "CachingProxy/1.0",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            },
        )
        return response
    except requests.RequestException as e:
        return None


def compress_data(data):
    """Compress data for efficient storage"""
    return gzip.compress(pickle.dumps(data))


def decompress_data(compressed_data):
    """Decompress data from storage"""
    return pickle.loads(gzip.decompress(compressed_data))


@app.route("/", defaults={"path": ""}, methods=["GET"])
@app.route("/<path:path>", methods=["GET"])
def caching_proxy(path):
    cache_key = f"cache:{request.full_path}"

    try:
        cached_data = g.r.get(cache_key)
        if cached_data is not None:
            # Cache hit - decompress and return
            response_data = decompress_data(cached_data)
            response = Response(
                response_data["content"],
                response_data["status_code"],
                response_data["headers"],
            )
            response.headers["X-Cache"] = "HIT"
 
            return response
    except Exception as e:
        # Cache error - continue to fetch from upstream
        pass

    # Cache miss - fetch from upstream
    full_uri = f"{PROXY_URL}{request.full_path}"
    upstream_response = fetch_from_upstream(full_uri)

    if upstream_response is None:
        return Response("Upstream server error", 502)

    # Prepare response
    response = Response(
        upstream_response.content,
        upstream_response.status_code,
        upstream_response.headers.items(),
    )
    response.headers["X-Cache"] = "MISS"

    # Cache the response asynchronously (fire and forget)
    if upstream_response.status_code == 200:
        response_data = {
            "content": upstream_response.content,
            "status_code": upstream_response.status_code,
            "headers": dict(upstream_response.headers),
        }

        # Store in cache asynchronously
        executor.submit(store_in_cache, g.r, cache_key, response_data, PROXY_EXPIRY)

    return response


def store_in_cache(redis_client, key, data, expiry):
    """Store data in cache asynchronously"""
    try:
        compressed_data = compress_data(data)
        redis_client.set(key, compressed_data, ex=expiry)
    except Exception as e:
        # Log error but don't affect the response
        pass


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.route("/cache/clear", methods=["POST"])
def clear_cache():
    """Clear cache endpoint"""
    try:
        g.r.flushdb()
        return {"status": "cache cleared"}
    except Exception as e:
        return {"error": str(e)}, 500
