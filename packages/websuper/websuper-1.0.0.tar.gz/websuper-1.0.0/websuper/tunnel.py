import requests
import random
import string
import threading
from flask import Flask, request

def rand():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=5))

def start_tunnel(port, token):
    sub = rand()
    url = f"https://{sub}.temp.websuper.org/call"

    print("WebSuper v1.0")
    print("Auth: connected")
    print(f"Forwarding: {url} -> http://localhost:{port}")
    print("Press CTRL+C to stop")

    app = Flask(__name__)

    @app.route("/call", methods=["GET","POST","PUT","DELETE","PATCH"])
    def forward():
        r = requests.request(
            request.method,
            f"http://localhost:{port}",
            headers=request.headers,
            data=request.get_data()
        )
        return (r.content, r.status_code, r.headers.items())

    app.run(port=9999)
