import numpy as np
from collections import defaultdict

def consecutive(data, stepsize=1): 
    return np.split(data, np.where(np.diff(data) != stepsize)[0]+1) 

fname = "test_output_bb.txt_desc_t5"
lines = ""
qdict = defaultdict(lambda: defaultdict(dict))   
with open(fname) as f: 
    for line in f: 
        qid,_,docid,_,score,_ = line.strip().split() 
        qdict[qid][docid] = np.exp(float(score))

for key in qdict: 
    val = qdict[key] 
    doc_dict = defaultdict(lambda: defaultdict(list))
    val = dict(sorted(val.items(),key=lambda w : w[1],reverse=True))
    i = 1
    for doc,score in val.items(): 
         docid, pos = doc.split("_") 
         pos = int(float(pos)/60) 
         doc_dict[docid]["position"].append(pos)
         doc_dict[docid]["scores"].append(score)
         doc_dict[docid]["rank"].append(i)
         i += 1

    new_dict = {}
    for docid,val in doc_dict.items():
        pos = val["position"]
        score = val["scores"]
        rank = dict(zip(pos,val["rank"]))
        tmp = dict(sorted(zip(pos,score),key=lambda w: w[0]))
        for arr in consecutive(list(tmp.keys())): 
            total = 0 
            if len(arr)==1: 
                new_dict["{}_{}.0".format(docid,60*arr[0])] = tmp[arr[0]]
            else:
                min_rank = 1000
                # max_rank = 1
                for v in arr: 
                    total += tmp[v]
                    min_rank = min(min_rank,rank[v])
                #     max_rank = max(max_rank, rank[v])
                # avg1 = total/len(val)/(1000*min_rank)
                # avg2 = (max(arr)-min(arr))/min_rank
                # avg = (avg1+avg2)/2
                avg = total/len(val)/(1500*min_rank)
                for v in arr: 
                    new_dict["{}_{}.0".format(docid,60*v)] = tmp[v]+avg
                
                # for i,v in enumerate(arr):
                #     if i==0 or i==len(arr)-1: 
                #         new_dict["{}_{}.0".format(docid,60*v)] = tmp[v]
                #     else:
                #         avg = sum(arr[i-1:i+2])/3
                #         min_rank = min([rank[p] for p in arr[i-1:i+2]])
                #         new_dict["{}_{}.0".format(docid,60*v)] = tmp[v] + avg/(1000)


                
    rank = 1
    for doc,score in sorted(new_dict.items(),key=lambda w: w[1],reverse=True):
        lines += f"{key} Q0 {doc} {rank} {score} postboost\n"
        rank += 1

        
with open(f"{fname}_postboost","w") as f:
    f.write(lines)