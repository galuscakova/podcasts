from trectools import TrecRun, TrecEval, TrecQrel, fusion

r1 = TrecRun("/storage/proj/petra/projects/podcasts/experiments/experiment5/test_output.5")
r2 = TrecRun("/storage/proj/petra/projects/podcasts/experiments/experiment5/test_output.6")

# Easy way to create new baselines by fusing existing runs:
#fused_run = fusion.reciprocal_rank_fusion([r1,r2])
fused_run = fusion.combos([r1,r2], strategy="mnz")
print(fused_run)

qrels_file =  "/storage/proj/petra/projects/podcasts/podcasts_2020_train.1-8.qrels"
qrels = TrecQrel(qrels_file)

r1_p10 = TrecEval(r1, qrels).get_precision(depth=10)          # P@25: 0.3392
r2_p10 = TrecEval(r2, qrels).get_precision(depth=10)          # P@25: 0.2872
fused_run_p10 = TrecEval(fused_run, qrels).get_precision(depth=10)   # P@25: 0.3436

r1_map = TrecEval(r1, qrels).get_map()          # P@25: 0.3392
r2_map = TrecEval(r2, qrels).get_map()          # P@25: 0.2872
fused_run_map = TrecEval(fused_run, qrels).get_map()

r1_ndcg = TrecEval(r1, qrels).get_ndcg()          # P@25: 0.3392
r2_ndcg = TrecEval(r2, qrels).get_ndcg()          # P@25: 0.2872
fused_run_ndcg = TrecEval(fused_run, qrels).get_ndcg()  

print("NDCG -- Run 1: %.3f, Run 2: %.3f, Fusion Run: %.3f" % (r1_ndcg, r2_ndcg, fused_run_ndcg))
print("MAP -- Run 1: %.3f, Run 2: %.3f, Fusion Run: %.3f" % (r1_map, r2_map, fused_run_map))
print("P@10 -- Run 1: %.3f, Run 2: %.3f, Fusion Run: %.3f" % (r1_p10, r2_p10, fused_run_p10))

#fused_run.print_subset("/storage/proj/petra/projects/podcasts/experiments/experiment5/test.output.9", topics=fused_run.topics())
fused_run.print_subset("/storage/proj/petra/projects/podcasts/experiments/experiment5/test.output.10", topics=fused_run.topics())

