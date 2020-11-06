import argparse
import os
import json
from bs4 import BeautifulSoup

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to process Podcasts query xml to json file')

    parser.add_argument('--input_file', type=str, required=True)
    parser.add_argument('--output_file', type=str, required=True)
    args = parser.parse_args()
    
    lines=""
    with open(args.input_file) as f:
        for line in f:
            lines+=line

    soup = BeautifulSoup(lines, features="lxml")
    qids = [num.text.strip() for num in soup.find_all("num")]
    titles = [title.text.strip() for title in soup.find_all("query")]
    descs = [desc.text.strip() for desc in soup.find_all("description")]
    query_types = [title.text.strip() for title in soup.find_all("type")]

    query_lines = []
    for qid, qtype, title, desc in zip(qids,query_types,titles,descs):
        query_dict = {}
        query_dict["qid"] = qid
        query_dict["title"] = title
        query_dict["desc"] = desc
        query_dict["type"] = qtype
        query_lines.append(json.dumps(query_dict))
    
    with open(args.output_file, "w") as f:
        for line in query_lines:
            f.write(line+"\n")