# P4 Link-Latency based AQM/Congestion Control

### Setup
1. Install the following required tools:
    * [Mininet](https://github.com/mininet/mininet) - including **make install**
    * [P4 compiler bm](https://github.com/p4lang/p4c-bm)
    * [P4 behavioral model](https://github.com/p4lang/behavioral-model)

2. and in advance the following packages:
    ```
    sudo apt-get install openvswitch-testcontroller python-tk iperf3 xterm
    python -mpip install matplotlib
    pip install scapy
    ```
    
3. Clone the repository such that the 'behavioral-model' install is accessable from the p4-codel folder using `../../behavioral-model`


### Directory overview
.\
├── eval\_scripts\
│   ├── eval.py\
│   └── plotting.py\
├── out\
├── srcP4\
│   ├── simple\_router.p4\
│   ├── commandsRouterSimple\_r0.txt\
│   ├── commandsRouterSimple\_r1.txt\
│   ├── commandsRouterSimple\_r2.txt\
│   └── header.p4\
├── srcPython\
│   ├── toposetup.py\
│   └── ping.py\
└── testOPs\

#### eval\_scripts
* eval.py - Primary evaluation script. Parses the pcap and iperf-JSON outputs. PCAP parsing is done by the `evaluate()` and `parse_pcap_trace()` functions. `parse_pcap_trace()` tells the script which PCAPs to evaluate (hard-cded). The iperf JSON output is parsed by the `evaluate_iperf()` function which makes calls to plotting.py

* plotting.py - Evaluates the iperf JSON output to calculate throughput and RTT. Also used for GUI (currently unused and not updated)

#### out
* Contains the output iperf3 JSON(s) and the PCAP files from each interface.

#### srcP4
* simple\_router.p4 - Contains the link-latency scheme implementation. The file contains flags `MONITOR_ENABLED` which enables the Link-Latency based scheme, `CODEL_IMPLEMENTED` which enables the original CoDel implementation, `MAX_PACKET_LATENCY_1` which denotes the latency limit for flow 1, `MAX_PACKET_LATENCY_2` which denotes the latency limit for flow 2, and `ENABLE_DEBUG_TABLES` which enables logs/debug. Note: The original CoDel implementation was done in the router.p4 which we do not use here. We should probably change the names of these files at some point.

* header.p4 - Contains the header definitions used in our implementation. This includes header `monitor_t` and struct `fwd_t`.

* commandsRouterSimple\_x.txt - The 3 files contain the commands for the corresponding p4 switches in our test setup. 

#### srcPython
* toposetup.py - python script to setup the mininet topology for testing. Sets up 4 hosts (h1, h2, h3, h4) and 3 p4 switches (r0, r1, r2). r1, r2, and r3 are connected in a line topology (r1 <---> r0 <---> r2) with hosts h1 and h2 connected to r1 and hosts h3 and h4 to r2. Once the setup is done, the script then runs the iperf test on the same and then enters CLI mode. 

* ping.py - Contains the iperf test implementation. The `IperfTest()` function creates, starts, and joins the threads the run the iperf test flows. The `startIperfTest()` function runs the iperf3 client and server within a thread with the provided flags (bw, interval, time, etc.).

## Run
* Run Mininet with the P4(bmv2) Link Latency scheme implementation (Alternatively, modify and run the testing\_script.sh shell script to do all this for you)
```
./simple_run.sh [--nocli --iperft x --bw y]
```
Normally this script generates PCAP files for evaluation and enters the Mininet CLI mode for debugging.
With the optional command line parameter (--nocli), this behavior can be changed.


## Evaluate
To evaluate the measured results run:
```
./evaluate.sh
```
Note: The --gui parameter is not configured for the link-latency implementation and should be avoided.

## Test Script
The test script requires a folder name (or prefix) as input and then runs 20 iterations of the simple\_run and eval scripts for the set array of bandwidths. It creates separate directories for each combination within the testOPs directory and places the 20 iterations of each combination into the correspondingly named directory.
```
./testing_script.sh directory_prefix
```
