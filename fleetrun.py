#!/usr/bin/env python3
"""Run one RouterOS command across every router in an inventory file.

Usage:
    python fleetrun.py inventory.json "/system resource print"
"""
import argparse
import json
import socket
import sys

import paramiko

DEFAULT_TIMEOUT = 10


def load_inventory(path: str) -> list:
    with open(path) as f:
        data = json.load(f)
    return data["routers"]


def run_on_router(router: dict, command: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    name = router.get("name", router["host"])
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            router["host"],
            port=router.get("port", 22),
            username=router["username"],
            password=router["password"],
            timeout=timeout,
        )
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        output = stdout.read().decode(errors="replace").strip()
        error = stderr.read().decode(errors="replace").strip()
        exit_status = stdout.channel.recv_exit_status()

        if exit_status != 0 and error:
            return {"name": name, "host": router["host"], "ok": False, "output": error}
        return {"name": name, "host": router["host"], "ok": True, "output": output}

    except (paramiko.ssh_exception.SSHException, socket.timeout, socket.error, OSError) as e:
        return {"name": name, "host": router["host"], "ok": False, "output": str(e)}

    finally:
        client.close()


def run_fleet(routers: list, command: str, timeout: int = DEFAULT_TIMEOUT) -> list:
    return [run_on_router(r, command, timeout) for r in routers]


def print_results(results: list) -> None:
    for result in results:
        status = "OK" if result["ok"] else "FAIL"
        print(f"\n=== {result['name']} ({result['host']}) [{status}] ===")
        print(result["output"] if result["output"] else "(no output)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory_file", help="Path to an inventory.json file")
    parser.add_argument("command", help="RouterOS command to run on every router")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                         help="Per-router SSH/command timeout in seconds")
    args = parser.parse_args()

    routers = load_inventory(args.inventory_file)
    results = run_fleet(routers, args.command, args.timeout)
    results.sort(key=lambda r: r["name"])
    print_results(results)

    fails = sum(1 for r in results if not r["ok"])
    print(f"\n{len(results) - fails}/{len(results)} succeeded.")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
