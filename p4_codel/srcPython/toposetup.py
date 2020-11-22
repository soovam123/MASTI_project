#!/usr/bin/python

# Copyright 2018-present Ralf Kundel, Jeremias Blendin, Nikolas Eller
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mininet.node import Node
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink

from p4_mininet import P4Switch, P4Host
from ping import *
from linuxrouter import LinuxRouter

import sys
#from eval_scripts.eval import *
sys.path.insert(1, '/home/abhi/Documents/MASTI_project/p4-codel/eval_scripts/')
#import eval

import argparse
from time import sleep
import os
import subprocess

_THIS_DIR = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(description='Mininet demo')
parser.add_argument('--json', help='Path to JSON config file',
                    type=str, action="store", required=True)
parser.add_argument('--swpath', help='Path to the switch which should be used in this exercise',
                    type=str, action="store")
parser.set_defaults(swpath="simple_switch")
parser.add_argument('--cli', help='Path to BM CLI',
                    type=str, action="store", required=True)
parser.add_argument('--cliCmd', help='Path to cli instructions',
                    type=str, action="store", required=True)
parser.add_argument("-p4", "--useP4", action="count",
                    help="use the p4 switch")
parser.add_argument('--nopcap', help='Deactivates the switch PCAP logging',
                    type=bool, action="store")
parser.set_defaults(nopcap=False)
parser.add_argument('--nocli', help='Deactivates the mininet CLI',
                    type=bool, action="store")
parser.set_defaults(nocli=False)
parser.add_argument('--h3delay', help='The delay between h3 and s2. Example: "30ms"',
                    type=str, action="store")
parser.set_defaults(h3delay="2ms")
parser.add_argument('--iperft', help='The transmit time of iperf3 in seconds. Example: 30',
                    type=int, action="store")
parser.set_defaults(iperft=10)
parser.add_argument('--bw', help='Set iperf test bandwidth',
                    type=str, action="store")
parser.set_defaults(bw="5m")

args = parser.parse_args()


class MyTopo(Topo):
    def __init__(self, json_path, p4=True, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)
        #s1 = self.addSwitch('s1')

        aqm_switch = None
        if p4:
            aqm_switch = self.addSwitch('r0',
                                    cls=P4Switch,
                                    sw_path = args.swpath,
                                    json_path = json_path,
                                    thrift_port = 22222,
                                    pcap_dump = not args.nopcap,
                                    #pcap_dir = "out",
                                    log_console = True, #TODO
                                    enable_debugger = False)
            s1 = self.addSwitch('r1',
                                    cls=P4Switch,
                                    sw_path = args.swpath,
                                    json_path = json_path,
                                    thrift_port = 22223,
                                    pcap_dump = not args.nopcap,
                                    #pcap_dir = "out",
                                    log_console = True, #TODO
                                    enable_debugger = False)
            s2 = self.addSwitch('r2',
                                    cls=P4Switch,
                                    sw_path = args.swpath,
                                    json_path = json_path,
                                    thrift_port = 22224,
                                    pcap_dump = not args.nopcap,
                                    #pcap_dir = "out",
                                    log_console = True, #TODO
                                    enable_debugger = False)
        else:
            aqm_switch = self.addNode( 'r1', cls=LinuxRouter )
            s1 = self.addSwitch('s1')
            s2 = self.addSwitch('s2')

        #s2 = self.addSwitch('s2')

        h1 = self.addHost('h1', ip = '10.0.1.1/24',
                          mac = '00:00:00:00:01:01',
			  defaultRoute='via 10.0.1.10 dev eth0')
        h2 = self.addHost('h2', ip = '10.0.2.2/24',
                          mac = '00:00:00:00:02:02',
			  defaultRoute='via 10.0.2.20 dev eth0')
        h3 = self.addHost('h3', ip = '10.0.3.3/24',
                          mac = '00:00:00:00:03:03',
			  defaultRoute='via 10.0.3.30 dev eth0')                         
        h4 = self.addHost('h4', ip = '10.0.4.4/24',
                          mac = '00:00:00:00:04:04',
			  defaultRoute='via 10.0.4.40 dev eth0')

        self.addLink(h1, s1, delay='2ms', intfName2='r1-eth1', addr2="00:00:00:00:01:00")
        self.addLink(h2, s1, delay='2ms', intfName2='r1-eth2', addr2="00:00:00:00:02:00")
        self.addLink(h3, s2, delay='2ms', intfName2='r2-eth1', addr2="00:00:00:00:03:00")
        self.addLink(h4, s2, delay='2ms', intfName2='r2-eth2', addr2="00:00:00:00:04:00")

        #TODO: Fix addLink for the routers
        #self.addLink(s1, aqm_switch,
        #             intfName2='r1-eth1',
        #             addr2="00:00:00:00:01:fe")
        #self.addLink(s2, aqm_switch,
        #             intfName2='r1-eth2',
        #             addr2="00:00:00:00:02:fe")

        self.addLink(s1,aqm_switch,intfName1='r1-eth3',intfName2='r0-eth1', delay='2ms')
        self.addLink(s2,aqm_switch,intfName1='r2-eth3',intfName2='r0-eth2', delay='2ms')

