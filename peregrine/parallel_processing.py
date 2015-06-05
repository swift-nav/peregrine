# Multiprocessing helper functions thanks to stackoverflow user 'klaus se''
# http://stackoverflow.com/questions/3288595/16071616#16071616

import progressbar as pb
import multiprocessing as mp
import time

def spawn(f):
    def fun(q_in, q_out):
        while True:
            i,x = q_in.get()
            if i is None:
                break
            q_out.put((i,f(x)))
    return fun

def parmap(f, X, nprocs = mp.cpu_count(), progress=True):
    q_in   = mp.Queue(1)
    q_out  = mp.Queue()

    proc = [mp.Process(target=spawn(f),args=(q_in,q_out)) for _ in range(nprocs)]

    for p in proc:
        p.daemon = True
        p.start()

    if progress:
        pbar = pb.ProgressBar(widgets=[pb.Percentage(), ' ', pb.ETA()], maxval=len(X)).start()
    sent=[]
    for i, x in enumerate(X):
        sent.append(q_in.put((i,x)))
        if progress:
            pbar.update(i)

    [q_in.put((None,None)) for _ in range(nprocs)]
    pbar.finish()

    res = [q_out.get() for _ in range(len(sent))]

    [p.join() for p in proc]

    return [x for i,x in sorted(res)]
