import os

def get_real_disks() -> list:
    disks = []
    
    with open("/proc/diskstats", "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 3:
                continue
            
            disk_name = parts[2]
            # Check if it is a real physical disk (not a partition or virtual device)
            if not os.path.exists(f"/sys/block/{disk_name}/device"):
                continue
            
            disks.append(disk_name)
            
    return disks

def get_disk_IO(disks: list = None) -> dict:
    if disks is None:
        disks = get_real_disks()
        
    disk_io = {}
    
    with open("/proc/diskstats", "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 14:
                continue
            
            disk_name = parts[2]
            if disk_name in disks:
                # Sector size in Linux is 512 bytes
                read_bytes = int(parts[5]) * 512
                write_bytes = int(parts[9]) * 512
                disk_io[disk_name] = {
                    "read_bytes": read_bytes,
                    "write_bytes": write_bytes,
                    "reads": int(parts[3]),
                    "writes": int(parts[7]),
                }
            
    return disk_io

def get_disk_storage(disks: list = None) -> dict:
    if disks is None:
        disks = get_real_disks()
        
    disk_storage = {}
    
    # Map mount points for each device partition
    mounts = {}
    if os.path.exists("/proc/mounts"):
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2 and parts[0].startswith("/dev/"):
                    mounts.setdefault(parts[0], parts[1])
    
    for disk in disks:
        # Read total raw hardware capacity from /sys/block/<disk>/size (512-byte sectors)
        total_hw = 0
        size_file = f"/sys/block/{disk}/size"
        if os.path.exists(size_file):
            try:
                with open(size_file, "r") as f:
                    total_hw = int(f.read().strip()) * 512
            except (ValueError, IOError):
                total_hw = 0
                
        total_fs = 0
        used_fs = 0
        free_fs = 0
        
        for dev_path, mount_point in mounts.items():
            dev_name = os.path.basename(dev_path)
            # Match disk or its partitions (e.g. sda1 -> sda, nvme0n1p1 -> nvme0n1)
            if dev_name == disk or dev_name.startswith(disk):
                try:
                    st = os.statvfs(mount_point)
                    total_fs += st.f_blocks * st.f_frsize
                    free_fs += st.f_bavail * st.f_frsize
                    used_fs += (st.f_blocks - st.f_bfree) * st.f_frsize
                except OSError:
                    pass
                    
        total = total_fs if total_fs > 0 else total_hw
        used = used_fs
        free = free_fs if total_fs > 0 else max(0, total_hw - used_fs)
        
        disk_storage[disk] = {
            "total": total,
            "used": used,
            "free": free,
        }
    
    return disk_storage

if __name__ == "__main__":
    disks = get_real_disks()
    disk_IO = get_disk_IO(disks)
    disk_storage = get_disk_storage(disks)
    print("Disks:", disks)
    print("Disk IO:", disk_IO)
    print("Disk Storage:", disk_storage)

