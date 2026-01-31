class Response:
    def __init__(self, body, status="200 OK", headers=None, content_type="text/html"):
        self.body = body
        self.status = status
        self.headers = headers if headers is not None else [("Content-Type", content_type)]
        self.content_type = content_type
        self.cookies = {}
    def set_cookie(self, key, value, path="/", max_age=None, http_only=True):
        cookie = f"{key}={value}; Path={path}"
        if max_age:
            cookie += f"; Max-Age={max_age}"
        if http_only:
            cookie += "; HttpOnly"
        self.cookies[key] = cookie
        print('set_cookie called:', cookie)
        self.headers.append(("Set-Cookie", cookie))