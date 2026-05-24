import psutil

class PsutilScannerBackend():
    def get_disk_usage(self) -> list[dict]:
        partitions = psutil.disk_partitions(all=True)
        results = []
        for part in partitions:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                if any(r["mounted_on"] == part.mountpoint for r in results):
                    # Found these ones on my machine:
                    # sdiskpart(device='/dev/nvme0n1p6', mountpoint='/nix/store', fstype='ext4', opts='rw,relatime'),
                    # sdiskpart(device='/dev/nvme0n1p6', mountpoint='/nix/store', fstype='ext4', opts='ro,nosuid,nodev,relatime')
                    continue  # Skip if we already have this mountpoint (e.g., multiple devices on same mount)
                results.append({
                    "filesystem": part.device,
                    "mounted_on": part.mountpoint,
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "available_bytes": usage.free,
                    # Optional: calculate percent if needed later
                    # "use_percent": usage.percent
                })
            except PermissionError:
                # Skip inaccessible partitions (e.g., CD-ROM, network mounts)
                continue
        return results
