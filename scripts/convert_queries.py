import getopt
import sys
import os
import re
import string
import xml.etree.ElementTree as ET

input_filename = ""
expansion_filename = ""
output_type = "combine"

exclude = set(string.punctuation)

options, remainder = getopt.getopt(sys.argv[1:], 'i:e:t:', ['inputfile=', 'expansionfile=', 'type='])

for opt, arg in options:
    if opt in ('-i', '--inputfile'):
        input_filename = arg
        if (not os.path.exists(input_filename)):
            sys.exit("Error: Inputfile does not exists")
    if opt in ('-e', '--expansionfile'):
        expansion_filename = arg
        if (not os.path.exists(expansion_filename)):
            sys.exit("Error: Expansion file does not exists")
    if opt in ('-t', '--type'):
        output_type = arg

def get_sdm_query(query,lambda_t=0.8,lambda_o=0.1,lambda_u=0.1):
    words = query.split()
    if len(words)==1:
        return f"{lambda_t} #combine( {query} )"
    terms = " ".join(words)
    ordered = "".join([" #1({}) ".format(" ".join(bigram)) for bigram in zip(words,words[1:])])
    unordered = "".join([" #uw8({}) ".format(" ".join(bigram)) for bigram in zip(words,words[1:])])
    indri_query = f"{lambda_t} #combine( {terms} ) {lambda_o} #combine({ordered}) {lambda_u} #combine({unordered})"
    return indri_query


expansion_terms = []
if (expansion_filename != ""):
    with open(expansion_filename) as expandfile:
        expansion_terms = expandfile.readlines()
   
xml_root = ET.parse(input_filename)

print("<parameters>")

order = 0
for topic in xml_root.findall('.//topic'):
    num = topic.find('num').text
    query = topic.find('query').text
    description = topic.find('description').text
    query = query.replace('-', ' ')
    query = query.replace('\n', ' ')
    description = description.replace('-', ' ')
    description = description.replace('\n', ' ')
    query = query.translate(str.maketrans('', '', string.punctuation))
    description = description.translate(str.maketrans('', '', string.punctuation))
    print("<query>")
    print("<number>" + str(num) + "</number>")

    expansion = ""
    if ( expansion_filename != ""):
        line_expansion_term = expansion_terms[order]
        line_expansion_term = line_expansion_term.replace("[", "")
        line_expansion_term = line_expansion_term.replace("]", "")
        line_expansion_term = line_expansion_term.replace('"', "")
        line_expansion_term = line_expansion_term.replace('\n',"")
        line_expansion_terms = line_expansion_term.split(',')

        expansion = " "
        max_expansion_terms = 10
        for i in range (min(max_expansion_terms, len(line_expansion_terms))):
            if (':' in line_expansion_terms[i]):
                term,score = line_expansion_terms[i].split(':')
                score = score.replace("\n", "")
                if (output_type == "weights"):
                    expansion = expansion + str(score) + " #combine(" + term + ") "
                else:
                    expansion = expansion + term
        expansion = expansion + " "

    if (output_type == "combine"):
        print("<text>#combine(" + query + " " + expansion + description + ")</text>")

    if (output_type == "weights"):
        print("<text>#weight( 1.0 #combine(" + query + ") " + expansion + " 0.5 #combine(" + description + "))</text>")

    if (output_type == "terms"):
        print("<text>" + query + " " + expansion + description + "</text>")

    if (output_type == "sdm"):
        query_sdm = get_sdm_query(query)
        description_sdm = get_sdm_query(description)
        print("<text>#weight(" + query_sdm + " " + description_sdm + ")</text>")

    print("</query>")
    
    order += 1


print("</parameters>")



