import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "frontend" / "public"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)


parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=5173)
args = parser.parse_args()

ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
