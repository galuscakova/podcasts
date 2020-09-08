import getopt
import sys
import os
import re
import string
import math

input_filename = ""
segment_shift = 300
max_segment_length = 120
postprocessing_type = "simple"
input_segment_length = 120

options, remainder = getopt.getopt(sys.argv[1:], 'i:s:t:l:', ['inputfile=', 'shift=', 'type=', 'seglen='])
for opt, arg in options:
    if opt in ('-i', '--inputfile'):
        input_filename = arg
        if (not os.path.exists(input_filename)):
            sys.exit("Error: Inputfile does not exists")
    elif opt in ('-s', '--shift'):
         segment_shift = int(arg)
    elif opt in ('-t', '--type'):
         postprocessing_type = arg
    elif opt in ('-l', '--seglen'):
         input_segment_length = arg

prev_query_id = -1
output = ""
prev_results_fulllines = []
real_order = 1
all_prev_scores = {}

with open(input_filename) as inf:

    lines = inf.readlines()

    for line in lines:
       #print(line)
       query_id, q0, filename_time, order, score, desc = line.split()
       if (float(score) < 0):
           score = math.exp(float(score))

       if (prev_query_id == -1 or (prev_query_id != query_id)):

           #print(all_prev_scores)

           if (postprocessing_type == "sumscores" or postprocessing_type == "boostscores"):
               all_prev_scores_sorted = sorted(all_prev_scores.items(), key=lambda kv: kv[1],reverse=True)
               new_order = 1
               for apss, apss_score in all_prev_scores_sorted:
                   # print(apss, apss_score)
                   nquery_id, nq0, nfilename_time, norder, nscore, ndesc = apss.split()
                   new_output = "%s %s %s %s %.5f %s" % (str(nquery_id), nq0, nfilename_time, str(new_order), float(apss_score), ndesc)
                   output = output + new_output + "\n"
                   new_order += 1

           real_order = 1
           prev_results_fulllines = []
           all_prev_scores = {}
           
       filename, time = filename_time.split("_")
       time = time.replace(".0.0", ".0")
       if (input_segment_length > max_segment_length):
           time = float(time) + (input_segment_length / 2)
       if (float(time) % 1 != 0):
           sys.exit("Time must be an integer!")
       while (float(time) % 60 != 0):
           time = time + 1

       do_not_print = 0
       for prev_results_fullline in prev_results_fulllines:
           pquery_id, pq0, pfilename_time, porder, pscore, pdesc = prev_results_fullline.split()
           pfilename, ptime = pfilename_time.split("_")
           if ((filename == pfilename) and (float(ptime) <= float(time)) and (float(ptime) + segment_shift >= float(time))):
                   do_not_print = 1
                   break
           if ((filename == pfilename) and (float(time) <= float(ptime)) and (float(ptime) - segment_shift <= float(time))):
                   do_not_print = 1
                   break

       if (do_not_print == 0 or postprocessing_type == "boostscores"):
           new_line = "%s %s %s_%s %s %.5f %s" % (str(query_id), q0, filename, str(time), str(real_order), float(score), desc)
           #print(new_line)
           if (postprocessing_type == "simple"):
               output = output + new_line
           if (postprocessing_type == "sumscores"):
               #print (str(score))
               all_prev_scores[new_line] = float(score)
           if (postprocessing_type == "boostscores"):
               all_prev_scores[new_line] = float(score)
           prev_results_fulllines.append(new_line)
           real_order = real_order + 1

       if (do_not_print == 1):
           #print("replaced by:")
           #print(prev_results_fullline)
           if (postprocessing_type == "sumscores"):
               prev_total_score = all_prev_scores[prev_results_fullline]
               all_prev_scores[prev_results_fullline] = float(prev_total_score) + float(score)
           if (postprocessing_type == "boostscores"):
               prev_total_score = all_prev_scores[prev_results_fullline]
               boost_score = (float(prev_total_score) - float(score)) / 2
               print(prev_results_fullline)
               print(prev_total_score)
               print(boost_score)
               all_prev_scores[prev_results_fullline] = float(prev_total_score) + float(boost_score)


       prev_query_id = query_id

if (postprocessing_type == "sumscores" or postprocessing_type == "boostscores"):
    all_prev_scores_sorted = sorted(all_prev_scores.items(), key=lambda kv: kv[1],reverse=True)
    new_order = 1
    for apss, apss_score in all_prev_scores_sorted:
        nquery_id, nq0, nfilename_time, norder, nscore, ndesc = apss.split(" ")
        new_output = "%s %s %s %s %.5f %s" % (str(nquery_id), nq0, nfilename_time, str(new_order), apss_score, ndesc)
        output = output + new_output + "\n"
        new_order += 1


print(output)
