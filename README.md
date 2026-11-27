# PDF Toolkit
Created by Washim Reja. Contact: 7003714487

## Start fresh on GitHub
1. Create a new empty repository.
2. Unzip `PDFToolkit-project.zip`. Open the `pdf-toolkit-local` folder.
3. Select everything inside it (including the folders `android`, `static` and `.github`) and drag it onto **Add file, Upload files**. Dragging folders keeps their structure. Commit.
4. Open **Actions, Build installers, Run workflow**.
5. When finished, download **PDFToolkit-Windows-Setup** (and **PDFToolkit-Android-APK** if that job succeeds) from Artifacts.

## Windows
Run `PDFToolkit-Setup.exe`. OCR is bundled. Word/Excel/PowerPoint to PDF needs LibreOffice (libreoffice.org).
Developer mode: `pip install -r requirements.txt`, then `python desktop.py`.

## What's in the app
Undo and Redo (header buttons, Ctrl+Z / Ctrl+Y) cover pending edits first, then earlier saved steps such as rotate or delete page.
Images, signatures and stamps are placed once. They then stay selected so you can drag to move, drag the blue corner to resize, and press Delete (or Edit, Delete Selected) to remove. Use Edit, Select / Move to select any pending item later. The Eraser also removes items.

## Android
The APK is a window onto a PDF Toolkit server (the PDF engine, OCR and Word conversion cannot run inside Android).
- **Server on your PC (same Wi-Fi):** `python app.py --lan` prints a link for your phone.
- **Server anywhere:** `PDFTK_KEY=long-random-text docker compose up -d --build`, behind HTTPS.
- **Install:** copy `app-debug.apk` to the phone, allow unknown apps, open it, paste the link, tap Connect. Android 10 or newer.

### If the GitHub Android job keeps failing: build the APK on your PC
1. Install Android Studio (developer.android.com/studio) and open the `android` folder.
2. Wait for Gradle sync to finish. Then **Build, Build Bundle(s) / APK(s), Build APK(s)**.
3. The file is at `android/app/build/outputs/apk/debug/app-debug.apk`.

## Side panes (View tab, or the small buttons at the bottom right)
Switch each panel on or off in **View → Panes** or with the 🖼 🕘 🧰 buttons in the status bar. Your choices are remembered. Drag the thin bar beside a panel to make it wider or narrower (double-click the bar to reset, or use **View → Reset Widths**).
- **Pages:** page thumbnails on the left. Click one to jump to the page. **Right-click** a thumbnail for page actions: rotate, insert blank page before or after, duplicate, move up or down or to a position, extract, print or delete the page.
- **Recent Files:** a list on the left of PDFs you opened lately (desktop app only). A private copy is kept in `%APPDATA%\PDFToolkit\recent` (up to 15 files). Password-protected files stay protected.
- **Quick Tools:** on from the first launch. Buttons on the right for the tools you use most (markup, add text, image, signature and stamp, rotate and delete pages, Find, Print, Undo, Redo, Save, Save As).

## Saving and closing (desktop app)
- **Save** (Ctrl+S) writes your changes straight back to the file you opened, with no dialog. A document that has no file yet (merged, converted, or opened from the recent list copy) asks where to save the first time.
- **Save As** (Ctrl+Shift+S) always asks where to save and then keeps working on the new file.
- A ● next to the file name means there are unsaved changes. Closing the window, the **✕ Close** button, or opening another file while changes are unsaved shows **Save / Don't save / Cancel**.
- In a browser or the Android app, Save and Save As download the file, because a web page cannot overwrite files on your device.

## If the app seems stuck
- The desktop app shows a purple start-up screen at once, then loads. If something fails during start-up it shows the reason instead of a blank window.
- Slow jobs (large files, OCR, print preparation) show **Working… N s** in the status bar.
- A log is kept in `%APPDATA%\PDFToolkit\log.txt`. It lists any request slower than 3 seconds, errors, and the reason if the PDF engine ever crashes. Send that file if a problem keeps happening.

## Notes
Keep your access key private and use HTTPS on the internet. Uploaded files are deleted from the server after 6 hours.
