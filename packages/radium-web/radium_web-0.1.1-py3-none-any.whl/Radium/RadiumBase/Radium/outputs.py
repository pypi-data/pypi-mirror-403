from Radium.response import Response
import json

class Outputs:

    @staticmethod
    def _apply_cookies(res, cookies):
        if cookies:
            for key, value in cookies.items():
                res.set_cookie(key=key, value=str(value))
        return res

    @staticmethod
    def TextResponse(response, cookies=None, status="200 OK"):
        res = Response(
            response,
            status=status,
            content_type="text/plain"
        )
        return Outputs._apply_cookies(res, cookies)

    @staticmethod
    def HTMLResponse(response, cookies=None, status="200 OK"):
        res = Response(
            response,
            status=status,
            content_type="text/html"
        )
        return Outputs._apply_cookies(res, cookies)

    @staticmethod
    def HTMLFileResponse(
        file_path,
        layout=None,
        params=None,
        layout_params=None,
        cookies=None,
        status="200 OK"
    ):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if params:
                for key, value in params.items():
                    content = content.replace(f"{{{{{key}}}}}", str(value))

            if layout:
                with open(layout, "r", encoding="utf-8") as f:
                    layout_content = f.read()

                if layout_params:
                    for key, value in layout_params.items():
                        layout_content = layout_content.replace(
                            f"{{{{{key}}}}}", str(value)
                        )

                content = layout_content.replace("{{children}}", content)

            res = Response(
                content,
                status=status,
                content_type="text/html"
            )
            return Outputs._apply_cookies(res, cookies)

        except FileNotFoundError:
            return Response(
                f"<h1>File {file_path} not found.</h1>",
                status="404 Not Found",
                content_type="text/html"
            )

    @staticmethod
    def JSONResponse(response_dict, cookies=None, status="200 OK"):
        res = Response(
            json.dumps(response_dict),
            status=status,
            content_type="application/json"
        )
        return Outputs._apply_cookies(res, cookies)

    @staticmethod
    def RedirectResponse(location, cookies=None, status="302 Found"):
        res = Response(
            "",
            status=status,
            headers=[("Location", location)]
        )
        return Outputs._apply_cookies(res, cookies)
