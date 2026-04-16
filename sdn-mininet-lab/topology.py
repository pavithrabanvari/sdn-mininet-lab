#!/usr/bin/env python3
"""
topology.py — SDN Linear Topology with Configurable Link Delay
==============================================================
Creates a Mininet linear topology with 3 switches and 3 hosts,
connected to a remote POX OpenFlow controller.

Topology layout:
    h1 --- s1 --- s2 --- s3 --- h3
                   |
                  h2

Usage:
    sudo python3 topology.py                  # 0 ms delay (baseline)
    sudo python3 topology.py --delay 10ms     # 10 ms link delay
    sudo python3 topology.py --delay 20ms     # 20 ms link delay

Author: Pavithra
Date:   April 2026
"""

import argparse
from mininet.net import Mininet
from mininet.topo import LinearTopo
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info


def build_network(delay=None):
    """
    Build and start a linear Mininet topology with 3 switches.

    Args:
        delay (str | None): Link delay string e.g. '10ms', '20ms'.
                            Pass None for baseline (no delay).

    Returns:
        Mininet: Running network object.
    """
    topo = LinearTopo(k=3)  # 3 switches, each with 1 host

    # Select link type based on whether delay is requested
    if delay:
        link_opts = dict(cls=TCLink, delay=delay)
        info(f"*** Link delay set to {delay} on all links\n")
    else:
        link_opts = {}
        info("*** No link delay (baseline)\n")

    net = Mininet(
        topo=topo,
        controller=RemoteController(
            name='c0',
            ip='127.0.0.1',
            port=6633          # POX default OpenFlow port
        ),
        **link_opts
    )

    return net


def run_ping_tests(net):
    """
    Run connectivity and latency tests between all host pairs.

    Tests performed:
        1. pingall  — verifies full mesh reachability
        2. ping -c 5 between each host pair — measures avg RTT
    """
    info("\n*** Testing full mesh connectivity (pingall)\n")
    net.pingAll()

    hosts = net.hosts
    info("\n*** Running ping -c 5 between all host pairs\n")
    for i in range(len(hosts)):
        for j in range(i + 1, len(hosts)):
            src = hosts[i]
            dst = hosts[j]
            info(f"  {src.name} -> {dst.name}\n")
            result = src.cmd(f"ping -c 5 {dst.IP()}")
            # Print just the summary line
            for line in result.splitlines():
                if "rtt" in line or "packet" in line:
                    info(f"    {line}\n")


def dump_flow_tables(net):
    """
    Print OpenFlow flow tables for all switches using ovs-ofctl.
    Useful for verifying that the SDN controller installed rules correctly.
    """
    info("\n*** Dumping OpenFlow flow tables\n")
    for switch in net.switches:
        info(f"\n  [Switch: {switch.name}]\n")
        result = switch.cmd(f"ovs-ofctl dump-flows {switch.name}")
        for line in result.splitlines():
            info(f"    {line}\n")


def main():
    parser = argparse.ArgumentParser(
        description="SDN Mininet topology with configurable link delay"
    )
    parser.add_argument(
        "--delay",
        type=str,
        default=None,
        help="Link delay to apply to all links, e.g. '10ms' or '20ms'"
    )
    parser.add_argument(
        "--auto-test",
        action="store_true",
        help="Run ping tests and dump flow tables automatically, then exit"
    )
    args = parser.parse_args()

    setLogLevel("info")

    info("*** Building network\n")
    net = build_network(delay=args.delay)

    info("*** Starting network\n")
    net.start()

    if args.auto_test:
        dump_flow_tables(net)
        run_ping_tests(net)
        info("\n*** Auto-test complete. Stopping network.\n")
        net.stop()
    else:
        info("\n*** Network ready. Type 'exit' or Ctrl-D to quit.\n")
        CLI(net)
        net.stop()


if __name__ == "__main__":
    main()
