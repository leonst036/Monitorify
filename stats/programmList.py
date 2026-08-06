import os
import time
import threading

# pyrefly: ignore [missing-import]
from textual.widgets import ListItem, Static

_cache_lock = threading.Lock()
_current_cache = {}
_current_pids = []
_current_items_data = []
_cache_version = 0
_thread_started = False


def get_process_list():
    # Get active PIDs
    try:
        return [int(p) for p in os.listdir("/proc") if p.isdigit()]
    except (FileNotFoundError, PermissionError, OSError):
        return []


def build_process_cache(pids=None):
    if pids is None:
        pids = get_process_list()
    cache = {}
    for pid in pids:
        try:
            # Parse stat file
            with open(f"/proc/{pid}/stat", "r") as f:
                data = f.read()
                start = data.find('(') + 1
                end = data.rfind(')')
                if start > 0 and end > 0:
                    cache[pid] = data[start:end]
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError, Exception):
            continue
    return cache


def get_process_names(pids, cache):
    if not isinstance(cache, dict):
        cache = {}
    if pids is None:
        return []
    
    names = []
    try:
        for pid in pids:
            try:
                names.append(cache.get(pid, "Unknown"))
            except Exception:
                names.append("Unknown")
    except Exception:
        return []
    return names


def _cache_worker(interval: float = 1.5):
    global _current_cache, _current_pids, _current_items_data, _cache_version
    while True:
        pids = get_process_list()
        if pids:
            cache = build_process_cache(pids)
            names = get_process_names(pids, cache)
            items_data = [f"[bold #61afef]{pid:>6d}[/bold #61afef]  {name}" for pid, name in zip(pids, names)]
            with _cache_lock:
                _current_pids = pids
                _current_cache = cache
                _current_items_data = items_data
                _cache_version += 1
        time.sleep(interval)


def start_process_cache_thread(interval: float = 1.5):
    global _thread_started
    with _cache_lock:
        if _thread_started:
            return
        _thread_started = True

    t = threading.Thread(target=_cache_worker, args=(interval,), daemon=True)
    t.start()


def get_latest_process_data():
    """Return latest process data tuple."""
    global _current_cache, _current_pids, _cache_version
    start_process_cache_thread()
    with _cache_lock:
        if _cache_version == 0:
            pids = get_process_list()
            if pids:
                cache = build_process_cache(pids)
                _current_pids = pids
                _current_cache = cache
                _cache_version = 1
        version = _cache_version
        pids = list(_current_pids)
        cache = dict(_current_cache)
    names = get_process_names(pids, cache)
    return version, pids, names


def get_latest_process_items_data():
    """Return (version, count, items_data_list)."""
    global _current_cache, _current_pids, _current_items_data, _cache_version
    start_process_cache_thread()
    with _cache_lock:
        if _cache_version == 0:
            pids = get_process_list()
            if pids:
                cache = build_process_cache(pids)
                names = get_process_names(pids, cache)
                _current_pids = pids
                _current_cache = cache
                _current_items_data = [f"[bold #61afef]{pid:>6d}[/bold #61afef]  {name}" for pid, name in zip(pids, names)]
                _cache_version = 1
        version = _cache_version
        count = len(_current_pids)
        items_data = list(_current_items_data)

    return version, count, items_data


def get_latest_process_items():
    """Return ListItems for UI hot swap."""
    version, count, items_data = get_latest_process_items_data()
    list_items = [ListItem(Static(text)) for text in items_data]
    return version, count, list_items



