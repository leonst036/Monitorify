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

_PAGE_SIZE = os.sysconf('SC_PAGE_SIZE') if hasattr(os, 'sysconf') else 4096
_CLK_TCK = float(os.sysconf(os.sysconf_names.get("SC_CLK_TCK", "SC_CLK_TCK"))) if hasattr(os, "sysconf") else 100.0

_previous_cpu_times = {}
_previous_cpu_timestamp = 0.0


def get_process_list():
    # Get active PIDs
    try:
        return [int(p) for p in os.listdir("/proc") if p.isdigit()]
    except (FileNotFoundError, PermissionError, OSError):
        return []


def get_system_uptime() -> float:
    """Fetch total system uptime in seconds once per cycle."""
    try:
        with open("/proc/uptime", "r") as f:
            return float(f.read().split()[0])
    except Exception:
        return 0.0


def _format_running_time(uptime_seconds: float, start_time_ticks: float) -> str:
    """Format process running time from starttime ticks."""
    start_time_seconds = start_time_ticks / _CLK_TCK
    elapsed_seconds = int(uptime_seconds - start_time_seconds)

    if elapsed_seconds < 0:
        return "00:00"

    days, remainder = divmod(elapsed_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
    elif hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def build_process_cache(pids=None):
    """Build process cache in a single pass per process by reading /proc/{pid}/stat."""
    global _previous_cpu_times, _previous_cpu_timestamp
    if pids is None:
        pids = get_process_list()

    current_timestamp = time.time()
    elapsed_seconds = current_timestamp - _previous_cpu_timestamp
    if elapsed_seconds <= 0:
        elapsed_seconds = 0.1

    uptime = get_system_uptime()

    state_map = {
        'S': 'Sleeping',
        'R': 'Running',
        'D': 'Waiting',
        'Z': 'Zombie',
        'T': 'Stopped',
        't': 'Stopped'
    }

    cache = {}
    new_cpu_times = {}

    for pid in pids:
        try:
            with open(f"/proc/{pid}/stat", "r") as f:
                data = f.read()

            start = data.find('(')
            end = data.rfind(')')
            if start == -1 or end == -1:
                continue

            name = data[start + 1:end]
            fields = data[end + 1:].split()

            # State
            state = state_map.get(fields[0], "Unknown")

            # CPU times: utime (field 11) + stime (field 12)
            utime = int(fields[11])
            stime = int(fields[12])
            cpu_time = utime + stime
            new_cpu_times[pid] = cpu_time

            # CPU percentage calculation
            prev_time = _previous_cpu_times.get(pid)
            if prev_time is not None:
                delta_ticks = cpu_time - prev_time
                cpu_usage = round(100.0 * (delta_ticks / _CLK_TCK) / elapsed_seconds, 1)
            else:
                cpu_usage = 0.0

            # Running time: starttime (field 19)
            start_time_ticks = float(fields[19])
            running_time = _format_running_time(uptime, start_time_ticks)

            # RAM usage: rss (field 21 in pages)
            ram_bytes = int(fields[21]) * _PAGE_SIZE
            ram_usage = round(ram_bytes / (1024 ** 2), 1)

            cache[pid] = {
                'name': name,
                'ram_ussage': ram_usage,
                'cpu_ussage': cpu_usage,
                'state': state,
                'running_time': running_time,
            }
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError, ValueError, IndexError):
            continue

    _previous_cpu_times = new_cpu_times
    _previous_cpu_timestamp = current_timestamp

    return cache


def get_process_data_list(pids, cache):
    if not isinstance(cache, dict):
        cache = {}
    if pids is None:
        return []
    
    data_list = []
    for pid in pids:
        info = cache.get(pid, {})
        if isinstance(info, str):
            info = {'name': info, 'ram_ussage': 0, 'cpu_ussage': 0, 'state': 'Unknown', 'running_time': 'Unknown'}
        
        name = info.get('name', 'Unknown')
        ram = info.get('ram_ussage', 0)
        cpu = info.get('cpu_ussage', 0)
        state = info.get('state', 'Unknown')
        running_time = info.get('running_time', 'Unknown')
        data_list.append({
            'pid': pid,
            'name': name,
            'ram_ussage': ram,
            'cpu_ussage': cpu,
            'state': state,
            'running_time': running_time
        })
    return data_list


def _cache_worker(interval: float = 2.0):
    global _current_cache, _current_pids, _current_items_data, _cache_version
    while True:
        pids = get_process_list()
        if pids:
            cache = build_process_cache(pids)
            items_data = get_process_data_list(pids, cache)
            with _cache_lock:
                _current_pids = pids
                _current_cache = cache
                _current_items_data = items_data
                _cache_version += 1
        time.sleep(interval)


def start_process_cache_thread(interval: float = 2.0):
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
    data_list = get_process_data_list(pids, cache)
    return version, pids, data_list


def get_latest_process_items_data():
    """Return (version, count, items_data_list)."""
    global _current_cache, _current_pids, _current_items_data, _cache_version
    start_process_cache_thread()
    with _cache_lock:
        if _cache_version == 0:
            pids = get_process_list()
            if pids:
                cache = build_process_cache(pids)
                _current_pids = pids
                _current_cache = cache
                _current_items_data = get_process_data_list(pids, cache)
                _cache_version = 1
        version = _cache_version
        count = len(_current_pids)
        items_data = list(_current_items_data)

    return version, count, items_data


def _format_process_item(d: dict) -> str:
    ram_mb = f"{d['ram_ussage']:.1f} MB" if isinstance(d['ram_ussage'], (int, float)) else "0.0 MB"
    
    cpu_val = d.get('cpu_ussage', 0.0)
    cpu_str = f"{cpu_val:.1f}%" if isinstance(cpu_val, (int, float)) else "0.0%"
    
    name = str(d.get('name', ''))
    if len(name) > 25:
        name = name[:22] + "..."
        
    return f"[bold #61afef]{d.get('pid', 0):>6d}[/bold #61afef]  {name:<25} [yellow]{ram_mb:>10}[/yellow]  [red]{cpu_str:>7}[/red]"


def get_latest_process_items():
    """Return ListItems for UI hot swap."""
    version, count, items_data = get_latest_process_items_data()
    list_items = [ListItem(Static(_format_process_item(d))) for d in items_data]
    return version, count, list_items


def get_process_ram_ussage(pids: list[int]):
    """Deprecated: Standalone RAM fetcher."""
    cache = build_process_cache(pids)
    return [cache.get(pid, {}).get('ram_ussage', 0.0) for pid in pids]


def get_process_cpu_usage(pids: list[int]):
    """Deprecated: Standalone CPU fetcher."""
    cache = build_process_cache(pids)
    return [cache.get(pid, {}).get('cpu_ussage', 0.0) for pid in pids]


def get_process_state(pid: int):
    """Standalone State fetcher."""
    cache = build_process_cache([pid])
    return cache.get(pid, {}).get('state', 'Unknown')


def get_process_running_time(pid: int) -> str:
    """Standalone Running Time fetcher."""
    cache = build_process_cache([pid])
    return cache.get(pid, {}).get('running_time', 'Unknown')
