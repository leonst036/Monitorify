import time

prev_net = None

def _read_net_dev():
    with open("/proc/net/dev", "r") as f:
        next(f)  # Skip header
        next(f)
        net_stats = {}
        for line in f:
            parts = line.split()
            interface = parts[0].strip(":")
            
            rx_bytes = int(parts[1])
            
            tx_bytes = int(parts[9])
            
            net_stats[interface] = (rx_bytes, tx_bytes)
            
    return net_stats

def get_default_interface():
    with open("/proc/net/dev", "r") as f:
        next(f)  # Skip header
        next(f)
        for line in f:
            parts = line.split()
            interface = parts[0].strip(":")
            if interface != "lo":
                return interface

def get_network_usage(interface=None, interval=1, max_speed=None):
    """Set max_speed as bytes per seconds"""
    global prev_net

    if callable(interface):
        interface = interface()
    elif interface is None:
        interface = get_default_interface()

    if prev_net is None:
        prev_net = _read_net_dev()
        time.sleep(interval if interval and interval > 0 else 1)
        current_net = _read_net_dev()
    else:
        current_net = _read_net_dev()

    prev_rx, prev_tx = prev_net.get(interface, (0, 0))
    current_rx, current_tx = current_net.get(interface, (0, 0))

    prev_net = current_net

    diff_rx = max(0, current_rx - prev_rx)
    diff_tx = max(0, current_tx - prev_tx)

    if interval <= 0:
        interval = 1
        
    
    # Return in bytes per second
    rx_bps = diff_rx / interval
    tx_bps = diff_tx / interval
    return rx_bps, tx_bps

def get_total_network_stats():
    net_stats = _read_net_dev()
    total_rx = sum(rx for rx, tx in net_stats.values())
    total_tx = sum(tx for rx, tx in net_stats.values())
    return total_rx, total_tx