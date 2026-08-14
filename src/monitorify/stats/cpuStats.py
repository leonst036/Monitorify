import time

prev_cpu = None

def _read_cpu_times():
    with open("/proc/stat", "r") as f:
        line = f.readline()
    parts = [float(x) for x in line.split()[1:]]
    idle_time = parts[3] + parts[4]  # idle + iowait
    total_time = sum(parts)
    return idle_time, total_time

def get_cpu_usage(interval=None, unit="percent"):
    """Calculate total CPU usage via /proc/stat."""
    global prev_cpu
    
    if prev_cpu is None:
        t1_idle, t1_total = _read_cpu_times()
        time.sleep(interval if interval and interval > 0 else 0.1)
        t2_idle, t2_total = _read_cpu_times()
        prev_cpu = (t2_idle, t2_total)
        diff_total = t2_total - t1_total
        diff_idle = t2_idle - t1_idle
    elif interval is not None and interval > 0:
        t1_idle, t1_total = _read_cpu_times()
        time.sleep(interval)
        t2_idle, t2_total = _read_cpu_times()
        prev_cpu = (t2_idle, t2_total)
        diff_total = t2_total - t1_total
        diff_idle = t2_idle - t1_idle
    else:
        t2_idle, t2_total = _read_cpu_times()
        prev_idle, prev_total = prev_cpu
        prev_cpu = (t2_idle, t2_total)
        diff_total = t2_total - prev_total
        diff_idle = t2_idle - prev_idle

    if diff_total == 0:
        return 0.0
    # Return requested unit
    if unit == "percent":
        return round((1.0 - (diff_idle / diff_total)) * 100, 2)
    elif unit == "raw":
        return 1.0 - (diff_idle / diff_total)
    else:
        raise ValueError("Invalid unit. Use 'percent' or 'raw'.")