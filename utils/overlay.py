# overlay.py
"""Simple overlay window using tkinter to show recent plays for a track.
This is intentionally lightweight: creates a borderless, topmost window
centered on the primary screen and destroys itself after `duration` seconds.
"""
import threading
import time
from datetime import datetime
from typing import List, Tuple
from config.config_manager import config
from utils.safe_print import safe_print

try:
    import tkinter as tk
    from tkinter import font as tkfont
except Exception:
    tk = None


class Overlay:
    def __init__(self):
        self._thread = None

    def show(self, title: str, artist: str, history: List[Tuple], duration: float = None) -> None:
        """Show overlay non-blocking. `history` is list of (timestamp, play_percentage, playback_status, app_name)."""
        if tk is None:
            safe_print("[overlay] tkinter unavailable; cannot show overlay")
            return

        if duration is None:
            duration = config.get("display.overlay_duration_seconds", 5)

        # Start a thread to run the tkinter window so it won't block async loop
        t = threading.Thread(target=self._run_window, args=(title, artist, history, duration), daemon=True)
        t.start()
        self._thread = t

    def _run_window(self, title: str, artist: str, history: List[Tuple], duration: float):
        try:
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)

            # Attempt semi-transparency if supported
            try:
                root.attributes("-alpha", 0.85)
            except Exception:
                pass

            # Build content
            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()

            win_w = min(900, int(screen_w * 0.8))
            win_h = min(300, int(screen_h * 0.25))

            x = (screen_w - win_w) // 2
            y = int(screen_h * 0.1)

            root.geometry(f"{win_w}x{win_h}+{x}+{y}")

            # Frame with background
            frame = tk.Frame(root, bg="#111111")
            frame.pack(fill=tk.BOTH, expand=True)

            # Fonts
            try:
                title_font = tkfont.Font(family="Segoe UI", size=24, weight="bold")
                meta_font = tkfont.Font(family="Segoe UI", size=14)
                small_font = tkfont.Font(family="Segoe UI", size=12)
            except Exception:
                title_font = None
                meta_font = None
                small_font = None

            # Title
            title_text = f"{title}"
            if artist:
                title_text += f" — {artist}"

            lbl_title = tk.Label(frame, text=title_text, fg="#ffffff", bg="#111111", wraplength=win_w-40)
            if title_font:
                lbl_title.config(font=title_font)
            lbl_title.pack(pady=(16, 6))

            # History lines
            if history:
                # Show up to 5 recent entries
                history_frame = tk.Frame(frame, bg="#111111")
                history_frame.pack(padx=20, pady=(0, 12), fill=tk.BOTH, expand=True)

                for ts, pct, status, app in history:
                    try:
                        # ts stored as ISO format in DB
                        dt = datetime.fromisoformat(ts)
                        ts_str = dt.strftime(config.get_timestamp_format())
                    except Exception:
                        ts_str = str(ts)

                    pct_str = f"{pct}%" if pct is not None else "—"
                    line = f"{ts_str} | {pct_str} | {status or 'Unknown'} | {app or 'Unknown'}"
                    lbl = tk.Label(history_frame, text=line, fg="#dddddd", bg="#111111")
                    if small_font:
                        lbl.config(font=small_font)
                    lbl.pack(anchor="w")

            # Auto-destroy after duration seconds
            def close_after():
                time.sleep(duration)
                try:
                    root.destroy()
                except Exception:
                    pass

            threading.Thread(target=close_after, daemon=True).start()
            root.mainloop()

        except Exception as e:
            safe_print(f"[overlay] 显示叠加层失败: {e}")


# 全局实例
overlay = Overlay()
