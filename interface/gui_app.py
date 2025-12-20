import sys
import threading
import queue
import logging
import time
import platform
try:
    import tkinter as tk
    from tkinter.scrolledtext import ScrolledText
except Exception:
    tk = None

try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:
    pystray = None


class GuiLoggerHandler(logging.Handler):
    def __init__(self, write_cb):
        super().__init__()
        self.write_cb = write_cb

    def emit(self, record):
        try:
            msg = self.format(record)
            self.write_cb(msg + "\n")
        except Exception:
            pass


class StdoutRedirector:
    def __init__(self, write_cb, orig=None):
        self.write_cb = write_cb
        self.orig = orig or sys.__stdout__

    def write(self, s):
        if s:
            try:
                self.write_cb(s)
            except Exception:
                pass
        try:
            self.orig.write(s)
        except Exception:
            pass

    def flush(self):
        try:
            self.orig.flush()
        except Exception:
            pass


class GuiApp:
    def __init__(self, title="PlaylistControl"):
        self.title = title
        self.root = None
        self.text = None
        self.queue = queue.Queue()
        self._running = False
        self._tray_icon = None

    def _create_tray_image(self, size=64, color1=(0, 120, 215), color2=(255, 255, 255)):
        image = Image.new('RGB', (size, size), color1)
        d = ImageDraw.Draw(image)
        d.rectangle([size//4, size//4, 3*size//4, 3*size//4], fill=color2)
        return image

    def _install_tray(self):
        if pystray is None:
            return

        def on_show(icon, item):
            self.show()

        def on_hide(icon, item):
            self.hide()

        def on_quit(icon, item):
            icon.stop()
            self.quit()

        image = self._create_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem('Show', on_show),
            pystray.MenuItem('Hide', on_hide),
            pystray.MenuItem('Quit', on_quit)
        )
        self._tray_icon = pystray.Icon('PlaylistControl', image, 'PlaylistControl', menu)

        def tray_loop():
            try:
                self._tray_icon.run()
            except Exception:
                pass

        t = threading.Thread(target=tray_loop, daemon=True)
        t.start()

    def write(self, s):
        # push to queue for main thread to consume
        self.queue.put(s)

    def _flush_queue(self):
        while not self.queue.empty():
            try:
                s = self.queue.get_nowait()
            except Exception:
                break
            if self.text is not None:
                try:
                    self.text.configure(state='normal')
                    self.text.insert('end', s)
                    self.text.see('end')
                    self.text.configure(state='disabled')
                except Exception:
                    pass

    def show(self):
        if self.root is None:
            return
        try:
            self.root.deiconify()
            self.root.lift()
        except Exception:
            pass

    def hide(self):
        if self.root is None:
            return
        try:
            self.root.withdraw()
        except Exception:
            pass

    def quit(self):
        self._running = False
        try:
            if self.root:
                self.root.quit()
        except Exception:
            pass

    def run(self, auto_start=False, monitor=None, start_hidden=False):
        if tk is None:
            # tkinter not available; fallback to console
            return

        self._running = True
        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry('700x400')

        frame = tk.Frame(self.root)
        frame.pack(fill='both', expand=True)

        self.text = ScrolledText(frame, state='disabled')
        self.text.pack(fill='both', expand=True)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill='x')

        def on_quit():
            self.quit()

        def on_hide():
            self.hide()

        tk.Button(btn_frame, text='Hide', command=on_hide).pack(side='right')
        tk.Button(btn_frame, text='Quit', command=on_quit).pack(side='right')

        # polling loop to flush queue
        def poll():
            self._flush_queue()
            if self._running:
                self.root.after(200, poll)
            else:
                try:
                    self.root.destroy()
                except Exception:
                    pass

        # install tray icon if available (do this before hiding so tray is usable)
        if pystray is not None:
            try:
                self._install_tray()
            except Exception:
                pass

        # redirect stdout/stderr and logging
        sys.stdout = StdoutRedirector(self.write, orig=sys.__stdout__)
        sys.stderr = StdoutRedirector(self.write, orig=sys.__stderr__)
        handler = GuiLoggerHandler(self.write)
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        logging.getLogger().addHandler(handler)

        # auto-start monitoring if requested
        if auto_start and monitor is not None:
            try:
                import asyncio
                threading.Thread(target=lambda: asyncio.run(monitor.monitor_media()), daemon=True).start()
            except Exception:
                pass

        # optionally start hidden (hide window but keep tray installed)
        if start_hidden:
            try:
                self.root.withdraw()
            except Exception:
                pass

        self.root.after(200, poll)
        self.root.mainloop()
