#!/usr/bin/env python3
"""
run_experiment.py — Network Delay Measurement Tool
===================================================
Runs a complete experiment across three delay settings (0ms, 10ms, 20ms):
    1. Ping RTT measurement between all host pairs
    2. iperf3 TCP throughput measurement
    3. iperf3 UDP latency + packet loss measurement

Prints a consolidated results table at the end.

Prerequisites:
    - iperf3 must be installed:
        sudo apt install iperf3
    - POX controller must be running before executing this script:
        cd ~/pox && python3 pox.py forwarding.l2_learning

Usage:
    sudo python3 run_experiment.py

Author: Pavithra
Date:   April 2026
"""

import time
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.log import setLogLevel, info

# ── Configuration ─────────────────────────────────────────────────────────────
DELAYS     = [None, "10ms", "20ms"]   # None = 0ms baseline
PING_COUNT = 5                         # Pings per host pair
IPERF_TIME = 5                         # Seconds to run each iperf test
# ──────────────────────────────────────────────────────────────────────────────


class LinearTopoWithDelay(Topo):
    """3-host, 3-switch linear topology with optional per-link TC delay."""

    def build(self, k=3, delay=None):
        link_opts = {'delay': delay} if delay else {}
        hosts    = [self.addHost(f'h{i+1}') for i in range(k)]
        switches = [self.addSwitch(f's{i+1}') for i in range(k)]
        for i in range(k):
            self.addLink(hosts[i], switches[i], **link_opts)
        for i in range(k - 1):
            self.addLink(switches[i], switches[i + 1], **link_opts)


# ── Parsing helpers ───────────────────────────────────────────────────────────

def parse_avg_rtt(ping_output):
    """Extract average RTT (ms) from ping output. Returns -1.0 on failure."""
    for line in ping_output.splitlines():
        if "rtt" in line and "avg" in line:
            try:
                return float(line.split("=")[1].strip().split("/")[1])
            except (IndexError, ValueError):
                pass
    return -1.0


def parse_tcp_bandwidth(iperf_output):
    """
    Extract TCP bandwidth (Mbits/sec) from iperf3 output.
    Looks for the sender summary line.
    Returns -1.0 on failure.
    """
    for line in iperf_output.splitlines():
        if "sender" in line:
            parts = line.split()
            for i, p in enumerate(parts):
                if "Mbits" in p or "Gbits" in p or "Kbits" in p:
                    try:
                        val = float(parts[i - 1])
                        if "Gbits" in p:
                            val *= 1000
                        elif "Kbits" in p:
                            val /= 1000
                        return val
                    except (ValueError, IndexError):
                        pass
    return -1.0


def parse_udp_results(iperf_output):
    """
    Extract UDP jitter (ms) and packet loss (%) from iperf3 output.
    Returns (jitter_ms, loss_percent) or (-1.0, -1.0) on failure.
    """
    for line in iperf_output.splitlines():
        if "receiver" in line or ("ms" in line and "%" in line):
            parts = line.split()
            jitter, loss = -1.0, -1.0
            for i, p in enumerate(parts):
                if p == "ms" and i > 0:
                    try:
                        jitter = float(parts[i - 1])
                    except ValueError:
                        pass
                if "%" in p:
                    try:
                        loss = float(p.replace("(", "").replace("%)", "")
                                      .replace("%", ""))
                    except ValueError:
                        pass
            if jitter != -1.0 or loss != -1.0:
                return jitter, loss
    return -1.0, -1.0


# ── Experiment runner ─────────────────────────────────────────────────────────

