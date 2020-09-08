import getopt
import sys
import os
import re
import string

input_filename = ""

options, remainder = getopt.getopt(sys.argv[1:], 'i:', ['inputfile='])

for opt, arg in options:
    if opt in ('-i', '--inputfile'):
        input_filename = arg


def get_sdm_query(query,lambda_t=0.8,lambda_o=0.1,lambda_u=0.1):
        words = query.split()
        if len(words)==1:
            return f"#combine( {query} )"
        terms = " ".join(words)
        ordered = "".join([" #1({}) ".format(" ".join(bigram)) for bigram in zip(words,words[1:])])
        unordered = "".join([" #uw8({}) ".format(" ".join(bigram)) for bigram in zip(words,words[1:])])
        indri_query = f"#weight({lambda_t} #combine( {terms} ) {lambda_o} #combine({ordered}) {lambda_u} #combine({unordered}))"
        return indri_query


if __name__ == "__main__":
    with open(input_filename) as infile:
        line = infile.readline()
        while line:
            if "<text>" in line:
                query = line.replace("<text>", "")
                query = query.replace("</text>", "")
                query = query.replace("#combine(", "")
                query = query.replace(")", "")
                query = get_sdm_query(query)
                line = "<text>" + query + "</text>\n"
            print(line, end ="")
            line = infile.readline()
