from trectools import TrecRun, TrecEval, TrecQrel, fusion
r1 = TrecRun("test_output_bb.txt_title_t5")
r2 = TrecRun("test_output_bb.txt_desc_t5")
# r3 = TrecRun("test_output.15_title_castorini")
r4 = TrecRun("test_output_bb.txt_title_desc_castorini")

r3 = TrecRun("test_output_bb.txt")

#qrels_file =  "/fs/clip-ir-podcasts/data/podcasts_2020_train.1-8.qrels"
#qrels = TrecQrel(qrels_file)

fused_run = fusion.reciprocal_rank_fusion([r1,r2,r3,r4])
fused_run.print_subset("run3_train_baseline_comb_rerank.txt", topics=fused_run.topics())
#print(TrecEval(fused_run, qrels).get_ndcg())

#fused_run = fusion.reciprocal_rank_fusion([r1,r2,r3,r4])
#print(TrecEval(fused_run, qrels).get_ndcg())

#fused_run = fusion.reciprocal_rank_fusion([r1,r2,r3,r4])
#print(TrecEval(fused_run, qrels).get_ndcg())
