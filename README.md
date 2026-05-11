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

## Vulnerability Scanner Module

The `vulnerabilities/` subdirectory implements a NixOS vulnerability scanner with:

### Backend
- **ScanPipeline**: Orchestrates derivation resolution, vulnix scanning, dependency mapping, tree merging, normalization with severity propagation up the tree (parent nodes inherit highest child severity)
- **Database**: SQLite with `scans`, `vulnerability_events`, `dependency_tree` tables
- **Timeseries queries**: Package-level and global vulnerability timelines

### Frontend (Phase 3)
- **HTMX-powered SPA**: Sidebar scan list, collapsible dependency tree, timeline bar chart
- **Severity coloring**: CRITICAL (red) → HIGH (orange) → MEDIUM (yellow) → LOW (green)
- **API endpoints**:
  - `GET /api/scans` — Scan list for sidebar
  - `GET /api/tree/<scan_id>` — HTML dependency tree with severity-propagated nodes (parent shows max child severity)
  - `GET /api/vuln-map/<scan_id>` — JSON vulnerability map
  - `GET /timeseries` — Timeline data
  - `GET /aggregation/<scan_id>/<package>` — Severity aggregation
  - `GET /scan/<scan_id>` — Full scan detail page

### Test Coverage
- 131 tests across 15 test modules
- 100% pass rate on all checks (mypy, unittest, nix-build)

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
# Environment variables
export BIND_ADDRESS=0.0.0.0:8000  # Host and port for the Bottle server

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