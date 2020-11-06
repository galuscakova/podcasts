import os
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to process podcasts trascripts to json file')

    parser.add_argument('--input_file', type=str, required=True)
    parser.add_argument('--result_file', type=str, required=True)
    parser.add_argument('--output_file', type=str, required=True)
    args = parser.parse_args()

    input_lines = []
    with open(args.input_file) as f:
        for line in f:
            input_lines.append(line.strip())
    
    result_lines = []
    with open(args.result_file) as f:
        for line in f:
            result_lines.append(line.strip().split("\t")[1])
    
    out_dict = {}
    for input_line,score in zip(input_lines,result_lines):
        qid,_,docid,_,_,_ = input_line.split()
        if qid not in out_dict:
            out_dict[qid] = {}
        out_dict[qid][docid] = score


    with open(args.output_file,"w") as f:
        for key,val in out_dict.items():
            val = sorted(val.items(),key=lambda w: w[1], reverse=True)
            line = ""
            for i, (docid,score) in enumerate(val, start=1):
                line += f"{key} q0 {docid} {i} {score} bert\n"
            f.write(line)