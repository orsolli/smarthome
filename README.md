# smarthome

Declarative smart home monitoring infrastructure built on NixOS.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        smarthome System                         │
├─────────────────────────────────────────────────────────────────┤
│  Collector             | Database table |  Visualizer           │
├─────────────────────────────────────────────────────────────────┤
│  [read_waveplus] ────► [                ]                       │
│  [read_han] ─────────► [                ]                       │
│  ...                   [                ]                    ...│
│                        [                ] ───► [timeseries_plot]│
└─────────────────────────────────────────────────────────────────┘
```

- **Collectors**: Individual `app.py` modules implementing sensor reading
- **Storage**: SQLite time-series with automatic schema creation
- **Visualization**: Flask/Plotly dashboard with interactive charts

## Principles

| Principle          | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **NixOS Integration** | All components are Nix-managed modules with reproducible builds          |
| **Data Model**      | Timestamped time-series; one table per sensor type; auto-schema            |
| **Security**        | Dedicated service account; local socket only; least-privilege principle    |
| **Immutability**    | Services defined in Nix flakes; config changes require rebuild             |

## Maintenance

| Frequency    | Action                                                         |
|--------------|----------------------------------------------------------------|
| **Daily**    | Verify services active; review logs; check disk space          |
| **Weekly**   | Database integrity check; vacuum; backup to external location  |
| **Monthly**  | Review retention policy; archive old data; security audit      |

## Expansion Pattern

### Adding a New Collector
1. Create module directory (e.g., `new_sensor/`)
2. Implement `app.py` with data collection logic
3. Write `default.nix` for Nix package management
4. Add module to imports in parent `default.nix`
5. Configure service options and systemd tmpfiles

### Adding Visualization
1. Add new sensor to plotting logic
2. Update chart configuration as needed

## Troubleshooting

| Issue              | Diagnostic Command                                      |
|--------------------|---------------------------------------------------------|
| Service not active | `systemctl status <service-name>`                        |
| Serial device      | `dmesg \| grep ttyUSB`                                   |
| Database locked    | `lsof /var/lib/smarthome/*.db`                           |

## Quick Reference

```bash
# Enable service
sudo nixos-rebuild switch

# Check status
systemctl status smarthome-<component-name>

# Access dashboard
open http://localhost:8000

# Backup databases
tar -czf backup_$(date +%Y%m%d).tar.gz /var/lib/smarthome/*.db
```

---

*See individual component directories for implementation details.*