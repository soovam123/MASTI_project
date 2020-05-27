/*
* Copyright 2018-present Ralf Kundel, Nikolas Eller
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

#include <core.p4>
#include <v1model.p4>

#define add_queue_delay
#define ENABLE_DEBUG_TABLES

#include "header.p4"

#ifdef add_queue_delay
#include "queue_measurement.p4"
#include "tcp_checksum.p4"
#endif

#define PKT_INSTANCE_TYPE_INGRESS_CLONE 1

//const bit<32> BMV2_V1MODEL_INSTANCE_TYPE_INGRESS_CLONE = 1;

//#define IS_I2E_CLONE(std_meta) (std_meta.instance_type == BMV2_V1MODEL_INSTANCE_TYPE_INGRESS_CLONE)

//const bit<32> I2E_CLONE_SESSION_ID = 5;

parser ParserImpl(packet_in packet, out headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        meta.routing_metadata.tcpLength = hdr.ipv4.totalLen;
        transition select(hdr.ipv4.protocol) {
            8w17: parse_udp;
            8w6: parse_tcp;
            default: accept;
        }
    }
    state parse_payload {
        packet.extract(hdr.tcp_options);
	#ifdef add_queue_delay
        packet.extract(hdr.queue_delay);
	#endif
        transition accept;
    }
    state parse_tcp {
        packet.extract(hdr.tcp);
	#ifdef add_queue_delay
        transition select(hdr.tcp.dataOffset) {
            4w0x8: parse_payload;
            default: accept;
        }
	#else
	transition accept;
	#endif
    }
    state parse_udp {
        packet.extract(hdr.udp);
        transition select(hdr.udp.destPort) {
            default: accept;
        }
    }
    state start {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.ethertype) {
            16w0x800: parse_ipv4;
            default: accept;
        }
    }
}

#ifdef ENABLE_DEBUG_TABLES
control debug_std_meta(in standard_metadata_t standard_metadata)
{
    table dbg_table {
        key = {
            // This is a complete list of fields inside of the struct
            // standard_metadata_t as of the 2018-Sep-01 version of
            // p4c in the file p4c/p4include/v1model.p4.

            // parser_error is commented out because the p4c back end
            // for bmv2 as of that date gives an error if you include
            // a field of type 'error' in a table key.
            standard_metadata.ingress_port : exact;
            standard_metadata.egress_spec : exact;
            standard_metadata.egress_port : exact;
            standard_metadata.instance_type : exact;
            standard_metadata.packet_length : exact;
            standard_metadata.enq_timestamp : exact;
            standard_metadata.enq_qdepth : exact;
            standard_metadata.deq_timedelta : exact;
            standard_metadata.deq_qdepth : exact;
            standard_metadata.ingress_global_timestamp : exact;
            standard_metadata.egress_global_timestamp : exact;
            standard_metadata.mcast_grp : exact;
            standard_metadata.egress_rid : exact;
            standard_metadata.checksum_error : exact;
            //standard_metadata.parser_error : exact;
        }
        actions = { NoAction; }
        const default_action = NoAction();
    }
    apply {
        dbg_table.apply();
    }
}

control my_debug_1(in headers hdr, in metadata meta)
{
    table dbg_table {
        key = {
            hdr.ipv4.dstAddr : exact;
            meta.fwd.fptr : exact;
        }
        actions = { NoAction; }
        const default_action = NoAction();
    }
    apply {
        dbg_table.apply();
    }
}
#endif  // ENABLE_DEBUG_TABLES

control egress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    #ifdef ENABLE_DEBUG_TABLES
        debug_std_meta() debug_std_meta_egress_start;
        debug_std_meta() debug_std_meta_egress_end;
    #endif  // ENABLE_DEBUG_TABLES

    c_checksum() c_checksum_0;
    c_add_queue_delay() c_add_queue_delay_0;

    action change_macs(bit<48> smac, bit<48> dmac, bit<32> dip) {
        hdr.ethernet.src_addr = smac;
        hdr.ethernet.dst_addr = dmac;
        hdr.ipv4.dstAddr = dip;
    }

    table exchange_mac {
        actions = {
            change_macs;
        }
        key = {
            hdr.ipv4.srcAddr : exact; 
        }
    }

    apply {
    
        #ifdef ENABLE_DEBUG_TABLES
            debug_std_meta_egress_start.apply(standard_metadata);
        #endif  // ENABLE_DEBUG_TABLES 
        
        #ifdef add_queue_delay
            c_add_queue_delay_0.apply(hdr, standard_metadata);
            c_checksum_0.apply(hdr, meta);
        #endif

        if (standard_metadata.instance_type == PKT_INSTANCE_TYPE_INGRESS_CLONE) {
            exchange_mac.apply();
        }

        #ifdef ENABLE_DEBUG_TABLES
            debug_std_meta_egress_end.apply(standard_metadata);
        #endif  // ENABLE_DEBUG_TABLES

    }
}

control ingress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    #ifdef ENABLE_DEBUG_TABLES
        debug_std_meta() debug_std_meta_ingress_start;
        debug_std_meta() debug_std_meta_ingress_end;
        my_debug_1() my_debug_1_1;
        my_debug_1() my_debug_1_2;
    #endif  // ENABLE_DEBUG_TABLES

    action forward(bit<9> egress_spec, bit<48> dst_mac) {
        standard_metadata.egress_spec = egress_spec;
        hdr.ethernet.dst_addr = dst_mac;
    }

    action clone_i2e(bit<32> fptr, bit<32> session_id) {
        //const bit<32> REPORT_MIRROR_SESSION_ID = 5;

        clone(CloneType.I2E, session_id);   //REPORT_MIRROR_SESSION_ID);
        meta.fwd.fptr = fptr;
    }

    table cloning {
        actions = {
            clone_i2e;
        }
        key = {
            standard_metadata.ingress_port: exact;
            hdr.ipv4.dstAddr              : exact;
        }
    }

    table forwarding {
        actions = {
            forward;
        }
        key = {
            //meta.fwd.fptr                 : exact;
            standard_metadata.ingress_port: exact;
            hdr.ipv4.dstAddr              : exact;
        }
    }

    apply {
        #ifdef ENABLE_DEBUG_TABLES
            debug_std_meta_ingress_start.apply(standard_metadata);
            my_debug_1_1.apply(hdr, meta);
        #endif  // ENABLE_DEBUG_TABLES
        
        forwarding.apply();
        cloning.apply();

        #ifdef ENABLE_DEBUG_TABLES
            my_debug_1_2.apply(hdr, meta);
            debug_std_meta_ingress_end.apply(standard_metadata);
        #endif  // ENABLE_DEBUG_TABLES
        
    }
}

control DeparserImpl(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.tcp);
        packet.emit(hdr.tcp_options);
        packet.emit(hdr.queue_delay);
        packet.emit(hdr.udp);
    }
}

V1Switch(ParserImpl(), verifyChecksum(), ingress(), egress(), computeChecksum(), DeparserImpl()) main;

