import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fleetrun import run_fleet, run_on_router


def make_fake_client(output=b"", error=b"", exit_status=0, raise_on_connect=None):
    client = MagicMock()
    if raise_on_connect:
        client.connect.side_effect = raise_on_connect

    stdout = MagicMock()
    stdout.read.return_value = output
    stdout.channel.recv_exit_status.return_value = exit_status

    stderr = MagicMock()
    stderr.read.return_value = error

    client.exec_command.return_value = (MagicMock(), stdout, stderr)
    return client


class RunOnRouterTests(unittest.TestCase):
    ROUTER = {"name": "r1", "host": "10.0.0.1", "username": "admin", "password": "x"}

    @patch("fleetrun.paramiko.SSHClient")
    def test_successful_command(self, mock_ssh):
        mock_ssh.return_value = make_fake_client(output=b"RouterOS 7.15", exit_status=0)
        result = run_on_router(self.ROUTER, "/system resource print")
        self.assertTrue(result["ok"])
        self.assertEqual(result["output"], "RouterOS 7.15")

    @patch("fleetrun.paramiko.SSHClient")
    def test_nonzero_exit_with_stderr_is_a_failure(self, mock_ssh):
        mock_ssh.return_value = make_fake_client(error=b"no such command", exit_status=1)
        result = run_on_router(self.ROUTER, "/bogus command")
        self.assertFalse(result["ok"])
        self.assertEqual(result["output"], "no such command")

    @patch("fleetrun.paramiko.SSHClient")
    def test_connection_failure_is_reported_not_raised(self, mock_ssh):
        mock_ssh.return_value = make_fake_client(raise_on_connect=OSError("unreachable"))
        result = run_on_router(self.ROUTER, "/system resource print")
        self.assertFalse(result["ok"])
        self.assertIn("unreachable", result["output"])


class RunFleetTests(unittest.TestCase):
    ROUTERS = [
        {"name": "r1", "host": "10.0.0.1", "username": "admin", "password": "x"},
        {"name": "r2", "host": "10.0.0.2", "username": "admin", "password": "x"},
    ]

    @patch("fleetrun.paramiko.SSHClient")
    def test_sequential_runs_all_routers(self, mock_ssh):
        mock_ssh.return_value = make_fake_client(output=b"ok")
        results = run_fleet(self.ROUTERS, "/system resource print", max_parallel=1)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r["ok"] for r in results))

    @patch("fleetrun.paramiko.SSHClient")
    def test_parallel_runs_all_routers(self, mock_ssh):
        mock_ssh.return_value = make_fake_client(output=b"ok")
        results = run_fleet(self.ROUTERS, "/system resource print", max_parallel=4)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r["ok"] for r in results))


if __name__ == "__main__":
    unittest.main()
