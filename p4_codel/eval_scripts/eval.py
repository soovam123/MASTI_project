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

import argparse
import os, sys
import json
from plotting import *
from scapy.all import *


def parse_multi_iperf3_json(folder):
    range = [0, 2, 5, 10, 20, 50]
    all_runs = {}
    for i in range:
        path = os.path.join(folder, "iperf_output"+str(i)+".json")
        if not os.path.isfile(path):
            return None
        parse_result = parse_iperf3_json(path)
        all_runs[i] = parse_result
    return all_runs



def parse_iperf3_json(path):
    content = readFiletoString(path)
    content = json.loads(content)
    #now content is a dict
    loRawInputs = content['intervals']
    resLst = []
    for x in loRawInputs:
        innerLst = []
        for y in x['streams']:
            innerLst.append(y) #TODO hier wird nur der erste Stream geparst
        resLst.append(innerLst)
    return  resLst

def parse_ping_trace(folder, dropFirstN=0):
    content = readFiletoString(os.path.join(folder, "ping_out.txt"))
    lines=content.splitlines()
    del lines[0] #"'PING 10.0.0.4 (10.0.0.4) 56(84) bytes of data.'"
    del lines[:dropFirstN]
    del lines[-4:] #delete last lines
    result = []
    for line in lines:
        splitline = line.split(" ")
        ping_time = splitline[6].replace("time=", "")
        result.append(float(ping_time))
    return result

def parse_pcap_trace(folder, index):
    # TODO: set the packets_in and packets_out for the links/interfaces we want to test; Maybe make this a cli arg?
    if(index == 0):
        packets_in = rdpcap(os.path.join(folder, "r1-eth1_out.pcap"))
        packets_out = rdpcap(os.path.join(folder, "r2-eth1_in.pcap"))
    else:
        packets_in = rdpcap(os.path.join(folder, "r1-eth2_out.pcap"))
        packets_out = rdpcap(os.path.join(folder, "r2-eth2_in.pcap"))
    out_pointer = 0
    print("number ingoing packets "+str(index)+" : "+str(len(packets_in)))
    print("number outgoing packets "+str(index)+" : "+str(len(packets_out)))
    resLst = []
    length = len(packets_out)
    dropLst = []
    basePacket = packets_in[0]
    counterDrops = 0
    pk_in = 0
    out_of_order = []
    for packet in packets_in:
        if (length == out_pointer):
            break
        # TODO: Do we want to also ignore packets.len < 500?
        # Ignore non-TCP packets in packets_in
        if packet['IP'].proto != 6:
            pk_in += 1
            continue
        # Ignore non-TCP packets in packets_out
        while packets_out[out_pointer]['IP'].proto != 6:
            out_pointer += 1
        out_packet = packets_out[out_pointer]
        tcp_in = packet['TCP']
        tcp_out = out_packet['TCP']
        #print("%d %d" %(pk_in, tcp_in.seq))
        #print("%d %d" %(out_pointer, tcp_out.seq))
        pk_in += 1
        if (tcp_out.seq < packets_out[out_pointer - 1]['TCP'].seq):
            out_of_order.append(out_packet)
            out_pointer += 1
            if(length != out_pointer):
                tcp_out = packets_out[out_pointer]['TCP']
            else:
                break

        match = tcp_in.seq == tcp_out.seq
        if(match):
            out_pointer+=1
            resLst.append((packet, out_packet))
            #print(tcp_in.seq)
            #print("Matched this:")
            #print("r1-eth1_out: %d" %(tcp_in.seq))
            #print("r1-eth3_in: %d" %(tcp_out.seq))
            #print("\n\n")
        else:
            counterDrops = counterDrops + 1
            #print("Dropped sequence: " + str(tcp_in.seq))
            #print("Packet dropped: " + str(packet.time - basePacket.time))
            dropLst.append(packet)
            #print(tcp_in.seq)
            #print(out_pointer)
            #break
    print("number drops "+str(index)+" : " + str(counterDrops))
    print("number matched packets "+str(index)+" : "+str(len(resLst)))
    print("number of out_of_orders "+str(index)+" :" + str(len(out_of_order)))
    return packets_in, resLst

def readFiletoString(file_name):
    file = open(file_name, "r")
    content = file.read()
    return content
#  2034089065


def evaluate(folder, index):
    if not check_for_pcap(folder):
        return
    out_folder = os.path.join(os.getcwd(), folder)
    #evaluate_iperf(out_folder)
    #pingResLst = parse_ping_trace(out_folder)

    pcap_in_trace, pcap_trace = parse_pcap_trace(out_folder, index)
    plotPcapTrace(pcap_trace, index)
    plotPcapInBandwidth(pcap_in_trace)
    plotPcapBandwidth(pcap_trace)
    #plotPcapQueueDelay(pcap_trace)

def evaluate_iperf(folder, index):
    out_folder = os.path.join(os.getcwd(), folder)
    json_file = "iperf_output_" + str(index) + ".json"
    iperf3_file = os.path.join(out_folder, json_file)
    if not os.path.isfile(iperf3_file):
        return
    iperf3ResLst = parse_iperf3_json(iperf3_file)
    plotIperf3(iperf3ResLst, index)

def evaluate_multi_iperf(folder):
    res = parse_multi_iperf3_json(folder)
    if res != None:
        plot_multiple_iperf3_runs(res)

def check_for_pcap(folder):
    # TODO: set the packets_in and packets_out for the interfaces we want to test
    packets_in = os.path.join(folder, "r1-eth1_out.pcap")
    packets_out = os.path.join(folder, "r2-eth1_in.pcap")
    if not os.path.isfile(packets_in):
        return False
    if not os.path.isfile(packets_out):
        return False
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Processes the mininet out files and creates statistics')
    parser.add_argument('Path', nargs='?', default="out", help='path to out folder')
    parser.add_argument('--gui', help='Show plots in a GUI',
                        type=bool, action="store")
    parser.set_defaults(gui=False)
    args = parser.parse_args()
    folder = args.Path

    evaluate_multi_iperf(folder)

    # Change range to according to the flows
    for index in range(2):    
        evaluate_iperf(folder, index)
        evaluate(folder, index)

    if args.gui:
        show_plots()
