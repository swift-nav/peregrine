import sys
import time

class Waitbar(object):
    
    def __init__(self, use_eta=False,totalWidth=77):
        self.progBar = "[]"   # This holds the progress bar string
        self.min = 0.0
        self.max = 1.0
        self.span = self.max-self.min
        self.width = totalWidth
        
        self.display_eta=True
        
        self.amount = 0       # When amount == max, we are 100% done 
        self.update(0)  # Build progress bar string

        self.initial_time=time.time()
        
    def update(self, newAmount = 0):
        if newAmount < self.min: newAmount = self.min
        if newAmount > self.max: newAmount = self.max
        self.amount = newAmount

        # Figure out the new percent done, round to an integer
        diffFromMin = float(self.amount - self.min)
        percentDone = (diffFromMin / float(self.span)) * 100.0
        
        if self.display_eta:
            if percentDone==0.0:
                eta_str=' (ETA: ??)'
            else:
                dt=time.time()-self.initial_time
            
                eta=dt/percentDone*(100-percentDone)
                
                seconds=eta%60
                eta=int(eta/60)
                minutes=eta%60
                eta=int(eta/60)
                hours=eta%24
                eta=int(eta/24)
                days=eta
                
                eta_str=' (ETA: '
                if days:
                    eta_str+=str(days)+" d "
                if hours:
                    eta_str+=str(hours)+" h "
                if minutes:
                    eta_str+=str(minutes)+" m "
                eta_str+='%.1f s)' % seconds
                
                
        else:
            eta_str=''
        
        percentDone = round(percentDone)
        percentDone = int(percentDone)

        done_str=str(percentDone)+"%" +eta_str
        
        
        
        
        # Figure out how many hash bars the percentage should be
        allFull = self.width - 2
        numHashes = (percentDone / 100.0) * allFull
        numHashes = int(round(numHashes))

        # build a progress bar with hashes and spaces
        self.progBar = "[" + '#'*numHashes + ' '*(allFull-numHashes) + "]"

        # figure out where to put the percentage, roughly centered
        percentPlace = (len(self.progBar) / 2) - len(done_str)/2 
        percentString = done_str

        # slice the percentage into the bar
        self.progBar = self.progBar[0:percentPlace] + percentString + self.progBar[percentPlace+len(percentString):]

        
    def display(self):
        print self,
        sys.stdout.flush()
        
    def updated(self,newAmount=0):
        self.update(newAmount)
        self.display()
    
        
    def __str__(self):
        return str(self.progBar)+"\r"


if __name__=="__main__":
    import time
    w = Waitbar(False)
    for i in xrange(1000):
        w.update(i/1000.0)
        print w,
        time.sleep(.01)

