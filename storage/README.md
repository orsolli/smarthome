# Storage
This is a storage monitor that tracks the disk usage over time and provides a visualization to show the trend.

## Getting Started
### Installation
To install this package using nix, run `nix-build storage.nix` and run the scanner `DATABASE_PATH=./storage.sqlite result/bin/storage-scanner`

After a scan, you can start the web-server to serve a visual dashboard `DATABASE_PATH=./storage.sqlite BIND_ADDRESS=0.0.0.0 result/bin/storage-web`

## Development
[storage/docs/TODO.md](docs/TODO.md) — List of things that need to be done.

[storage/docs/DESIGN.md](docs/DESIGN.md) — Detailed documentation on how to do things.
