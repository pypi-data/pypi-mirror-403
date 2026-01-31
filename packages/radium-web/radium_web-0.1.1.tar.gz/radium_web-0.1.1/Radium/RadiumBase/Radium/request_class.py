import re

class Request:
    def __init__(self, paths, environ):
        self.environ = environ

        self.path = environ.get("PATH_INFO", "/")
        self.method = environ.get("REQUEST_METHOD", "GET")
        self.query = self._parse_query(environ.get("QUERY_STRING", ""))
        temp_body = environ.get("wsgi.input").read(int(environ.get("CONTENT_LENGTH", 0) or 0)).decode() if environ.get("CONTENT_LENGTH") else ""
        self.body = temp_body.split("&") if temp_body else []
        body_dict = {}
        if self.method == "POST":
            for pair in self.body:
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    body_dict[key] = value
        
        self.body = body_dict
        self.headers = self._parse_headers(environ)
        
        self.route, self.params = self._find_matching_route(
            paths.keys(),
            self.path
        )
        self.cookies = self._parse_cookies(environ)

    def _parse_cookies(self, environ):
        cookies = {}
        cookie_str = environ.get("HTTP_COOKIE", "")
        for pair in cookie_str.split(";"):
            if "=" in pair:
                key, value = pair.strip().split("=", 1)
                cookies[key] = value
        return cookies

    def _parse_headers(self, environ):
        headers = {}
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                name = key[5:].replace("_", "-").title()
                headers[name] = value

        if "CONTENT_TYPE" in environ:
            headers["Content-Type"] = environ["CONTENT_TYPE"]

        if "CONTENT_LENGTH" in environ:
            headers["Content-Length"] = environ["CONTENT_LENGTH"]

        return headers
    
    def _parse_query(self, query_string):
        from urllib.parse import parse_qs

        parsed = parse_qs(query_string, keep_blank_values=True)

        clean = {}
        for key, value in parsed.items():
            if key == "":
                raise ValueError("Invalid query parameter key")
            clean[key] = value[0] if len(value) == 1 else value

        return clean


    def _match_route(self, route, path):
        pattern = re.sub(
            r"\[(\w+)\]",
            r"(?P<\1>[^/]+)",
            route.strip("/")
        )
        match = re.fullmatch(pattern, path.strip("/"))
        return match.groupdict() if match else None

    def _find_matching_route(self, routes, user_path):
        for route in routes:
            params = self._match_route(route, user_path)
            if params is not None:
                return route, params
        return None, {}
