from scipy import signal
import numpy as np
import matplotlib.pyplot as plt
from StringIO import StringIO
import argparse

def main():
  parser = argparse.ArgumentParser()

  parser.add_argument("-f", "--file", default="tracking_res.csv",
                      help="the input CSV file to process")

  parser.add_argument("-p", "--par-to-print", default="CN0",
                      help="parameter to print")

  parser.add_argument("-s", "--time-step", default="0.1",
                      help="time step [s]")

  args = parser.parse_args()

  fig = plt.figure()
  #plt.title('Carrier tracking loop filter frequency response')
  ax1 = fig.add_subplot(111)

  plt.ylabel(args.par_to_print, color='b')
  plt.xlabel('time [%s s]' % float(args.time_step))

  data = np.genfromtxt(args.file, dtype=float, delimiter=',', names=True)

  plt.plot(np.array(range(len(data[args.par_to_print]))),
           np.array(data[args.par_to_print]), 'r.')

  plt.legend(loc='upper right')

  plt.grid()
  plt.axis('tight')
  plt.show()

if __name__ == '__main__':
   main()
