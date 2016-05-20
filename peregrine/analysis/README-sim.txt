Running L2C Performance Simulations
===================================

Performance simulations are run with run_sim.py tool which invokes iqgen_main.py 
and tracking_loop.py. The tool stores all the simulation results (including commands
for generating iq data and tracking l2c signal) in json file. Data is always appended
in given json file.

Thereafter, results are illustrated with plt_res.py which reads data from json file.

The json file contains following data for each iqgen and L2C tracking run:
{
    "acc":       # Acceleration (L1CA Hz / s)
    "avgcn0":    # Average of all tracker CN0 estimates
    "dopMaxErr": # Maximum Doppler frequency error
    "dopSigma1": # 1-sigma Doppler error (68.3% of errors is less than this)
    "dopSigma2": # 2-sigma Doppler error (95.5% of errors is less than this)
    "dopSigma3": # 3-sigma Doppler error (99.7% of errors is less than this)
    "duration":  # Length of simulation in seconds
    "iqgencmd":  # Command line for iqgen 
    "iqgencn0":  # L2C CN0 reported by iqgen
    "l2chip":    # Initial L2C code phase reported by iqgen
    "l2dop":     # Initial L2C Doppler frequency reported by iqgen
    "lockrate":  # PLL lock rate 
    "snr":       # SNR argument for iqgen
    "stamp":     # Wall clock time stamp of simulation run
    "trackcmd":  # Command line for running the tracking_loop.py
}


Performance data can be generated with following commands:

1) $ ./run_sim.py -l  -f result_1.json
   This command loops CN0 range for e.g PLL lock rate vs. CN0 or Doppler error vs. CN0 data.
   Results can be plotted with
   $ ./plt_res.py -l -f result_1.json  # Lockrate vs. CN0 or
   $ ./plt_res.py -s -f result_1.json  # 1-sigma Doppler error vs. CN0

2) $ ./run_sim.py -d -f result_2.json  # PLL lock acceleration tolerance
   This command loops CN0 range and for each CN0 bin, it loops acceleration until 
   PLL lock rate < 0.68 (1-sigma threshold). Full acceleration range is not run 
   but for each CN0 bin, the initial acceleration, from which looping starts, is 
   derived from the results of previous CN0 bin.
   Results can be plotted with
   $ ./plt_res.py -d -f result_2.json

3) $ ./run_sim -e -f result_3.json    # Frequency error acceleration tolerance
   This is like 2) but runs for Doppler error. The command loops CN0 range and for 
   each CN0 bin, it loops acceleration until 1-sigma Doppler error < 1/(12*20 ms)
   = 4.17 Hz. 
   Results can be plotted with
   $ ./plt_res.py -e -f result_3.json


Varying simulation parameters
=============================
Changing values in the python file is as easy as value in configuration file
and many times more clear than value in configuration file or on command line.
Therfore, all the parametrization takes place in modifying run_sim.py.

There are three main functions which can be configured: 

1) runCn0Range() 
User can change following simulation parameters
length = 60                   # Duration (s)
snrRng = range(-270,-350,-10) # SNR for iqgen command. Unit 0.1 dBHz
doppler = 0                   # Hz
acceleration = 0.0            # Hz / s

2) runDynamicLockRate()
Function runs acceleration range for each CN0 bin
length = 30                   # Duration (s)
snrRng = range(-300,-200,10)  # Unit 0.1 dBHz. Must run from low CN0 to high CN0
doppler = 0                   # Hz
accStep = 10                  # Size of single acceleration step (L1CA Hz/s)
lockRateThreshold = 0.68      # Failure threshold. When it is reached, the next CN0 bin is tried

3) runDynamicFreq()
Function runs acceleration range for each CN0 bin
length = 30                   # Duration (s)
snrRng = range(-300,-200,10)  # Unit 0.1 dBHz. Must run from low CN0 to high CN0
doppler = 0                   # Hz
accStep = 10                  # Size of single acceleration step (L1CA Hz/s)
freqErrThreshold = 1.0 / (12*0.02)  # Failure threshold. When it is reached, the next CN0 bin is tried


Changing CN0 estimator of plt_res.py
====================================
In plt_res.py there is a string which defines which CN0 estimate is used:
CN0STRING="avgcn0"     # CN0 from tracking
#CN0STRING="iqgencn0"  # CN0 from iqgen
