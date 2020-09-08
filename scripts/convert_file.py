import json
import getopt
import sys
import os
import re

input_filename = ""
input_filelist = ""
segment_length = 120
segment_shift = 60
alternatives_processing = "1best"

actual_segment_id = 1
last_open_time = -1

options, remainder = getopt.getopt(sys.argv[1:], 'i:l:o:s:h:a:', ['inputfile=', 'inputlist=', 'outdir=', 'seglen=', 'shift=', 'alternatives='])

for opt, arg in options:
    if opt in ('-i', '--inputfile'):
        input_filename = arg
        if (not os.path.exists(input_filename)):
            sys.exit("Error: Inputfile does not exists")
    elif opt in ('-l', '--inputlist'):
        input_filelist = arg
        if (not os.path.exists(input_filelist)):
            sys.exit("Error: Inputfile does not exists")
    elif opt in ('-o', '--outdir'):
        outdir = arg
    elif opt in ('-s', '--seglen'):
        segment_length = float(arg)
    elif opt in ('-s', '--shift'):
        segment_shift = float(arg)
    elif opt in ('-a', '--alternatives'):
        alternatives_processing = arg

if (input_filename != "" and input_filelist != ""):
    sys.exit("Error: Input file and list cannot be defined at the same time")

if (input_filename == "" and input_filelist == ""):
    sys.exit("Error: Either input file or list need to be defined")

#if not os.path.exists(outdir):
#    os.makedirs(outdir)
#    print("Output dir was created")
#else:
#    sys.exit("Error: Outdir already exists")

segments = {}
segments_start_points = {}
open_segments = []

def add_word_to_segments(word, time):

    global actual_segment_id
    global last_open_time
    global open_segments

    #print (word, str(time), actual_segment_id)
   
    #print (str(last_open_time + segment_shift), str(time))

    while ((float(last_open_time + segment_shift) < float(time)) or (last_open_time == -1)):
        #print("hi")
        if (last_open_time == -1):
            last_open_time = 0
            segments_start_points[actual_segment_id] = last_open_time
        else:
             last_open_time = last_open_time + segment_shift
             segments_start_points[actual_segment_id] = last_open_time          
        
        open_segments.append(actual_segment_id)
        actual_segment_id = actual_segment_id + 1
        #print(str(last_open_time), str(segment_shift), str(time)) 

    for open_segment in open_segments:
        #print(open_segment)
        open_segment_start_time = segments_start_points[open_segment]
        if (open_segment_start_time + segment_length < float(time)):
            #print (str(open_segment_start_time + segment_length))
            open_segments.remove(open_segment)
            #print("removed")
        else: 
            if open_segment in segments:
                segments[open_segment] = segments[open_segment] + " " + word
            else:
                segments[open_segment] = word


def process_file (local_input_filename):
    full_filename = local_input_filename
    filename = os.path.basename(full_filename)
    filename = re.sub('\.json$', '', filename)

    global segments
    global segments_start_points
    global open_segments
    global last_open_time

    segments = {}
    segments_start_points = {}
    open_segments = []
    last_open_time = -1

    with open(local_input_filename) as json_file:
        data = json.load(json_file)
        if (alternatives_processing == "1best"):
            for sentence in (data['results']):
                #print(sentence)
                if 'confidence' in sentence['alternatives'][0]:
                    confidence = sentence['alternatives'][0]['confidence']
                    for w in sentence['alternatives'][0]['words']:
                       word = w['word']
                       time = w['startTime']
                       time = time.replace("s", "")
                       add_word_to_segments(word, time)
        else:
            for sentence in (data['results']):
                #print(sentence)
                if 'confidence' in sentence['alternatives'][0]:
                    confidence = sentence['alternatives'][0]['confidence']
                if 'words' in sentence['alternatives'][0]:
                    for w in sentence['alternatives'][0]['words']:
                       word = w['word']
                       time = w['startTime']
                       time = time.replace("s", "")
                       add_word_to_segments(word, time)

    for segment in segments.keys():
        if (segments[segment] != ""):
            print ("<DOC>")
            print ("<PATH>" + local_input_filename + "</PATH>")
            print ("<DOCID>" + filename + "</DOCID>")
            print ("<DOCNO>spotify:episode:" + filename + "_" + str(segments_start_points[segment]) + ".0</DOCNO>")
            print ("<CONF>" + str(confidence) + "</CONF>")
            print ("<START>" + str(segments_start_points[segment]) + "</START>")
            print ("<END>" + str(segments_start_points[segment] + segment_length) + "</END>")
            print ("<TEXT>\n" + segments[segment] + "\n</TEXT>")
            print ("</DOC>")


if (input_filename != ""):
    process_file(input_filename)


if (input_filelist != ""):
    #print ("here")
    #print(input_filelist)
    with open(input_filelist, "r") as listfile:
        for filename in listfile:
            #print(filename)
            process_file(filename.strip())




