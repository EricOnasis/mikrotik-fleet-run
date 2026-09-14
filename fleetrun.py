#!/usr/bin/env python3
"""Run one RouterOS command across every router in an inventory file.

Usage:
    python fleetrun.py inventory.json "/system resource print"
    python fleetrun.py inventory.json "/system resource print" --parallel 8
"""
import argparse
import json
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

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


def run_fleet(routers: list, command: str, max_parallel: int = 1,
              timeout: int = DEFAULT_TIMEOUT) -> list:
    if max_parallel <= 1:
        return [run_on_router(r, command, timeout) for r in routers]

    results = []
    with ThreadPoolExecutor(max_workers=max_parallel) as executor:
        futures = {executor.submit(run_on_router, r, command, timeout): r for r in routers}
        for future in as_completed(futures):
            results.append(future.result())
    return results


def print_results(results: list) -> None:
    for result in results:
        status = "OK" if result["ok"] else "FAIL"
        print(f"\n=== {result['name']} ({result['host']}) [{status}] ===")
        print(result["output"] if result["output"] else "(no output)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory_file", help="Path to an inventory.json file")
    parser.add_argument("command", help="RouterOS command to run on every router")
    parser.add_argument("--parallel", type=int, default=1,
                         help="Number of routers to run against concurrently (default: 1)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                         help="Per-router SSH/command timeout in seconds")
    args = parser.parse_args()

    routers = load_inventory(args.inventory_file)
    results = run_fleet(routers, args.command, args.parallel, args.timeout)
    results.sort(key=lambda r: r["name"])
    print_results(results)

    fails = sum(1 for r in results if not r["ok"])
    print(f"\n{len(results) - fails}/{len(results)} succeeded.")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
