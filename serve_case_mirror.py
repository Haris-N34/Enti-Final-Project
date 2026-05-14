from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PORT = 4173


class CaseMirrorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def should_redirect_app_js_document(self) -> bool:
        if self.path.split("?", 1)[0] != "/case-mirror/app.js":
            return False
        accept = self.headers.get("Accept", "")
        fetch_dest = self.headers.get("Sec-Fetch-Dest", "")
        return "text/html" in accept or fetch_dest == "document"

    def redirect_to_app(self):
        self.send_response(302)
        self.send_header("Location", "/case-mirror/")
        self.end_headers()

    def do_GET(self):  # noqa: N802 - stdlib method name
        if self.should_redirect_app_js_document():
            self.redirect_to_app()
            return
        super().do_GET()

    def do_HEAD(self):  # noqa: N802 - stdlib method name
        if self.should_redirect_app_js_document():
            self.redirect_to_app()
            return
        super().do_HEAD()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), CaseMirrorHandler)
    print(f"Case Mirror frontend running at http://127.0.0.1:{PORT}/")
    server.serve_forever()
