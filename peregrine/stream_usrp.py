#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Stream
# Author: Henry Hallam
# Description: Streams samples to one or more USRPs
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
    def __init__(self, filenames, dev_addrs,
                 onebit, iq, noise, mix, gain, fs, fc, unint, sync_pps):
        gr.top_block.__init__(self)

        if mix:
            raise NotImplementedError("TODO: Hilbert remix mode not implemented.")

        uhd_sinks = [
            uhd.usrp_sink(",".join(
                [addr, "send_frame_size=32768,num_send_frames=128"]),
                          uhd.stream_args(
                              cpu_format="fc32",
                              otwformat="sc8",
                              channels=[0]))
            for addr in dev_addrs]

        for sink in uhd_sinks:
            sink.set_clock_rate(fs*2, uhd.ALL_MBOARDS)
            sink.set_samp_rate(fs)
            sink.set_center_freq(fc, 0)
            sink.set_gain(gain, 0)
            # TODO Use offset tuning?
            if sync_pps:
                sink.set_clock_source("external") # 10 MHz
                sink.set_time_source("external") # PPS

        if unint:
            if noise or onebit or not iq:
                raise NotImplementedError("TODO: RX channel-interleaved mode only "
                                          "supported for noiseless 8-bit complex.")
            
            BLOCK_N=16*1024*1024
            demux = blocks.vector_to_streams(2, len(uhd_sinks))
            self.connect(blocks.file_source(2*len(uhd_sinks)*BLOCK_N, filenames[0], False),
                         blocks.vector_to_stream(2*len(uhd_sinks), BLOCK_N),
                         demux)
            for ix, sink in enumerate(uhd_sinks):
                self.connect((demux, ix),
                             blocks.vector_to_stream(1, 2),
                             blocks.interleaved_char_to_complex(), # [-128.0, +127.0]
                             blocks.multiply_const_cc(1.0/1024), # [-0.125, 0.125)
#                             blocks.vector_to_stream(8, 16*1024),
                             sink)

        else:
            file_srcs = [blocks.file_source(gr.sizeof_char*1, f, False)
                         for f in filenames]

            for src, sink in zip(file_srcs, uhd_sinks):

                if iq:
                    node = blocks.multiply_const_cc(1.0/1024)
                    if onebit:
                        self.connect(src,
                                     blocks.unpack_k_bits_bb(8), 
                                     blocks.char_to_short(), # [0, 1] -> [0, 256]
                                     blocks.add_const_ss(-128), # [-128, +128],
                                     blocks.interleaved_short_to_complex(), # [ -128.0, +128.0]
                                     node) # [-0.125, +0.125]
                    else:
                        self.connect(src, # [-128..127]
                                     blocks.interleaved_char_to_complex(), # [-128.0, +127.0]
                                     node) # [-0.125, +0.125)
                    
                else:
                    node = blocks.float_to_complex(1)
                    if onebit:
                        self.connect(src,
                                     blocks.unpack_k_bits_bb(8), # [0, 1] -> [-0.125, +0.125]
                                     blocks.char_to_float(vlen=1, scale=4),
                                     blocks.add_const_vff((-0.125, )),
                                     node)
                    else:
                        self.connect(src, # [-128..127] -> [-0.125, +0.125)
                                     blocks.char_to_float(vlen=1, scale=1024),
                                     node)
                        
                if noise:
                    combiner = blocks.add_vcc(1)
                    self.connect(node,
                                 combiner,
                                 sink)
                    self.connect(analog.fastnoise_source_c(analog.GR_GAUSSIAN, noise, -222, 8192),
                                 (combiner, 1))
                else:
                    self.connect(node,
                                 sink)

        print "Setting clocks..."
        if sync_pps:
            time.sleep(1.1) # Ensure there's been an edge.  TODO: necessary?
            last_pps_time = uhd_sinks[0].get_time_last_pps()
            while last_pps_time == uhd_sinks[0].get_time_last_pps():
                time.sleep(0.1)
            print "Got edge"
            [sink.set_time_next_pps(uhd.time_spec(round(time.time())+1)) for sink in uhd_sinks]
            time.sleep(1.0) # Wait for edge to set the clocks
        else:
            # No external PPS/10 MHz.  Just set each clock and accept some skew.
            t = time.time()
            [sink.set_time_now(uhd.time_spec(time.time())) for sink in uhd_sinks]
            if len(uhd_sinks) > 1:
                print "Uncabled; loosely synced only. Initial skew ~ %.1f ms" % (
                    (time.time()-t) * 1000)

        t_start = uhd.time_spec(time.time() + 1.5)
        [sink.set_start_time(t_start) for sink in uhd_sinks]
        print "ready"
            
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("files", help="input file(s)", nargs='+')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-8", dest="eightbit", action="store_true",
                       help="Sample file(s) are 8-bit signed")
    group.add_argument("-1", dest="onebit", action="store_true",
                       help="Sample file(s) are 1-bit, MSB first")
    parser.add_argument("-c", dest="iq", action="store_true",
                       help="Samples are interleaved complex I,Q (real only)")
    parser.add_argument("-i", dest="unint", action="store_true",
                       help="Single file with samples interleaved between channels")
    parser.add_argument("-u", dest="addrs", nargs='+', default=[],
                        help="USRP identifier(s), e.g. serial=123456")
    parser.add_argument("-r", dest="fs", default=16368000.0, type=float,
                        help="Sampling rate (%(default).0f)")
    parser.add_argument("-m", dest="mix", action='store_true',
                        help="Apply Hilbert mixer, downmixing by fs/4")
    parser.add_argument("-p", dest="pps", action='store_true',
                        help="Sync multiple USRPs with external PPS and 10 MHz")
    parser.add_argument("-n", dest="noise", default=0, type=float,
                        help="Add this much noise (%(default).1f)")
    parser.add_argument("-g", dest="gain", default=20.0, type=float,
                        help="TX gain / dB (%(default).0f)")
    parser.add_argument("-f", dest="fc", default=1.57542e9-4.092e6, type=float,
                        help="Center frequency (%(default).0f)")
    args = parser.parse_args()

    if not args.eightbit and not args.onebit:
        # Infer 8-bit vs 1-bit from filename
        if args.files[0][-3:] == ".s8" or args.files[0][-4:] == ".int8":
            args.eightbit=True
        elif args.files[0][-5:] == ".1bit":
            args.onebit=True
        else:
            print "You didn't specify 8-bit or 1-bit, and I can't guess from the filename."
            sys.exit(posix.EX_USAGE)

    if len(args.addrs) < len(args.files):
        args.addrs.extend(['' for _ in range(len(args.files)-len(args.addrs))])

    if args.unint and len(args.files) > 1:
        print "Interleaved channel mode (-i) specified, but more than one file given."
        sys.exit(posix.EX_USAGE)

    tb = streamer(filenames=args.files, dev_addrs=args.addrs,
                  onebit=args.onebit, iq=args.iq, noise=args.noise,
                  mix=args.mix, gain=args.gain, fs=args.fs, fc=args.fc,
                  unint=args.unint,
                  sync_pps=args.pps)
    tb.start()
    tb.wait()
