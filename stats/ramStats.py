def get_ram_usage(unit="percent"):
    with open("/proc/meminfo", "r") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                mem_available = int(line.split()[1])
            if line.startswith("MemTotal:"):
                mem_total = int(line.split()[1])
    
    if unit == "percent":
        return round((1.0 - (mem_available / mem_total)) * 100, 2)
    elif unit == "raw":
        return 1.0 - (mem_available / mem_total)
    else:
        raise ValueError("Invalid unit. Use 'percent' or 'raw'.")