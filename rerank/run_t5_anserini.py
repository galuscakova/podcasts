import torch
import json
import string
import argparse
from tqdm import tqdm
from transformers import AutoTokenizer, T5ForConditionalGeneration
from pygaggle.model import T5BatchTokenizer
from pygaggle.rerank.base import Query, Text
from pygaggle.rerank.transformer import T5Reranker

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to generate MSMARCO pretrained t5-base model predictions')

    parser.add_argument('--input_file', type=str, required=True)
    parser.add_argument('--query_field', type=str, required=True)
    args = parser.parse_args()
    
    model_name = 'castorini/monot5-base-msmarco'
    tokenizer_name = 't5-base'
    batch_size = 8

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    model = T5ForConditionalGeneration.from_pretrained(model_name)
    model = model.to(device).eval()

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    tokenizer = T5BatchTokenizer(tokenizer, batch_size)
    reranker =  T5Reranker(model, tokenizer)

    query_dict = {}
    with open("train_queries.json") as f:
        for line in f:
            temp = json.loads(line.strip())
            query_dict[temp['qid']] = temp[args.query_field]
    print(len(query_dict))

    pass_dict = {}
    with open(f"{args.input_file}.trec_json") as f:
        for line in f:
            a,b = line.strip().split("indri #")
            qid,_,docid,_,_ = a.strip().split()
            if qid not in pass_dict:
                pass_dict[qid] = {}
            temp = json.loads(b)
            pass_dict[qid][docid] = temp["doc"]["body"]# + " " + temp["doc"]["title"]
    print(len(pass_dict))

    lines = []
    for qid in tqdm(query_dict):
        query = Query(query_dict[qid])
        passages = pass_dict[qid].items()      
        texts = [ Text(p[1], {'docid': p[0]}, 0) for p in passages]

        reranked = reranker.rerank(query, texts)
        reranked.sort(key=lambda x: x.score, reverse=True)

        for i,res in enumerate(reranked,start=1):
            docid = res.raw["docid"]
            score = res.score
            lines.append(f"{qid} Q0 {docid} {i} {score} bert\n")

    with open(f"{args.input_file}_{args.query_field}_t5","w") as f:
        f.write("".join(lines))
    
