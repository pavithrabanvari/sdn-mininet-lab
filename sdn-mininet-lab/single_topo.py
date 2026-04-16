#!/usr/bin/env python3
"""
single_topo.py — Single Switch Topology (3 Hosts)
==================================================
Creates a simple star topology with one OVS switch and 3 hosts.
No remote controller required — falls back to OVS normal forwarding.

Topology layout:
        h1
        |
    h2--s1
        |
        h3

Usage:
    sudo python3 single_topo.py

Author: Pavithra
Date:   April 2026
"""

from mininet.net import Mininet
from mininet.topo import SingleSwitchTopo
from mininet.cli import CLI
from mininet.log import setLogLevel, info


def main():
    setLogLevel("info")

    topo = SingleSwitchTopo(k=3)   # 1 switch, 3 hosts
    net = Mininet(topo=topo)

    net.start()

    info("\n*** Available nodes\n")
    for node in net.hosts + net.switches:
        info(f"  {node.name}\n")

    info("\n*** Testing connectivity\n")
    net.pingAll()

    info("\n*** Network ready. Type 'exit' to quit.\n")
    CLI(net)
    net.stop()


if __name__ == "__main__":
    main()
