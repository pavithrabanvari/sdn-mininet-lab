#!/usr/bin/env python3
"""
run_experiment.py — Automated RTT vs Delay Experiment
======================================================
Runs the full experiment automatically across all three delay settings
(0 ms, 10 ms, 20 ms) and prints a consolidated results table.

Each test:
    1. Starts the linear topology with the given delay
    2. Waits for the POX controller to install flow rules
    3. Runs ping -c 5 between all host pairs
    4. Records average RTT
    5. Tears down and repeats for next delay setting

Prerequisites:
    - POX controller must be running before executing this script:
        cd ~/pox && python3 pox.py forwarding.l2_learning

Usage:
    sudo python3 run_experiment.py

Author: Pavithra
Date:   April 2026
"""

import time
from mininet.net import Mininet
from mininet.topo import LinearTopo
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.log import setLogLevel, info


DELAYS = [None, "10ms", "20ms"]   # None = baseline (0 ms)
PING_COUNT = 5


def parse_avg_rtt(ping_output):
    """
    Extract average RTT (ms) from ping command output.

    Args:
        ping_output (str): Raw output of the ping command.

    Returns:
        float: Average RTT in milliseconds, or -1.0 if parsing fails.
    """
    for line in ping_output.splitlines():
        if "rtt" in line and "avg" in line:
            # Format: rtt min/avg/max/mdev = X/Y/Z/W ms
            try:
                parts = line.split("=")[1].strip().split("/")
                return float(parts[1])
            except (IndexError, ValueError):
                pass
    return -1.0


def run_single_delay(delay_str):
    """
    Run one full test with the given delay setting.

    Args:
        delay_str (str | None): Delay string like '10ms', or None for baseline.

    Returns:
        dict: Mapping of (src, dst) -> avg_rtt_ms
    """
    label = delay_str if delay_str else "0ms (baseline)"
    info(f"\n{'='*55}\n")
    info(f"  Starting experiment: delay = {label}\n")
    info(f"{'='*55}\n")

    topo = LinearTopo(k=3)
    link_opts = dict(cls=TCLink, delay=delay_str) if delay_str else {}

    net = Mininet(
        topo=topo,
        controller=RemoteController('c0', ip='127.0.0.1', port=6633),
        **link_opts
    )
    net.start()
    time.sleep(3)   # Allow controller to connect and install initial rules

    results = {}
    hosts = net.hosts

    for i in range(len(hosts)):
        for j in range(i + 1, len(hosts)):
            src, dst = hosts[i], hosts[j]
            output = src.cmd(f"ping -c {PING_COUNT} {dst.IP()}")
            avg = parse_avg_rtt(output)
            key = f"{src.name} -> {dst.name}"
            results[key] = avg
            info(f"  {key}: avg RTT = {avg:.3f} ms\n")

    net.stop()
    time.sleep(2)   # Allow cleanup before next run
    return results


def print_results_table(all_results):
    """
    Print a formatted summary table of all results.

    Args:
        all_results (list[tuple]): List of (delay_label, results_dict).
    """
    labels = [d if d else "0ms" for d in DELAYS]
    pairs = list(all_results[0][1].keys())

    col_w = 18
    header = f"{'Host Pair':<16}" + "".join(f"{l:>{col_w}}" for l in labels)
    print("\n" + "=" * len(header))
    print("  RESULTS: Average RTT (ms) by Link Delay")
    print("=" * len(header))
    print(header)
    print("-" * len(header))
    for pair in pairs:
        row = f"{pair:<16}"
        for _, res in all_results:
            row += f"{res.get(pair, -1):>{col_w}.3f} ms"
        print(row)
    print("=" * len(header))


def main():
    setLogLevel("info")
    all_results = []

    for delay in DELAYS:
        res = run_single_delay(delay)
        all_results.append((delay, res))

    print_results_table(all_results)
    info("\n*** Experiment complete.\n")


if __name__ == "__main__":
    main()
