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
        
    cache_ram_ussage = get_process_ram_ussage(pids)
    cache_cpu_ussage = get_process_cpu_usage(pids)

    for i, pid in enumerate(pids):
        name = cache.get(pid, "Unknown")
        if isinstance(name, dict):
            name = name.get("name", "Unknown")
        cache[pid] = {
            'name': name,
            'ram_ussage': cache_ram_ussage[i] if i < len(cache_ram_ussage) else 0,
            'cpu_ussage': cache_cpu_ussage[i] if i < len(cache_cpu_ussage) else 0,
        }
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
            info = {'name': info, 'ram_ussage': 0, 'cpu_ussage': 0}
        
        name = info.get('name', 'Unknown')
        ram = info.get('ram_ussage', 0)
        cpu = info.get('cpu_ussage', 0)
        data_list.append({
            'pid': pid,
            'name': name,
            'ram_ussage': ram,
            'cpu_ussage': cpu
        })
    return data_list


def _cache_worker(interval: float = 1.5):
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

_PAGE_SIZE = os.sysconf('SC_PAGE_SIZE') if hasattr(os, 'sysconf') else 4096


def get_process_ram_ussage(pids: list[int]):
    resources_data = []
    for pid in pids:
        try:
            with open(f"/proc/{pid}/statm", "r") as f:
                data = f.read().split()
                # data[1] is the resident set size (RSS) in pages
                ram_bytes = int(data[1]) * _PAGE_SIZE
                resources_data.append(ram_bytes / (1024**2))
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError, Exception):
            resources_data.append(0)
    return resources_data

_previous_cpu_times = {}
_previous_cpu_timestamp = 0.0
_CLK_TCK = float(os.sysconf(os.sysconf_names.get("SC_CLK_TCK", "SC_CLK_TCK"))) if hasattr(os, "sysconf") else 100.0

def get_process_cpu_usage(pids: list[int]):
    global _previous_cpu_times, _previous_cpu_timestamp
    
    current_timestamp = time.time()
    elapsed_seconds = current_timestamp - _previous_cpu_timestamp
    if elapsed_seconds <= 0:
        elapsed_seconds = 0.1
        
    current_cpu_times = {}
    resources_data = []
    
    for pid in pids:
        try:
            with open(f"/proc/{pid}/stat", "r") as f:
                data = f.read().split()
                # data[13] and data[14] are the CPU usage times in clock ticks
                cpu_time = int(data[13]) + int(data[14])
                current_cpu_times[pid] = cpu_time
                
                prev_time = _previous_cpu_times.get(pid)
                if prev_time is not None:
                    delta_ticks = cpu_time - prev_time
                    percent = 100.0 * (delta_ticks / _CLK_TCK) / elapsed_seconds
                    resources_data.append(round(percent, 1))
                else:
                    resources_data.append(0.0)
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError, Exception):
            resources_data.append(0.0)
            
    _previous_cpu_times = current_cpu_times
    _previous_cpu_timestamp = current_timestamp
    
    return resources_data

def get_process_state(pid: int):
    try:
        with open(f"/proc/{pid}/status", "r") as f:
            data = f.read().split('\n')
            for line in data:
                if line.startswith("State:"):
                    if line.split()[1] == 'S':
                        return "Sleeping"
                    elif line.split()[1] == 'R':
                        return "Running"
                    elif line.split()[1] == 'D':
                        return "Waiting"
                    elif line.split()[1] == 'Z':
                        return "Zombie"
                    elif line.split()[1] == 'T':
                        return "Stopped"
                    else:
                        continue
    except (FileNotFoundError, PermissionError, ProcessLookupError, OSError, Exception):
        return "Unknown"

def get_process_running_time(pid: int) -> str:
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.read().split()[0])
            
        with open(f"/proc/{pid}/stat", "r") as f:
            data = f.read()
            end_paren = data.rfind(')')
            if end_paren == -1:
                return "Unknown"
            
            fields = data[end_paren + 1:].split()
            start_time_ticks = float(fields[19])
            
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
    except (FileNotFoundError, PermissionError, ProcessLookupError, OSError, ValueError, IndexError, Exception):
        return "Unknown"
