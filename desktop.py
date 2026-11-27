"""PDF Toolkit desktop launcher: shows a window at once, then starts the local server inside it."""
import os, sys, time, socket, shutil, secrets, threading, traceback, faulthandler
from pathlib import Path
import webview

BASE = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
DATA = Path(os.environ.get("APPDATA") or (Path.home() / ".local" / "share")) / "PDFToolkit"
LOGFILE = DATA / "log.txt"

def log(msg):
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        if LOGFILE.exists() and LOGFILE.stat().st_size > 1_000_000: LOGFILE.write_text("", encoding="utf-8")
        with open(LOGFILE, "a", encoding="utf-8") as fh: fh.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
    except Exception: pass

try:  # if the PDF engine ever crashes hard, Python writes the reason into the log
    DATA.mkdir(parents=True, exist_ok=True); _fh = open(LOGFILE, "a", buffering=1); faulthandler.enable(file=_fh)
except Exception: pass

# Help the app find Tesseract and LibreOffice without the user editing PATH.
extra = [BASE / "tesseract", r"C:\Program Files\Tesseract-OCR", r"C:\Program Files\LibreOffice\program",
         r"C:\Program Files (x86)\LibreOffice\program", "/Applications/LibreOffice.app/Contents/MacOS",
         "/opt/homebrew/bin", "/usr/local/bin"]
os.environ["PATH"] = os.pathsep.join([str(p) for p in extra if Path(p).exists()] + [os.environ.get("PATH", "")])
if (BASE / "tesseract" / "tessdata").exists():  # optional bundled Tesseract
    os.environ["TESSDATA_PREFIX"] = str(BASE / "tesseract" / "tessdata")
os.environ.setdefault("PDFTK_RECENT", str(DATA / "recent"))   # recent files are kept in the desktop app only
os.environ.setdefault("PDFTK_LOG", str(LOGFILE))

# "Open with PDF Toolkit": Windows passes the file path as an argument.
FILES = [os.path.abspath(a) for a in sys.argv[1:] if a.lower().endswith(".pdf") and os.path.isfile(a)]
toolkit = None

SPLASH = """<!doctype html><meta charset="utf-8"><title>PDF Toolkit</title><style>
html,body{height:100%;margin:0}body{display:flex;align-items:center;justify-content:center;flex-direction:column;gap:16px;font:16px "Segoe UI",system-ui,sans-serif;
background:linear-gradient(120deg,#6d28d9,#db2777 60%,#f97316);color:#fff}h1{margin:0;font-size:34px}.sp{width:38px;height:38px;border:5px solid rgba(255,255,255,.35);border-top-color:#fff;border-radius:50%;animation:r 1s linear infinite}
@keyframes r{to{transform:rotate(360deg)}}small{opacity:.85;max-width:520px;text-align:center}</style>
<h1>PDF Toolkit</h1><div class="sp"></div><div id="m">Starting…</div><small id="s"></small>
<script>setTimeout(()=>{document.getElementById('s').textContent='Still starting. The first start can take a little longer while Windows checks the program files.'},12000)</script>"""

def error_page(text):
    import html
    return ("<!doctype html><meta charset='utf-8'><body style='font:15px Segoe UI,sans-serif;padding:32px;color:#222'><h2 style='color:#b91c1c'>PDF Toolkit could not start</h2>"
            f"<pre style='white-space:pre-wrap;background:#f4f4f4;padding:12px;border-radius:8px'>{html.escape(text)}</pre>"
            f"<p>Details were saved to:<br><code>{html.escape(str(LOGFILE))}</code></p>")

def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); return s.getsockname()[1]

def _dialog(kind):
    """Native file-dialog constants (newer pywebview uses FileDialog.OPEN/SAVE, older uses OPEN_DIALOG/SAVE_DIALOG)."""
    fd = getattr(webview, "FileDialog", None)
    return getattr(fd, kind) if fd is not None else getattr(webview, kind + "_DIALOG")

class Api:
    """Methods the page can call (window.pywebview.api.*). Names starting with _ are not exposed."""
    def __init__(self): self._window = None; self._force = False
    def pick_open(self):
        r = self._window.create_file_dialog(_dialog("OPEN"), allow_multiple=False, file_types=("PDF files (*.pdf)", "All files (*.*)"))
        return [str(x) for x in r] if r else []
    def pick_save(self, name="document.pdf", directory=""):
        r = self._window.create_file_dialog(_dialog("SAVE"), directory=directory or "", save_filename=name, file_types=("PDF files (*.pdf)",))
        if isinstance(r, (list, tuple)): r = r[0] if r else None
        return str(r) if r else ""
    def close_app(self):
        self._force = True; self._window.destroy()

def boot(window, api):
    """Runs after the window is on screen: load the PDF engine, start the server, then show the app."""
    global toolkit
    try:
        t0 = time.time(); log("starting")
        import app as toolkit_module
        toolkit = toolkit_module
        toolkit.DESKTOP = True; toolkit.DESKTOP_TOKEN = secrets.token_hex(16)     # lets the page open and save real files on this PC
        if FILES: toolkit.STARTUP.append(FILES[0])
        for extra_file in FILES[1:]:  # several files selected: one window each
            import subprocess
            subprocess.Popen([sys.executable, extra_file] if getattr(sys, "frozen", False) else [sys.executable, __file__, extra_file])
        from werkzeug.serving import make_server
        port = free_port(); server = make_server("127.0.0.1", port, toolkit.app, threaded=True)
        api._server = server
        threading.Thread(target=server.serve_forever, daemon=True).start()
        for _ in range(150):  # wait until the server answers (up to 15 s)
            try: socket.create_connection(("127.0.0.1", port), 0.2).close(); break
            except OSError: time.sleep(0.1)
        else: raise RuntimeError("The local server did not start.")
        log(f"server ready on port {port} after {time.time() - t0:.1f}s")
        window.load_url(f"http://127.0.0.1:{port}")
    except Exception:
        text = traceback.format_exc(); log("START FAILED\n" + text)
        window.load_html(error_page(text))

def main():
    api = Api(); api._server = None
    try: webview.settings["ALLOW_DOWNLOADS"] = True  # exports (zip, Word, images) still use the browser download
    except Exception: pass
    window = webview.create_window("PDF Toolkit", html=SPLASH, js_api=api, width=1100, height=820, min_size=(760, 560))
    api._window = window

    def on_closing():
        """Closing the window with unsaved edits: let the page ask Save / Don't save / Cancel."""
        if api._force: return True
        try: dirty = window.evaluate_js("typeof isDirty==='function' && isDirty()")
        except Exception: dirty = False
        if dirty:
            window.evaluate_js("askClose()"); return False       # keep the window open; the page closes it after the answer
        return True
    window.events.closing += on_closing
    webview.start(boot, (window, api))
    try:
        if api._server: api._server.shutdown()
    except Exception: pass
    if toolkit: shutil.rmtree(toolkit.WORK, ignore_errors=True)
    log("closed")

if __name__ == "__main__":
    main()
