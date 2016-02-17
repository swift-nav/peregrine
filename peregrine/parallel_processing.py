# Multiprocessing helper functions thanks to stackoverflow user 'klaus se''
# http://stackoverflow.com/questions/3288595/16071616#16071616

import progressbar as pb
import multiprocessing as mp
import time
import sys
import traceback


def spawn(f):
  def worker(q_in, q_out, q_progress):
    while True:
      i, x = q_in.get()
      if i is None:
        break
      try:
        if q_progress:
          res = f(x, q_progress=q_progress)
          q_out.put((i, res))
        else:
          res = f(x)
          q_out.put((i, res))
      except:
        print "Subprocess raised exception:"
        exType, exValue, exTraceback = sys.exc_info()
        traceback.print_exception(
            exType, exValue, exTraceback, file=sys.stdout)
        q_out.put(None)
  return worker


def parmap(f, X, nprocs=mp.cpu_count(), show_progress=True, func_progress=False):
  q_in = mp.Queue()
  q_out = mp.Queue()
  if func_progress:
    q_progress = mp.Queue(100)
  else:
    q_progress = None

  proc = [mp.Process(target=spawn(f), args=(q_in, q_out, q_progress))
          for _ in range(nprocs)]

  for p in proc:
    p.daemon = True
    p.start()

  if show_progress:
    pbar = pb.ProgressBar(
        widgets=[pb.Percentage(), ' ', pb.ETA()], maxval=len(X)).start()

  [q_in.put((i, x)) for i, x in enumerate(X)]

  [q_in.put((None, None)) for _ in range(nprocs)]

  n_done = 0
  progress = 0
  res = []
  t0 = time.time()
  while n_done < len(X):
    if func_progress:
      time.sleep(0.02)
    else:
      res.append(q_out.get())
      n_done += 1
    while not q_out.empty():
      res.append(q_out.get())
      n_done += 1
    if q_progress:
      while not q_progress.empty():
        progress_increment = q_progress.get_nowait()
        progress += progress_increment
    else:
      progress = n_done
    if show_progress and progress <= len(X):
      pbar.update(progress)

  if show_progress:
    pbar.finish()

  [p.join() for p in proc]

  return [x for i, x in sorted(res)]
