
from collections import Counter, deque
class TemporalConsensus:
    def __init__(self,window=12): self.items=deque(maxlen=int(window))
    def clear(self): self.items.clear()
    def reject(self): self.clear()
    def update(self,label,confidence): self.items.append((str(label),float(confidence)))
    def result(self,min_votes,min_mean_confidence):
        if not self.items:return None
        label,votes=Counter(x[0] for x in self.items).most_common(1)[0]
        conf=[c for l,c in self.items if l==label]; mean=sum(conf)/len(conf)
        return (label,mean,votes) if votes>=min_votes and mean>=min_mean_confidence else None
