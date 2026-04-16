# SDN Link Delay Analysis using Mininet

> **Measuring the impact of link delay on network latency in a Software-Defined Networking environment**

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Tools & Environment](#2-tools--environment)
3. [Network Topology](#3-network-topology)
4. [Repository Structure](#4-repository-structure)
5. [Setup & Installation](#5-setup--installation)
6. [Execution Steps](#6-execution-steps)
7. [Expected Output](#7-expected-output)
8. [Experimental Results](#8-experimental-results)
9. [Proof of Execution](#9-proof-of-execution)
10. [Observations & Analysis](#10-observations--analysis)
11. [Conclusion](#11-conclusion)
12. [References](#12-references)

---

## 1. Problem Statement

In Software-Defined Networking (SDN), the control plane is decoupled from the data plane. An OpenFlow controller manages all forwarding decisions, communicating with data-plane switches over a control channel.

**Research Question:**
> How does artificially introduced link delay affect end-to-end network latency (RTT) in an SDN-controlled Mininet topology?

This experiment:
- Creates a **linear 3-switch topology** in Mininet controlled by POX (an OpenFlow controller)
- Applies **configurable per-link delays** of 0 ms, 10 ms, and 20 ms using Linux `tc netem`
- Measures **Round-Trip Time (RTT)** between all host pairs using ICMP ping
- Verifies **SDN flow rule installation** using `ovs-ofctl dump-flows`
- Analyses the **proportional relationship** between link delay and observed latency

---

## 2. Tools & Environment

| Component | Version | Purpose |
|-----------|---------|---------|
| Ubuntu Linux | 20.04 LTS | Host OS (VirtualBox VM) |
| Mininet | 2.3.0 | Network emulator |
| Open vSwitch (OVS) | 2.13+ | Software OpenFlow switch |
| POX Controller | gar-experimenters | Remote SDN controller |
| tc netem | (kernel built-in) | Link delay emulation |
| `ping` / ICMP | (built-in) | RTT measurement |
| `ovs-ofctl` | (with OVS) | Flow table inspection |

---

## 3. Network Topology

### Linear Topology (primary experiment)

```
h1 ── s1 ── s2 ── s3 ── h3
            │
           h2
```

- **3 switches** (s1, s2, s3) connected in a chain
- **3 hosts** — h1 attached to s1, h2 attached to s2, h3 attached to s3
- **Remote POX controller** manages all switches via OpenFlow on port 6633
- **tc netem** applies uniform link delay to every link in the topology

### Single-Switch Topology (baseline reference)

```
    h1
    │
h2──s1
    │
    h3
```

- 1 switch (s1), 3 hosts in a star configuration
- Used to verify basic OVS forwarding without a remote controller

---

## 4. Repository Structure

```
sdn-mininet-lab/
│
├── topology.py          # Main script — linear topology, configurable delay
├── single_topo.py       # Single-switch star topology (baseline reference)
├── run_experiment.py    # Automated full experiment runner (all 3 delays)
├── cleanup.py           # Cleanup utility for stale Mininet state
├── requirements.txt     # Environment notes and installation commands
├── README.md            # This file
│
└── screenshots/
    ├── 01_linear_pingall_0ms.png       # pingall with 0ms delay
    ├── 02_h1_ping_h2_0ms.png           # h1→h2 RTT at 0ms
    ├── 03_h1_ping_h3_0ms.png           # h1→h3 RTT at 0ms
    ├── 04_h2_ping_h3_0ms.png           # h2→h3 RTT at 0ms
    ├── 05_linear_start_10ms.png        # Topology start with 10ms delay
    ├── 06_h1_ping_h2_10ms.png          # h1→h2 RTT at 10ms
    ├── 07_h1_ping_h3_10ms.png          # h1→h3 + h2→h3 RTT at 10ms
    ├── 08_linear_start_20ms.png        # Topology start with 20ms delay
    ├── 09_h1_ping_h2_h3_20ms.png       # h1→h2 + h1→h3 RTT at 20ms
    ├── 10_h2_ping_h3_20ms.png          # h2→h3 RTT at 20ms
    └── 11_single_topo_nodes.png        # Single topology nodes listing
```

---

## 5. Setup & Installation

### Step 1 — Install Mininet

```bash
sudo apt update
sudo apt install -y mininet
```

Verify:

```bash
mn --version
```

### Step 2 — Install Open vSwitch

```bash
sudo apt install -y openvswitch-switch
sudo service openvswitch-switch start
```

Verify:

```bash
ovs-vsctl --version
```

### Step 3 — Install POX Controller

```bash
cd ~
git clone https://github.com/noxrepo/pox
cd pox
```

Verify:

```bash
python3 pox.py --version
```

### Step 4 — Clone This Repository

```bash
git clone https://github.com/<your-username>/sdn-mininet-lab.git
cd sdn-mininet-lab
```

---

## 6. Execution Steps

### Option A — Manual Step-by-Step

#### Terminal 1 — Start POX Controller

```bash
cd ~/pox
python3 pox.py forwarding.l2_learning
```

Leave this terminal running. You should see:
```
POX 0.x ... / ...
Connected to switch ...
```

#### Terminal 2 — Run Topology

**Baseline (no delay):**

```bash
sudo python3 topology.py
```

**With 10 ms delay:**

```bash
sudo python3 topology.py --delay 10ms
```

**With 20 ms delay:**

```bash
sudo python3 topology.py --delay 20ms
```

#### Inside Mininet CLI

```bash
mininet> nodes                          # List all nodes
mininet> pingall                        # Test full mesh (expect 0% loss)
mininet> h1 ping -c 5 h2               # RTT: h1 to h2
mininet> h1 ping -c 5 h3               # RTT: h1 to h3
mininet> h2 ping -c 5 h3               # RTT: h2 to h3
```

**Inspect flow tables (in a third terminal while Mininet is running):**

```bash
sudo ovs-ofctl dump-flows s1
sudo ovs-ofctl dump-flows s2
sudo ovs-ofctl dump-flows s3
```

#### Exit Mininet

```bash
mininet> exit
```

---

### Option B — Automated Experiment Runner

With POX running in Terminal 1, run all three delay tests automatically:

```bash
sudo python3 run_experiment.py
```

This runs all three delay settings sequentially and prints a summary results table.

---

### Cleanup (if you see "File exists" errors)

```bash
sudo python3 cleanup.py
# or
sudo mn --clean
```

---

### Using Raw `mn` Commands (no Python scripts needed)

If you prefer not to use the Python scripts, the same results can be reproduced with:

```bash
# Baseline
sudo mn --topo linear,3 --controller remote

# 10ms delay
sudo mn --topo linear,3 --controller remote --link tc,delay='10ms'

# 20ms delay
sudo mn --topo linear,3 --controller remote --link tc,delay='20ms'
```

---

## 7. Expected Output

### pingall — Full Mesh Connectivity

```
*** Ping: testing ping reachability
h1 -> h2 h3
h2 -> h1 h3
h3 -> h1 h2
*** Results: 0% dropped (6/6 received)
```

### Ping Output Example (10ms delay, h1 → h2)

```
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=178 ms    ← first packet higher (flow install)
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=61.5 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=64 time=61.0 ms
64 bytes from 10.0.0.2: icmp_seq=4 ttl=64 time=71.4 ms
64 bytes from 10.0.0.2: icmp_seq=5 ttl=64 time=61.0 ms

--- 10.0.0.2 ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4009ms
rtt min/avg/max/mdev = 60.964/86.493/177.519/45.687 ms
```

### Flow Table Output (ovs-ofctl dump-flows s1)

```
NXST_FLOW reply (xid=0x4):
 cookie=0x0, duration=12.345s, table=0, n_packets=10, n_bytes=980,
 idle_age=2, priority=65535,icmp,in_port=1,... actions=output:2
 cookie=0x0, duration=12.000s, table=0, n_packets=10, n_bytes=980,
 idle_age=2, priority=65535,icmp,in_port=2,... actions=output:1
```

- `n_packets` counter increases with each ping — confirms SDN forwarding is active
- `actions=output:N` shows learned MAC-based forwarding installed by the POX L2 learning switch

---

## 8. Experimental Results

### RTT Summary Table

| Link Delay | h1 → h2 (avg RTT) | h1 → h3 (avg RTT) | h2 → h3 (avg RTT) |
|------------|-------------------|-------------------|-------------------|
| 0 ms       | 2.571 ms          | 4.224 ms          | 2.514 ms          |
| 10 ms      | 86.493 ms         | 110.020 ms        | 84.823 ms         |
| 20 ms      | 152.883 ms        | 198.403 ms        | 151.286 ms        |

### RTT vs Delay Graph

```
RTT (ms)
  200 |                                          ● h1→h3
      |                                   ●
  150 |                             ● h1→h2  ● h2→h3
      |
  100 |              ● h1→h3
      |        ●           ● h2→h3
   50 |  ● h1→h2
      |
    0 |__________________________________________
       0ms              10ms              20ms
                    Link Delay Applied
```

### Key Observations

- **RTT scales proportionally** with link delay — each 10ms increase in link delay adds ~60–80ms to RTT (accounts for multiple link traversals in round-trip)
- **h1 → h3 consistently highest RTT** — path traverses 5 links (h1-s1, s1-s2, s2-s3, s3-h3 × 2 for round-trip) vs 3 links for adjacent hosts
- **First ICMP packet always has higher latency** (icmp_seq=1) — caused by the SDN controller installing a new flow rule on first packet-in (packet goes to controller, rule installed, forwarded). Subsequent packets follow the pre-installed rule.
- **Zero packet loss in all tests** — tc netem introduces latency only, not drops

---

## 9. Proof of Execution

### Screenshot Index

| # | Screenshot | Description |
|---|-----------|-------------|
| 01 | `01_linear_pingall_0ms.png` | Linear topology start + pingall (0% loss, 0ms delay) |
| 02 | `02_h1_ping_h2_0ms.png` | h1→h2 ping output at 0ms delay (avg 2.571ms) |
| 03 | `03_h1_ping_h3_0ms.png` | h1→h3 ping output at 0ms delay (avg 4.224ms) |
| 04 | `04_h2_ping_h3_0ms.png` | h2→h3 ping output at 0ms delay (avg 2.514ms) |
| 05 | `05_linear_start_10ms.png` | Linear topology start with 10ms delay on all links |
| 06 | `06_h1_ping_h2_10ms.png` | h1→h2 ping at 10ms delay (avg 86.493ms) |
| 07 | `07_h1_ping_h3_10ms.png` | h1→h3 + h2→h3 ping at 10ms delay (avg 110.020ms / 84.823ms) |
| 08 | `08_linear_start_20ms.png` | Linear topology start with 20ms delay |
| 09 | `09_h1_ping_h2_h3_20ms.png` | h1→h2 + h1→h3 ping at 20ms delay (avg 152.883ms / 198.403ms) |
| 10 | `10_h2_ping_h3_20ms.png` | h2→h3 ping at 20ms delay (avg 151.286ms) |
| 11 | `11_single_topo_nodes.png` | Single switch topology — nodes listing |

> All screenshots are located in the [`screenshots/`](./screenshots/) folder of this repository.

---

## 10. Observations & Analysis

### Why does icmp_seq=1 always show higher RTT?

When a new flow starts in an SDN network, the first packet has no matching rule in the switch's flow table. The switch sends a `Packet-In` message to the POX controller. The controller runs its L2 learning logic, installs a new flow rule (`Flow-Mod`), and the packet is forwarded. This controller round-trip adds latency only to the **first packet**. All subsequent packets match the installed rule and are forwarded locally at wire speed.

### Why is h1→h3 RTT always higher than h1→h2?

```
h1 → h2:  h1─s1─s2─h2        = 3 link hops × delay × 2 (round trip) = 6 × delay
h1 → h3:  h1─s1─s2─s3─h3     = 4 link hops × delay × 2 (round trip) = 8 × delay
```

At 20ms delay: h1→h2 theoretical = 6×20 = 120ms (observed: 152ms with overhead)
At 20ms delay: h1→h3 theoretical = 8×20 = 160ms (observed: 198ms with overhead)

### Does tc netem cause packet loss?

No. tc netem in delay-only mode adds latency without dropping packets. All experiments show 0% packet loss. This confirms that increased RTT is purely due to the emulated delay, not network congestion or buffer overflow.

---

## 11. Conclusion

This experiment demonstrates that:

1. **Mininet accurately emulates configurable link delays** — observed RTTs closely match theoretical values based on hop count × delay × 2.
2. **POX SDN controller correctly installs OpenFlow flow rules** — verified via `ovs-ofctl dump-flows`, with packet counters incrementing as expected.
3. **RTT scales linearly with applied link delay** — enabling precise, repeatable latency emulation for SDN research.
4. **SDN architecture provides complete traffic visibility** — every forwarding decision can be inspected and verified, which is not possible in traditional networks.

Mininet proves to be an effective, low-cost platform for SDN research, prototyping, and teaching — allowing full network emulation without physical hardware.

---

## 12. References

- [Mininet Project](http://mininet.org/) — Network emulator documentation
- [OpenFlow Specification](https://opennetworking.org/) — ONF OpenFlow standards
- [POX Controller](https://noxrepo.github.io/pox-doc/) — POX SDN controller documentation
- [Open vSwitch](https://www.openvswitch.org/) — OVS reference manual
- [tc-netem(8)](https://man7.org/linux/man-pages/man8/tc-netem.8.html) — Linux traffic control: network emulator
- Lantz, B., Heller, B., McKeown, N. (2010). *A network in a laptop: rapid prototyping for software-defined networks.* ACM HotNets-IX.

---

*Submitted as part of SDN Lab Assignment — April 2026*
