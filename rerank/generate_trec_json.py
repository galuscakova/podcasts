import argparse
import os
import json
from tqdm import tqdm

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to create trec_json file from trec file')

    parser.add_argument('--input_file', type=str, required=True)
    parser.add_argument('--corpus_file', type=str, required=True)
    parser.add_argument('--output_file', type=str, required=True)
    args = parser.parse_args()

    corpus_dict = {}
    with open(args.corpus_file) as f:
        for line in tqdm(f):
            temp = json.loads(line.strip())
            docno = temp["docno"]
            docno = docno.replace("0.0.0","0.0")
            if docno not in corpus_dict:
                corpus_dict[docno] = {}
            corpus_dict[docno]["body"] = temp["body"]
            corpus_dict[docno]["title"] = temp["title"]

    print(len(corpus_dict))
    output_lines = []
    with open(args.input_file) as f:
        for line in tqdm(f):
            line = line.strip()
            if not line: continue
            docid = line.split()[2]
            doc_dict = {}
            doc_dict["doc"] = {}
            doc_dict["doc"]["body"] = corpus_dict[docid]["body"]
            doc_dict["doc"]["title"] = corpus_dict[docid]["title"]
            out = line + " # {}\n".format(json.dumps(doc_dict))
            output_lines.append(out)
            
    with open(args.output_file,"w") as f:
        f.write("".join(output_lines))
    