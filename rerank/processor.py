import logging
import random
import os
import json

from transformers import DataProcessor, InputExample, InputFeatures, PreTrainedTokenizer
from typing import List, Optional, Union

class PodcastProcessor(DataProcessor):

    def __init__(self, query_field):
        self.max_test_depth = 1000  # for testing, we re-rank the top 100 results
        self.max_train_depth = 1000  # for training, we use negative samples from the top 1000 documents
        self.q_fields = query_field.split('_')
        logging.info("Using query fields {}".format(' '.join(self.q_fields)))

    def get_train_examples(self, train_file, query_file, qrel_file):
        examples = []
        train_files = [train_file]

        qrel_file = open(qrel_file)
        qrels = self._read_qrel(qrel_file)
        logging.info("Qrel size: {}".format(len(qrels)))

        query_file = open(query_file)
        qid2queries = self._read_queries(query_file)
        logging.info("Loaded {} queries.".format(len(qid2queries)))

    
        train_file = open(train_file)
        for i, line in enumerate(train_file):

            items = line.strip().split('#')
            trec_line = items[0]

            qid, _, docid, r, _, _ = trec_line.strip().split(' ')

            # to train, we do not use all passages because it leads to overfitting
            # we subsample the following:
            #    first passage in a doc
            #    10% other passages in the doc
            # if int(docid.split('_')[-1].split('-')[-1]) != 0 and random.random() > 0.1:
            #     continue

            assert qid in qid2queries, "QID {} not found".format(qid)
            q_json_dict = qid2queries[qid]
            q_text_list = " ".join([q_json_dict[field] for field in self.q_fields])

            json_dict = json.loads('#'.join(items[1:]))
            d = json_dict["doc"]["body"]

            r = int(r)
            if r > self.max_train_depth:
                continue
            label = "0"
            if (qid, docid) in qrels or (qid, docid.split('_')[0]) in qrels:
                label = "1"
            guid = "train-%s-%s" % (qid, docid)
            examples.append(
                InputExample(guid=guid, text_a=q_text_list, text_b=d, label=label)
            )
        train_file.close()
        random.shuffle(examples)
        return examples

    def get_test_examples(self, test_file, query_file, qrel_file):
        examples = []
        dev_file = open(test_file)
        qrel_file = open(qrel_file)
        qrels = self._read_qrel(qrel_file)
        logging.info("Qrel size: {}".format(len(qrels)))

        query_file = open(query_file)
        qid2queries = self._read_queries(query_file)
        logging.info("Loaded {} queries.".format(len(qid2queries)))

        for i, line in enumerate(dev_file):
            items = line.strip().split('#')
            trec_line = items[0]

            qid, _, docid, r, _, _ = trec_line.strip().split(' ')
            assert qid in qid2queries, "QID {} not found".format(qid)
            q_json_dict = qid2queries[qid]
            q_text_list = " ".join([q_json_dict[field] for field in self.q_fields])

            json_dict = json.loads('#'.join(items[1:]))
            d = json_dict["doc"]["body"]

            r = int(r)
            if r > self.max_test_depth:
                continue
            label = "0"
            if (qid, docid) in qrels or (qid, docid.split('_')[0]) in qrels:
                label = "1"
            guid = "test-%s-%s" % (qid, docid)
            examples.append(
                InputExample(guid=guid, text_a=q_text_list, text_b=d, label=label)
            )
        dev_file.close()
        return examples

    def _read_qrel(self, qrel_file):
        qrels = set()
        for line in qrel_file:
            qid, _, docid, rel = line.strip().split('\t')
            rel = int(rel)
            if rel > 0:
                qrels.add((qid, docid))
        return qrels

    def _read_queries(self, query_file):
        qid2queries = {}
        for i, line in enumerate(query_file):
            json_dict = json.loads(line)
            qid = json_dict['qid']
            qid2queries[qid] = json_dict
            if i < 3:
                logging.info("Example Q: {}".format(json_dict))
        return qid2queries

    def get_labels(self):
        return ["0", "1"]

def convert_examples_to_features(
    examples: List[InputExample],
    tokenizer: PreTrainedTokenizer,
    max_length: Optional[int] = None,
    task=None,
    label_list=None,
    output_mode=None,
):
    if max_length is None:
        max_length = tokenizer.max_len    

    label_map = {label: i for i, label in enumerate(label_list)}

    def label_from_example(example: InputExample) -> Union[int, float, None]:
        if example.label is None:
            return None
        if output_mode == "classification":
            return label_map[example.label]
        elif output_mode == "regression":
            return float(example.label)
        raise KeyError(output_mode)

    labels = [label_from_example(example) for example in examples]
    batch_encoding = {}
    batch_encoding["input_ids"] = []
    batch_encoding["attention_mask"] = []
    batch_encoding["token_type_ids"] = []
    # batch_encoding = tokenizer(
    #     [(example.text_a, example.text_b) for example in examples],
    #     max_length=max_length,
    #     padding="max_length",
    #     truncation=True,
    # )
    # print(batch_encoding)
    def _encode(x, max_length, doc=False):
        input_ids = tokenizer.encode(x, add_special_tokens=False, max_length=max_length)
        padding_length = max_length - len(input_ids) - 2
        attention_mask = [1] * len(input_ids) + [0] * padding_length
        input_ids = input_ids + [103] * padding_length
        # if not doc:
        #     input_ids = [101] + input_ids + [102]
        #     attention_mask = [1] + attention_mask + [1]
        # else:
        #     input_ids = input_ids + [102]
        #     attention_mask = attention_mask + [102]
        return input_ids, attention_mask

    for example in examples:
        x,y = example.text_a, example.text_b

        ids1, mask1 = _encode(x, max_length=20)
        ids1 = [101] + ids1 + [102]
        mask1 = [1] + mask1 + [1]
        tids1 = [0] * len(ids1)


        ids2, mask2 = _encode(y, max_length=489)
        ids2 = ids2 + [102]
        mask2 = mask2 + [1]
        tids2 = [1] * len(ids2)

        input_ids = ids1 + ids2
        attention_mask = mask1 + mask2
        token_type_ids = tids1 + tids2

        batch_encoding["input_ids"].append(input_ids)
        batch_encoding["attention_mask"].append(attention_mask)
        batch_encoding["token_type_ids"].append(token_type_ids)

    features = []
    for i in range(len(examples)):
        inputs = {k: batch_encoding[k][i] for k in batch_encoding}

        feature = InputFeatures(**inputs, label=labels[i])
        features.append(feature)

    for i, example in enumerate(examples[:5]):
        logging.info("*** Example ***")
        logging.info("guid: %s" % (example.guid))
        logging.info("features: %s" % features[i])

    return features