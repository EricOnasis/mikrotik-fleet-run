# mikrotik-fleet-run

Run one RouterOS command across every router in an inventory file over SSH, and see the results
side by side instead of logging into each router one at a time.

## Installation

```sh
pip install -r requirements.txt
```

## Usage

```sh
cp inventory.example.json inventory.json   # fill in your routers
python fleetrun.py inventory.json "/system resource print"
```

```
=== branch-office (192.168.88.1) [OK] ===
uptime: 12w3d4h32m
version: 7.15 (stable)
...

2/2 succeeded.
```

Exits `1` if any router failed to connect or the command errored, `0` if every router succeeded.

Parallel execution across many routers at once coming soon.

## License

MIT — see [LICENSE](LICENSE).
