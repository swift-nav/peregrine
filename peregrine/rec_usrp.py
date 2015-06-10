#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Stream
# Author: Henry Hallam
# Description: Streams samples from one or more USRPs
##################################################

from gnuradio import analog
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
import time
import argparse
import sys
import posix

class streamer(gr.top_block):
    def __init__(self, filename, dev_addrs,
                 onebit, gain, digital_gain, fs, fc, sync_pps):
        gr.top_block.__init__(self)

        if onebit:
            raise NotImplementedError("TODO: 1-bit mode not implemented.")
        
        uhd_srcs = [
            uhd.usrp_source(",".join(
                [addr, "num_recv_frames=256,recv_frame_size=16384"]),
                          uhd.stream_args(
                              cpu_format="fc32",
                              otwformat="sc16",
                              channels=[0]))
            for addr in dev_addrs]

        str2vec = blocks.streams_to_vector(2, len(uhd_srcs))
        self.connect(str2vec,
                     blocks.stream_to_vector(2 * len(uhd_srcs), 16*1024*1024),
                     blocks.file_sink(2 * len(uhd_srcs) * 16 * 1024 * 1024, filename, False))
        
        for ix, src in enumerate(uhd_srcs):
            src.set_clock_rate(fs*2, uhd.ALL_MBOARDS)
            src.set_samp_rate(fs)
            src.set_center_freq(uhd.tune_request(fc, 3e6))
            src.set_gain(gain, 0)
            # TODO Use offset tuning?
            if sync_pps:
                src.set_clock_source("external") # 10 MHz
                src.set_time_source("external") # PPS

            self.connect(src,  # [-1.0, 1.0]
                         blocks.multiply_const_cc(32767 * digital_gain[ix]), # [-32767.0, 32767.0]
                         blocks.complex_to_interleaved_short(), #[-32768, 32767]
                         blocks.short_to_char(), #[-128, 127]
                         blocks.stream_to_vector(1, 2), # I,Q,I,Q -> IQ, IQ
                         (str2vec, ix))

        print "Setting clocks..."
        if sync_pps:
            time.sleep(1.1) # Ensure there's been an edge.  TODO: necessary?
            last_pps_time = uhd_srcs[0].get_time_last_pps()
            while last_pps_time == uhd_srcs[0].get_time_last_pps():
                time.sleep(0.1)
            print "Got edge"
            [src.set_time_next_pps(uhd.time_spec(round(time.time())+1)) for src in uhd_srcs]
            time.sleep(1.0) # Wait for edge to set the clocks
        else:
            # No external PPS/10 MHz.  Just set each clock and accept some skew.
            t = time.time()
            [src.set_time_now(uhd.time_spec(time.time())) for src in uhd_srcs]
            if len(uhd_srcs) > 1:
                print "Uncabled; loosely synced only. Initial skew ~ %.1f ms" % (
                    (time.time()-t) * 1000)

        t_start = uhd.time_spec(time.time() + 1.5)
        [src.set_start_time(t_start) for src in uhd_srcs]
        print "ready"
            
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="output file")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-8", dest="eightbit", action="store_true",
                       help="Sample format is 8-bit signed complex")
    group.add_argument("-1", dest="onebit", action="store_true",
                       help="Sample format is 1-bit, MSB first")
    parser.add_argument("-u", dest="addrs", nargs='+', default=[],
                        help="USRP identifier(s), e.g. serial=123456")
    parser.add_argument("-r", dest="fs", default=4.092e6, type=float,
                        help="Sampling rate (%(default).0f)")
    parser.add_argument("-p", dest="pps", action='store_true',
                        help="Sync multiple USRPs with external PPS and 10 MHz")
    parser.add_argument("-g", dest="gain", default=20.0, type=float,
                        help="RX analog gain / dB (%(default).0f)")
    parser.add_argument("-G", dest="digital_gain", default=[], type=float, nargs='+',
                        help="Digital gain per channel, to accont for uneven input signal strengths")
    parser.add_argument("-f", dest="fc", default=1.57542e9, type=float,
                        help="Center frequency (%(default).0f)")
    args = parser.parse_args()

    if not args.eightbit and not args.onebit:
        # Infer 8-bit vs 1-bit from filename
        if args.filename[-3:] == ".s8" or args.filename[-4:] == ".int8":
            args.eightbit=True
        elif args.filename[-5:] == ".1bit":
            args.onebit=True
        else:
            print "You didn't specify 8-bit or 1-bit, and I can't guess from the filename."
            sys.exit(posix.EX_USAGE)

    tb = streamer(filename=args.filename, dev_addrs=args.addrs,
                  onebit=args.onebit,
                  gain=args.gain, digital_gain=args.digital_gain,
                  fs=args.fs, fc=args.fc, sync_pps=args.pps)
    tb.start()
    tb.wait()
