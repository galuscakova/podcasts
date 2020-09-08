import getopt
import sys
import os
import re
import string

input_filename = ""
metadata_filename = ""

metadata = {}

options, remainder = getopt.getopt(sys.argv[1:], 'i:m:', ['inputfile=', 'metadata'])

for opt, arg in options:
    if opt in ('-i', '--inputfile'):
        input_filename = arg
        #if (not os.path.exists(input_filename)):
        #    sys.exit("Error: Inputfile does not exists")
    elif opt in ('-m', '--metadata'):
        metadata_filename = arg



with open(metadata_filename) as mf:
   line = mf.readline()
   while line:
       line = mf.readline()
       line_items = line.split("\t")
       if (len(line_items) > 8):
           podcast_id = line_items[6]
           show_name = line_items[1]
           show_description = line_items[2]
           publisher = line_items[3]
           episode_name = line_items[7]
           episode_description = line_items[8]
           full_description = show_name + " " + show_description + " " + publisher + " " + episode_name + " " + episode_description
           metadata[podcast_id] = full_description

with open(input_filename) as infile:
    line = infile.readline()
    while line:
        if "<DOCNO>" in line:
            podcastid = re.sub('<DOCNO>', '', line)
            podcastid = re.sub('</DOCNO>', '', podcastid)
            podcastid = podcastid.split("_")[0]
            #print(podcastid)
        if "</TEXT>" in line:
            if podcastid in metadata:
                podcast_metadata = metadata[podcastid]
                print(podcast_metadata)
        print(line, end ="")
        line = infile.readline()    