def main():
    p4 = True if args.useP4 is not None else False


    topo = MyTopo(json_path = args.json,
                  p4=p4)
    mn = Mininet(topo = topo,
                  link = TCLink,
                  host = P4Host,
                  autoStaticArp=True  )

    internet_hosts = ["h1", "h2"]
    homenet_hosts = ["h3", "h4"]
    routers = ["r0", "r1", "r2"]
    for h in mn.hosts:
        print("disable ipv6")
        print(h.name)
        h.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")
        if h.name == "h1":
            h.setARP("10.0.1.10", "00:00:00:00:01:00")
            h.setDefaultRoute("via 10.0.1.10 dev eth0")	
	elif h.name == "h2":
            h.setARP("10.0.2.20", "00:00:00:00:02:00")
	    h.setDefaultRoute("via 10.0.2.20 dev eth0")
	elif h.name == "h3":
	    h.setARP("10.0.3.30", "00:00:00:00:03:00")
	    h.setDefaultRoute("via 10.0.3.30 dev eth0")
	elif h.name == "h4":
	    h.setARP("10.0.4.40", "00:00:00:00:04:00")
	    h.setDefaultRoute("via 10.0.4.40 dev eth0")
        #elif h.name in homenet_hosts:
            #h.setARP("10.0.2.254", "00:00:00:00:02:fe")
            #h.setDefaultRoute("via 10.0.3.254 dev eth0")
        elif h.name in routers: #in case of linux kernel router
            print(h.name)
            h.setMAC("00:00:00:00:01:fe", intf="r1-eth1")
            h.setMAC("00:00:00:00:02:fe", intf="r1-eth2")
            h.setIP(ip="10.0.1.254", prefixLen=24, intf="r1-eth1")
            h.setIP(ip="10.0.2.254", prefixLen=24, intf="r1-eth2")
            h.setARP("10.0.1.1", "00:00:00:00:01:01")
            h.setARP("10.0.1.2", "00:00:00:00:01:02")
            h.setARP("10.0.3.1", "00:00:00:00:02:01")
            h.setARP("10.0.3.2", "00:00:00:00:02:02")

    for sw in mn.switches:
        print("disable ipv6")
        print(sw)
        sw.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        sw.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        sw.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")


    mn.start()
    if not p4 and not args.nopcap:
        r1 = mn.getNodeByName('r1')
        r1.start()

        
    iperfTest = IperfTest()

    if p4:
        sleep(1)
	r1 = mn.getNodeByName('r1')
        r1.setIP(ip="10.0.1.10", prefixLen=24, intf="r1-eth1")
        r1.setIP(ip="10.0.2.20", prefixLen=24, intf="r1-eth2")

	r2 = mn.getNodeByName('r2')
        r2.setIP(ip="10.0.3.30", prefixLen=24, intf="r2-eth1")
        r2.setIP(ip="10.0.4.40", prefixLen=24, intf="r2-eth2")

        for i in range(3):
            '''r1 = mn.getNodeByName('r%d'%(i))
            r1.setIP(ip="10.0.%d.254"%(1+i), prefixLen=24, intf="r%d-eth1"%(i))
            r1.setIP(ip="10.0.%d.254"%(3+i), prefixLen=24, intf="r%d-eth2"%(i))'''
            cmd = [args.cli,  args.json, "2222%d"%(i+2)]
            print(args.cliCmd)
            with open(args.cliCmd.split(',')[i], "r") as f:
                print(" ".join(cmd))
                try:
                    print("Running %s" % cmd)
                    output = subprocess.check_output(cmd, stdin = f)
                    print(output)
                except subprocess.CalledProcessError as e:
                    print(e)
                    print(e.output)



    sleep(1)

    print("Now the iperf test starts !")
    iperfTest.IperfTest(mn.getNodeByName('h1'), mn.getNodeByName('h3'), mn.getNodeByName('h2'), mn.getNodeByName('h4'), args.iperft, args.bw)
    if args.nocli:
        CLI( mn )
    mn.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    main()
