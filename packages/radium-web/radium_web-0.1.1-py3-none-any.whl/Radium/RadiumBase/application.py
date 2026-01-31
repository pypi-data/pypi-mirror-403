import mimetypes
import os
from wsgiref.simple_server import make_server
from paths import routes
import re
from Radium.request_class import Request
from middlewares.middleware import middleware



def normalize_response(response):
    if len(response) == 2:
        body, content_type = response
        return body, "200 OK", [("Content-Type", content_type)]
    if len(response) == 4:
        body, content_type, status, headers = response
        if content_type:
            headers.append(("Content-Type", content_type))
        return body, status, headers
    raise ValueError("Invalid response format")


def match_route(route, path):
    pattern = re.sub(r"\[(\w+)\]", r"(?P<\1>[^/]+)", route.strip("/"))
    match = re.match(f"^{pattern}$", path.strip("/"))
    return match.groupdict() if match else None

def find_matching_route(routes, user_path):
    for route in routes:
        params = match_route(route, user_path)
        if params is not None:
            return route, params
    return None, None


def app(environ, start_response):
    path = environ.get("PATH_INFO", "")
   # if middleware(path, environ) is not None:
   #    response = function(request)
   #   start_response(response.status, response.headers)
   #  return [response.body.encode()]
    if path.startswith("/static/"):
        file_path = path.lstrip("/")  # static/logo.png

        if os.path.exists(file_path) and os.path.isfile(file_path):
            content_type, _ = mimetypes.guess_type(file_path)
            content_type = content_type or "application/octet-stream"

            with open(file_path, "rb") as f:
                start_response("200 OK", [("Content-Type", content_type)])
                return [f.read()]

        start_response("404 Not Found", [])
        return [b"Static file not found"]
    
    request = Request(routes, environ)
    if request.route is None:
        try:
            with open("static/&error.html", "r") as f:
                error_content = f.read()
            start_response("404 Not Found", [("Content-Type", "text/html")])
            return [error_content.encode()]
        except FileNotFoundError:
            start_response("404 Not Found", [])
            return [b"Path Not Found"]
    function = routes[request.route]
    response = function(request)
    start_response(response.status, response.headers)
    return [response.body.encode()]


server = make_server("127.0.0.1", 8000, app)
server.serve_forever()
