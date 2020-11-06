import argparse
import os
import json
from bs4 import BeautifulSoup
from tqdm import tqdm

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to process podcasts trascripts to json file')

    parser.add_argument('--input_file', type=str, required=True)
    parser.add_argument('--output_file', type=str, required=True)
    parser.add_argument('--doc_file', type=str)
    parser.add_argument('--meta_file', type=str)
    args = parser.parse_args()

    if args.doc_file:
        out_docs = set()
        with open(args.doc_file) as f:
            for line in f:
                line = line.strip()
                out_docs.add(line)
    
    meta_dict = {}
    with open(args.meta_file) as f:
        flag = False
        for line in f:
            if not flag:
                flag = True
                continue
            temp = line.strip().split("\t")
            meta_dict[temp[6]] = temp[8]

    doc_lines=[]
    flag = False
    temp = []
    with open(args.input_file) as f:
        for line in tqdm(f):
            line = line.strip()
            if args.doc_file and "<DOCNO>" in line:
                docno = line.replace("<DOCNO>","").replace("</DOCNO>","")
                if docno not in out_docs:
                    flag = False
                    temp = []
                    continue
            if flag and "</DOC>" in line:
                flag = False
                soup = BeautifulSoup("\n".join(temp), features="lxml")
                docno = soup.find("docno").text.strip()
                body = soup.find("text").text.strip()
                doc_dict = {}
                doc_dict["docno"] = docno
                # body, title = text.split("\n")
                # doc_dict["title"] = title
                doc_dict["body"] = body
                doc_dict["title"] = meta_dict[docno.split("_")[0]]
                doc_lines.append(json.dumps(doc_dict))
                temp = []
            elif "<DOC>" in line:
                flag = True
                temp = [line]
            elif flag:
                temp.append(line)

    with open(args.output_file, "w") as f:
        for line in doc_lines:
            f.write(line+"\n")