def run_single_delay(delay_str):
    """
    Run one full test (ping + iperf TCP + iperf UDP) for a given delay.

    Args:
        delay_str (str | None): e.g. '10ms' or None for baseline.

    Returns:
        dict: {
            'ping': { 'h1 -> h2': avg_rtt, ... },
            'tcp':  { 'h1 -> h2': bandwidth_mbps, ... },
            'udp':  { 'h1 -> h2': (jitter_ms, loss_pct), ... }
        }
    """
    label = delay_str if delay_str else "0ms (baseline)"
    info(f"\n{'=' * 60}\n")
    info(f"  Starting experiment: delay = {label}\n")
    info(f"{'=' * 60}\n")

    topo = LinearTopoWithDelay(k=3, delay=delay_str)
    net  = Mininet(
        topo=topo,
        controller=RemoteController('c0', ip='127.0.0.1', port=6633),
        link=TCLink
    )
    net.start()
    time.sleep(3)  # Wait for controller to install flow rules

    hosts = net.hosts
    ping_results = {}
    tcp_results  = {}
    udp_results  = {}

    for i in range(len(hosts)):
        for j in range(i + 1, len(hosts)):
            src, dst = hosts[i], hosts[j]
            key = f"{src.name} -> {dst.name}"

            # ── 1. Ping RTT ───────────────────────────────────────────────────
            info(f"\n  [PING] {key}\n")
            ping_out = src.cmd(f"ping -c {PING_COUNT} {dst.IP()}")
            avg_rtt  = parse_avg_rtt(ping_out)
            ping_results[key] = avg_rtt
            info(f"    avg RTT = {avg_rtt:.3f} ms\n")

            # ── 2. iperf3 TCP throughput ──────────────────────────────────────
            info(f"  [iperf3 TCP] {key}\n")
            dst.cmd("pkill -f iperf3")           # Kill any old server
            dst.cmd("iperf3 -s -D")              # Start server as daemon
            time.sleep(0.5)
            tcp_out = src.cmd(
                f"iperf3 -c {dst.IP()} -t {IPERF_TIME} 2>&1"
            )
            bw = parse_tcp_bandwidth(tcp_out)
            tcp_results[key] = bw
            info(f"    bandwidth = {bw:.2f} Mbits/sec\n")
            dst.cmd("pkill -f iperf3")           # Stop server

            # ── 3. iperf3 UDP latency + packet loss ───────────────────────────
            info(f"  [iperf3 UDP] {key}\n")
            dst.cmd("pkill -f iperf3")
            dst.cmd("iperf3 -s -D")
            time.sleep(0.5)
            udp_out = src.cmd(
                f"iperf3 -c {dst.IP()} -u -b 10M -t {IPERF_TIME} 2>&1"
            )
            jitter, loss = parse_udp_results(udp_out)
            udp_results[key] = (jitter, loss)
            info(f"    jitter = {jitter:.3f} ms  |  loss = {loss:.1f}%\n")
            dst.cmd("pkill -f iperf3")

    net.stop()
    time.sleep(2)  # Allow cleanup before next run

    return {
        'ping': ping_results,
        'tcp':  tcp_results,
        'udp':  udp_results
    }


# ── Results printing ──────────────────────────────────────────────────────────

def print_results_table(all_results):
    """
    Print three formatted tables:
        Table 1 — Ping avg RTT
        Table 2 — iperf3 TCP Bandwidth
        Table 3 — iperf3 UDP Jitter + Packet Loss

    Args:
        all_results (list[tuple]): [(delay_str, results_dict), ...]
    """
    labels = [d if d else "0ms" for d in DELAYS]
    pairs  = list(all_results[0][1]['ping'].keys())
    col_w  = 20

    def print_table(title, data_fn):
        header = f"{'Host Pair':<16}" + "".join(f"{l:>{col_w}}" for l in labels)
        print("\n" + "=" * len(header))
        print(f"  {title}")
        print("=" * len(header))
        print(header)
        print("-" * len(header))
        for pair in pairs:
            row = f"{pair:<16}"
            for _, res in all_results:
                row += data_fn(res, pair)
            print(row)
        print("=" * len(header))

    # Table 1 — Ping RTT
    print_table(
        "TABLE 1 — Ping Average RTT (ms)",
        lambda res, p: f"{res['ping'].get(p, -1):>{col_w}.3f} ms"
    )

    # Table 2 — TCP Bandwidth
    print_table(
        "TABLE 2 — iperf3 TCP Bandwidth (Mbits/sec)",
        lambda res, p: f"{res['tcp'].get(p, -1):>{col_w}.2f} Mbps"
    )

    # Table 3 — UDP Jitter + Loss
    print("\n" + "=" * 80)
    print("  TABLE 3 — iperf3 UDP Jitter (ms) + Packet Loss (%)")
    print("=" * 80)
    print(f"{'Host Pair':<16}" +
          "".join(f"{'Jitter':>{col_w}}{'Loss':>{10}}" for _ in labels))
    sub = f"{'':16}" + "".join(f"{l:>{col_w}}{'':>10}" for l in labels)
    print(sub)
    print("-" * 80)
    for pair in pairs:
        row = f"{pair:<16}"
        for _, res in all_results:
            j, l = res['udp'].get(pair, (-1.0, -1.0))
            row += f"{j:>{col_w}.3f} ms{l:>{8}.1f} %"
        print(row)
    print("=" * 80)


# ── Main ──────────────────────────────────────────────────────────────────────

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
