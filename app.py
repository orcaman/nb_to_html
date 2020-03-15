import os
import nbhtml
import redis
import hashlib

from flask import Flask
from flask import request

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_password = os.environ.get("REDIS_PASSWORD")
redis_port = int(os.environ.get("REDIS_PORT", 6379))
cache_time = int(os.environ.get("CACHE_TIME", 259200))
redis_client = redis.StrictRedis(
    host=redis_host, port=redis_port, password=redis_password
)

print(f"redis_host: {redis_host}")

app = Flask(__name__)


@app.route("/nb_to_html")
def nb_to_html_request():
    hash_object = hashlib.sha1(request.url.encode("utf-8"))
    key = f"nb_to_html:{hash_object.hexdigest()}"
    no_cache = request.args.get("no_cache")

    # cache is disabled, execute notebook
    if no_cache is not None:
        print("cache is disable via query string")
        return nbhtml.execute_notebook(request)

    try:
        print(f"try to get cache key: {key}")
        cached = redis_client.get(key)
    except:
        print(f"cannot get cache key: {key}")
        cached = None

    # cache is enabled but key is not found
    if cached is None:
        data = nbhtml.execute_notebook(request)
        try:
            redis_client.setex(key, cache_time, data)
        except:
            print(f"cannot set cache key: {key}")
    else:
        # data was read from cache
        print("data was read from cache")
        data = cached

    return data


@app.route("/health")
def health():
    return "OK"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
