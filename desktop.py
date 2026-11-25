"""PDF Toolkit desktop launcher: runs the local server inside a native window."""
import os, sys, time, socket, shutil, secrets, threading
from pathlib import Path
import webview

BASE = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent

# Help the app find Tesseract and LibreOffice without the user editing PATH.
extra = [BASE / "tesseract", r"C:\Program Files\Tesseract-OCR", r"C:\Program Files\LibreOffice\program",
         r"C:\Program Files (x86)\LibreOffice\program", "/Applications/LibreOffice.app/Contents/MacOS",
         "/opt/homebrew/bin", "/usr/local/bin"]
os.environ["PATH"] = os.pathsep.join([str(p) for p in extra if Path(p).exists()] + [os.environ.get("PATH", "")])
if (BASE / "tesseract" / "tessdata").exists():  # optional bundled Tesseract
    os.environ["TESSDATA_PREFIX"] = str(BASE / "tesseract" / "tessdata")

os.environ.setdefault("PDFTK_RECENT", str(Path(os.environ.get("APPDATA") or (Path.home() / ".local" / "share")) / "PDFToolkit" / "recent"))
import app as toolkit  # noqa: E402  (after PATH is prepared)

# "Open with PDF Toolkit": Windows passes the file path as an argument.
FILES = [os.path.abspath(a) for a in sys.argv[1:] if a.lower().endswith(".pdf") and os.path.isfile(a)]
if FILES: toolkit.STARTUP.append(FILES[0])
for extra_file in FILES[1:]:  # several files selected: one window each
    import subprocess
    subprocess.Popen([sys.executable, extra_file] if getattr(sys, "frozen", False) else [sys.executable, __file__, extra_file])

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

def main():
    port = free_port(); api = Api()
    toolkit.DESKTOP = True; toolkit.DESKTOP_TOKEN = secrets.token_hex(16)     # lets the page open and save real files on this PC
    threading.Thread(target=lambda: toolkit.app.run("127.0.0.1", port, threaded=True, use_reloader=False),
                     daemon=True).start()
    for _ in range(100):  # wait until the server answers
        try: socket.create_connection(("127.0.0.1", port), 0.2).close(); break
        except OSError: time.sleep(0.1)
    try: webview.settings["ALLOW_DOWNLOADS"] = True  # exports (zip, Word, images) still use the browser download
    except Exception: pass
    window = webview.create_window("PDF Toolkit", f"http://127.0.0.1:{port}", js_api=api, width=1100, height=820, min_size=(760, 560))
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
    webview.start()
    shutil.rmtree(toolkit.WORK, ignore_errors=True)

if __name__ == "__main__":
    main()
