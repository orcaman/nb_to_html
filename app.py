import os
import nbhtml
import redis

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
    print(f"request url: {request.url}")

    # download the notebook first
    downloaded_nb_path = nbhtml.download_notebook_and_return_path(request)
    print(f"notebook downloaded to: {downloaded_nb_path}")

    # hash the notebook's content to see if we have ran this one before
    nb_content_hash = nbhtml.hash_file(downloaded_nb_path)
    print(f"notebook content hash: {nb_content_hash}")

    # use a combination of the notebok content and the runtime parameters as cache key
    key = nbhtml.hash_string(f'{request.url.encode("utf-8")}-{nb_content_hash}')

    try:
        print(f"try to get cache key: {key}")
        cached = redis_client.get(key)
    except:
        print(f"cannot get cache key: {key}")
        cached = None

    # cache is enabled but key is not found
    if cached is None:
        data = nbhtml.execute_notebook(downloaded_nb_path, request)
        try:
            redis_client.setex(key, cache_time, data)
            print(f"cache key set successfully: {key}")
        except:
            print(f"cannot set cache key: {key}")
    else:
        # data was read from cache
        print(f"data was read from cache for key: {key}")
        data = cached

    return data


@app.route("/health")
def health():
    return "OK"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
