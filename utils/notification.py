"""
Simple cross-platform notification helper.
Tries plyer.notification, then win10toast, then falls back to logger.info.
Provides a notify_duplicate(...) convenience function used by database when a duplicate is detected.
"""
from typing import Optional
from config.config_manager import config
from utils.logger import logger


def _notify_with_plyer(title: str, message: str, duration: int = 5) -> bool:
    try:
        from plyer import notification
        notification.notify(title=title, message=message, timeout=duration)
        return True
    except Exception:
        return False


def _notify_with_win10toast(title: str, message: str, duration: int = 5) -> bool:
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        # threaded=True to avoid blocking
        toaster.show_toast(title, message, duration=duration, threaded=True)
        return True
    except Exception:
        return False


def notify(title: str, message: str, duration: int = 5) -> None:
    """Send a desktop notification if possible; otherwise log as info.

    Honors `config.notifications.duplicates.preferred_backend` if set to
    "win10toast" or "plyer". Falls back safely to other backends or logging.
    """
    preferred = None
    try:
        preferred = config.get("notifications.duplicates.preferred_backend", None)
    except Exception:
        preferred = None

    # If preferred is win10toast, try it first
    if preferred == "win10toast":
        try:
            if _notify_with_win10toast(title, message, duration):
                return
        except Exception:
            pass

        # then try plyer
        try:
            if _notify_with_plyer(title, message, duration):
                return
        except Exception:
            pass

    else:
        # default: plyer first
        try:
            if _notify_with_plyer(title, message, duration):
                return
        except Exception:
            pass

        try:
            if _notify_with_win10toast(title, message, duration):
                return
        except Exception:
            pass

    # Fallback: write to logger
    try:
        logger.info(f"通知: {title} - {message}")
    except Exception:
        # Last resort: print
        try:
            from utils.safe_print import safe_print
            safe_print(f"通知: {title} - {message}")
        except Exception:
            pass


def notify_duplicate(title: str, artist: str, app_name: Optional[str] = None, timestamp: Optional[str] = None) -> None:
    """Convenience wrapper for duplicate-song notifications."""
    enabled = config.get("notifications.duplicates.enabled", True)
    if not enabled:
        return

    duration = config.get("notifications.duplicates.duration_seconds", 5)
    use_toast = config.get("notifications.duplicates.use_toast", True)

    display_title = "重复歌曲检测"
    display_message = f"{title} — {artist}"
    if app_name:
        display_message += f" ({app_name})"
    if timestamp:
        display_message += f" 在 {timestamp} 被检测到"

    # If user disabled toast, still call notify() which will fallback to logger
    if use_toast:
        notify(display_title, display_message, duration=duration)
    else:
        # Don't attempt toast; just log
        try:
            logger.info(f"重复歌曲: {display_message}")
        except Exception:
            try:
                from utils.safe_print import safe_print
                safe_print(f"重复歌曲: {display_message}")
            except Exception:
                pass
