"""Render PDF pages to PNG for visual (Rule 10) checks.

xpdf's pdftoppm is not installed on this machine (filesystem search, 2026-09-23) and
PyMuPDF's native DLL is blocked by Application Control. This renders with Mozilla
pdf.js (a full rasteriser) inside headless Chrome, driven over the DevTools protocol:
navigate, wait until pdf.js reports the page rendered, then read the canvas pixels.

Usage: python revision-artifacts/tools/render_pages.py PDF OUTDIR [--pages 1,5-7] [--dpi 150]
Assets: render.html + pdf.min.js + pdf.worker.min.js (pdfjs-dist 3.11.174) in ASSETS.
"""
import argparse, base64, http.server, json, pathlib, shutil, socketserver, subprocess, sys
import tempfile, threading, time, urllib.parse, urllib.request
import websocket  # websocket-client

ASSETS = pathlib.Path(r"C:\Users\Lenovo\AppData\Local\Temp\claude\D--scada"
                      r"\c26ddc76-d8d4-4d82-bb15-6d74c8510ab9\scratchpad\render")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9333


def page_list(spec, n):
    if not spec:
        return list(range(1, n + 1))
    out = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *x, **k):
        super().__init__(*x, directory=str(ASSETS), **k)

    def log_message(self, *x):
        pass


class Cdp:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=60)
        self.i = 0

    def call(self, method, **params):
        self.i += 1
        self.ws.send(json.dumps(dict(id=self.i, method=method, params=params)))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.i:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})

    def eval(self, expr):
        return self.call("Runtime.evaluate", expression=expr, returnByValue=True)["result"].get("value")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("outdir")
    ap.add_argument("--pages", default=""); ap.add_argument("--dpi", type=float, default=150)
    a = ap.parse_args()
    import pypdf
    n = len(pypdf.PdfReader(a.pdf).pages)
    scale = a.dpi / 72.0
    shutil.copy2(a.pdf, ASSETS / "doc.pdf")
    out = pathlib.Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    profile = tempfile.mkdtemp(prefix="cdp-profile-")
    chrome = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--remote-allow-origins=*",
                               "--remote-debugging-port=%d" % CDP_PORT, "--user-data-dir=" + profile,
                               "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                tabs = json.load(urllib.request.urlopen("http://127.0.0.1:%d/json" % CDP_PORT))
                pages = [t for t in tabs if t["type"] == "page"]
                if pages:
                    break
            except OSError:
                pass
            time.sleep(0.2)
        cdp = Cdp(pages[0]["webSocketDebuggerUrl"])
        with socketserver.TCPServer(("127.0.0.1", 0), Quiet) as srv:
            port = srv.server_address[1]
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            for p in page_list(a.pages, n):
                url = "http://127.0.0.1:%d/render.html?%s" % (port, urllib.parse.urlencode(
                    dict(file="doc.pdf", page=p, scale=scale, t=time.time())))
                cdp.call("Page.navigate", url=url)
                title = ""
                for _ in range(300):
                    title = cdp.eval("document.title") or ""
                    if title == "done" or title.startswith("error"):
                        break
                    time.sleep(0.1)
                if title != "done":
                    raise RuntimeError("page %d: %s" % (p, title or "timeout"))
                data = cdp.eval("document.getElementById('c').toDataURL('image/png')")
                png = out / ("page-%02d.png" % p)
                png.write_bytes(base64.b64decode(data.split(",", 1)[1]))
                print(png, png.stat().st_size)
            srv.shutdown()
    finally:
        chrome.terminate()


if __name__ == "__main__":
    sys.exit(main())
