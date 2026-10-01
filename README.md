# mikrotik-fleet-run

Run one RouterOS command across every router in an inventory file over SSH, and see the results
side by side instead of logging into each router one at a time. Useful for quick fleet-wide checks:
RouterOS version, uptime, whether a specific firewall rule made it everywhere, etc.

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

=== core (192.168.88.2) [OK] ===
uptime: 40w1d2h10m
version: 7.14.2 (stable)
...

2/2 succeeded.
```

Run against many routers at once instead of one at a time:

```sh
python fleetrun.py inventory.json "/system resource print" --parallel 8
```

Exits `1` if any router failed to connect or the command errored, `0` if every router succeeded —
safe to use in a script.

## Running the tests

```sh
python -m unittest discover -s tests
```

Tests mock the SSH layer, so they run without any real routers.

## License

MIT — see [LICENSE](LICENSE).

## About

Maintained by [Onasis Tech](https://onasis.tech), a Kenyan team building software for ISPs and network operators. If you manage MikroTik routers behind CGNAT or Starlink, [Onasis Tech Connect](https://connect.onasis.tech) gives each one a permanent remote access address, no public IP needed.
