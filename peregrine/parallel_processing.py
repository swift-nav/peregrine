# Multiprocessing helper functions thanks to stackoverflow user 'klaus se''
# http://stackoverflow.com/questions/3288595/16071616#16071616

import progressbar as pb
import multiprocessing as mp
import time

def spawn(f):
    def worker(q_in, q_out, q_progress):
        while True:
            i,x = q_in.get()
            if i is None:
                break
            try:
                try:
                    # Does the function support progress reporting?
                    q_out.put((i,f(x, q_progress=q_progress)))
                except TypeError as e:
                    if e.message.endswith("got an unexpected keyword argument 'q_progress'"):
                        # No, it doesn't.
                        q_out.put((i,f(x)))
                        # Declare 100% progress on this workpiece when complete.
                        q_progress.put(1)
                    else:
                        raise e
            except Exception as err:
                print "Subprocess raised exception:"
                print err
                q_out.put(None)
    return worker

def parmap(f, X, nprocs = mp.cpu_count(), show_progress=True):
    q_in   = mp.Queue()
    q_out  = mp.Queue()
    q_progress  = mp.Queue(100)

    proc = [mp.Process(target=spawn(f),args=(q_in, q_out, q_progress)) for _ in range(nprocs)]

    for p in proc:
        p.daemon = True
        p.start()

    if show_progress:
        pbar = pb.ProgressBar(widgets=[pb.Percentage(), ' ', pb.ETA()], maxval=len(X)).start()

    [q_in.put((i, x)) for i, x in enumerate(X)]

    [q_in.put((None,None)) for _ in range(nprocs)]

    n_done = 0
    progress = 0
    res = []
    t0 = time.time()
    while n_done < len(X):
        while not q_out.empty():
            res.append(q_out.get_nowait())
            n_done += 1
        while not q_progress.empty():
            progress_increment = q_progress.get_nowait()
            progress += progress_increment
#            print time.time() - t0, progress_increment, progress, progress / len(X)
        if show_progress and progress <= len(X):
            pbar.update(progress)
        time.sleep(0.1)

    if show_progress:
        pbar.finish()

    [p.join() for p in proc]

    return [x for i,x in sorted(res)]
