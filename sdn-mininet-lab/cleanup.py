#!/usr/bin/env python3
"""
cleanup.py — Mininet Environment Cleanup Utility
=================================================
Cleans up any leftover Mininet state (interfaces, bridges, processes)
from a previous run that exited uncleanly.

Run this if you see errors like:
    "Error creating interface pair ... File exists"
    "RTNETLINK answers: File exists"

Usage:
    sudo python3 cleanup.py

Author: Pavithra
Date:   April 2026
"""

import subprocess
import sys


def run(cmd, ignore_errors=False):
    """Run a shell command, optionally ignoring errors."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and not ignore_errors:
        print(f"  [warn] Command failed: {cmd}")
        print(f"         {result.stderr.strip()}")
    return result


def main():
    print("=" * 50)
    print("  Mininet Cleanup Utility")
    print("=" * 50)

    print("\n[1] Running mn --clean ...")
    run("mn --clean", ignore_errors=True)

    print("[2] Killing leftover processes ...")
    for proc in ["controller", "ofdatapath", "ofprotocol",
                 "ovs-openflowd", "nox_core", "ping", "mnexec"]:
        run(f"killall -q {proc}", ignore_errors=True)

    print("[3] Removing OVS bridges ...")
    result = run("ovs-vsctl list-br")
    bridges = result.stdout.strip().splitlines()
    for br in bridges:
        if br:
            run(f"ovs-vsctl --if-exists del-br {br}", ignore_errors=True)
            print(f"   Removed bridge: {br}")

    print("[4] Cleaning /tmp ...")
    run("rm -f /tmp/vconn* /tmp/vlogs* /tmp/*.out /tmp/*.log", ignore_errors=True)

    print("\n[OK] Cleanup complete. You can now run your topology safely.\n")


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)
    main()
