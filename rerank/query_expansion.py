import os, subprocess, numpy as np, re, argparse, sys, json, string
from collections import Counter, defaultdict
from scipy import spatial
from gensim.models import KeyedVectors
import multiprocessing as mproc
from time import gmtime, strftime
from nltk.stem import PorterStemmer
from sklearn.metrics.pairwise import cosine_similarity, pairwise_distances

log_file = None

def log_print(string):
	if log_file==None:
		print(string)
	else:
		present_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
		log_file.write(present_time + "\nQueryExpansion: " + str(string) + "\n")
def set_log_file(log_f):
	global log_file
	log_file = log_f
	
def load_glove_embedding(word2vec_path):
	model = KeyedVectors.load_word2vec_format(word2vec_path, binary=False)
	return model

def mult_proc(f, inp):

    n_proc = mproc.cpu_count()-1
    if n_proc<=0: n_proc=1
    with mproc.Pool(processes=n_proc) as pool:
        out = pool.map(f,np.array_split(inp,n_proc))
    return [item for sublist in out for item in sublist]

class QueryExpansion:
    
    def __init__(self, M, N, indri_path, index_path, duplicate, min_df, scoring):
        
        self.M = M
        self.N = N
        self.indri_path = indri_path
        self.index_path = index_path
        self.scoring = scoring
        self.duplicate = duplicate
        self.min_df = min_df
        
    def term_func(self, file_list):
        
        return [self.get_all_terms(file) for file in file_list]
       
    def __repr__(self):
        return "\nQueryExpansion parameters [M="+str(self.M)+"; N="+str(self.N)+"; indri_path"+self.indri_path+\
                "; index_path"+self.index_path+"; scoring="+str(self.scoring)+\
                "; duplicated="+str(self.duplicate)+"; min_df="+str(self.min_df)+"]"

    def get_all_terms(self, file):
        """
        This function returns all the terms occuring in the list of files provided

        Args:
            indri_path: Path to the folder that contains indri
            index_path: Path to the folder that contains index built by Indri
            files: List of filenames used for extracting terms

        Returns:
            list of terms present in the input files
        """
        cmd_args = [os.path.join(self.indri_path, 'dumpindex/dumpindex'), self.index_path,
                   "di", "docno", file]
        p = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        no = p.stdout.readline().strip()

        cmd_args = [os.path.join(self.indri_path, 'dumpindex/dumpindex'), self.index_path,
                   "dv", no]
        p = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')

        return [line.strip().split()[-1] for line in p.stdout.readlines()[3:]]

    def get_unique_terms(self, term):
        """
        This function returns the unique terms that occur in the N retrieved documents

        Args:
            term: Term/phrase that needs to be queried against the NYT corpus

        Returns:
            list of all the terms and the unique terms from the N documents
        """
        term = term.replace("'","")
        cmd_args = [os.path.join(self.indri_path, 'runquery/IndriRunQuery'), '-index={}'.format(self.index_path), '-query={}'.format(term), '-count={}'.format(self.N)]


        p = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')

        temp = [line.strip().split('\t') for line in p.stdout.readlines()]
        files = [x[1] for x in temp]

        all_terms = mult_proc(self.term_func,files)
        df = sum([Counter(set(l)) for l in all_terms],Counter())
        unique_terms = list(set(item for sublist in all_terms for item in sublist))
        if("[OOV]" in unique_terms): unique_terms.remove("[OOV]")
        alnum = lambda s: any(c.isalnum() for c in s)
        unique_terms = np.array([term for term in unique_terms if not re.search(r'\d',term) 
                                 and df[term]>=min(self.min_df,max(df.values())) 
                                 and alnum(term)])
        return all_terms, unique_terms
    
    def get_tfidf_score(self, input_term, all_terms, unique_terms):
        """
        This function returns a dictionary of unique terms with the product of term frequency and inverse document frequency.

        Args:
            all_terms: list of all the terms present in the retrieved N documents
            unique_terms: list of unique terms present in the retrieved N documents
        Returns:
            dict of terms with tf-idf score
        """
        if unique_terms.size==0: 
            log_print("No terms found for the input term {}".format(input_term))
            return None

        total = 1855658.0
        tf = Counter(item for sublist in all_terms for item in sublist)

        path_to_nyt_idf = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(path_to_nyt_idf, 'nyt_idf_nonstem.json'), 'r') as fp:
            idf = json.load(fp)
        score = np.array([tf[term]*np.log(total/idf[term]) for term in unique_terms])
        tf_idf = dict(zip(unique_terms, score/max(score)))
        return tf_idf
    
    def get_w2v_sim_score(self, input_term, model):
        """
        This function returns a dictionary of unique terms with cosine similarity scores of the embeddings

        Args:
            term: Input query term/phrase
            model: Gensim word2vec object
            unique_terms: list of unique terms present in the retrieved N documents

        Returns:
            dict of terms with cosine similarity score
        """
        if all(t.lower() not in model.vocab for t in input_term.split()):
            log_print("Terms {} not present in word2vec vocabulary. Try TF-IDF scoring metric".format(input_term))
            return None
        
        temp = model.most_similar(positive=[term.lower() for term in input_term.split() 
                                                     if term.lower() in model.vocab], topn=100)
        word2vec = {word:val for word,val in temp 
                    if all(punct not in word for punct in string.punctuation) and not re.search(r'\d',word)}
        
        return word2vec

    def add_left(self, terms, dic, score, l_curr, r_count):
        
        flag = False
        ps = PorterStemmer()
        for i,term in enumerate(score[l_curr:]):
            key,val = term.split(":")
            if self.duplicate: stemmed_term = key
            else: stemmed_term = ps.stem(key)
            if stemmed_term not in terms:
                if stemmed_term not in dic:
                    dic[stemmed_term]['term'] = key
                    dic[stemmed_term]['val'] = float(val)
                    flag = True
                else:
                    if dic[stemmed_term]['val']<float(val):
                        dic[stemmed_term]['term'] = key
                        dic[stemmed_term]['val'] = float(val)
                        r_count -= 1
                    flag = True
            if(flag):
                l_curr +=(i+1)
                return dic, l_curr, r_count
                    
    def retrieve_top_M_flat_words(self, input_term, dic, **attributes):
        """
        This function returns the top M words based on the scores. It removes the terms that are either stopwords or the ones which contain numbers

        Args:
            dic: dict containing terms and their score
            M: number of terms to return

        Returns:
            list of M terms sorted in descending order of scores
        """
        if dic is None:
            log_print('Empty score dictionary.')
            return []
        
#         print(attributes)
        if "M" in attributes: M = attributes["M"]
        else: M = self.M
        deduplicate = defaultdict(dict)
        ps = PorterStemmer()
        terms = set(ps.stem(term) for term in input_term.split())
        sort = sorted(dic.items(), key=lambda item: item[1], reverse=True)

        if self.duplicate:
            return ['{}:{}'.format(key,val) for key,val in sort[:2*M] if ps.stem(key) not in terms][:M]

        for key,val in sort:
            stemmed_term = ps.stem(key)
            if stemmed_term not in terms:
                if stemmed_term not in deduplicate or deduplicate[stemmed_term]['val']<val:
                    deduplicate[stemmed_term]['term'] = key
                    deduplicate[stemmed_term]['val'] = val
            if(len(deduplicate)==M): break
        return ['{}:{}'.format(out['term'],out['val']) for term,out in deduplicate.items()]
    
    def retrieve_top_M_conjunction_words(self, left, right, **attributes):
        
        terms = attributes['terms']
        ps = PorterStemmer()
        deduplicate = defaultdict(dict)
        if not self.duplicate: terms = set(ps.stem(t) for t in terms)
        
        if not left and not right:
            log_print("Empty dictionaries. Both the terms do not exist in the corpus")
            return []
        
        elif not left or not right:
            count = self.M
            
        else: count = self.M//2
            
        l_count = 0 
        l_curr = 0
        if left:
            for i,out in enumerate(left):
                key,val = out.split(":")
                if self.duplicate: stemmed_term = key
                else: stemmed_term = ps.stem(key)

                if stemmed_term not in terms:
                    deduplicate[stemmed_term]['term'] = key
                    deduplicate[stemmed_term]['val'] = float(val)
                    l_count += 1
                if(l_count==count): break
            l_curr=i+1

        r_count = 0
        if right:
            for j,out in enumerate(right):
                key,val = out.split(":")
                if self.duplicate: stemmed_term = key
                else: stemmed_term = ps.stem(key)

                if stemmed_term not in terms:
                    if stemmed_term not in deduplicate:
                            deduplicate[stemmed_term]['term'] = key
                            deduplicate[stemmed_term]['val'] = float(val)
                            r_count += 1
                    else:
                        if deduplicate[stemmed_term]['val']<float(val):
                            deduplicate[stemmed_term]['term'] = key
                            deduplicate[stemmed_term]['val'] = float(val)
                            r_count += 1
                            deduplicate, l_curr, r_count = self.add_left(terms, deduplicate, left, l_curr, r_count)
                if(r_count==count): break
        return ['{}:{}'.format(out['term'],out['val']) for term,out in sorted(deduplicate.items(),key=lambda out:out[1]['val'],reverse=True)]
    
    def get_flat_terms(self, term, **attributes):
        
        if 'embeddings' in attributes: emb = attributes['embeddings']
        if self.scoring==1:
            all_terms, unique_terms = self.get_unique_terms(term)
            score = self.get_tfidf_score(term, all_terms, unique_terms)
        elif self.scoring==2:
            score = self.get_w2v_sim_score(term, emb)
        else: 
            log_print('Wrong option for scoring. Scoring types are: 1 for TF-IDF on retrieved NYT documents 2 for Embedding similarity on retrieved NYT documents 3 for Embedding similarity on word2vec corpus (only for terms)')
        return self.retrieve_top_M_flat_words(term, score, **attributes)
    
    def get_conjunction_terms(self, left, right, **attributes):

        attributes['terms'] = [left,right]
        attributes['M'] = 50
        left_terms = self.get_flat_terms(left, **attributes)
        right_terms = self.get_flat_terms(right, **attributes)
        
        return self.retrieve_top_M_conjunction_words(left_terms, right_terms, **attributes)
        
if __name__ == '__main__':

    # term = "Barangay Mangingisda"
    # N = 10 #cutoff for number of relevant documents
    # M = 10 #top weighted terms for the input term
    # duplicate = False
    # min_df=2
    # indri_path = '/fs/clip-sw/user-supported/indri/indri-5.12/'
    # index_path = '/fs/clip-scratch/srnair/NYT/nytimes-corpus-extractor/index_store/index_nonstem'
    # word2vec_path = '/fs/clip-scratch/srnair/.embeddings/glove/glove.6B.300d.word2vec.txt'
    # embeddings = load_glove_embedding(word2vec_path)
    
    # tfidf_qe = QueryExpansion(M, N, indri_path, index_path, duplicate, min_df, scoring=1)
    # print("tfidf_qe:\t"+str(tfidf_qe))
    # word2vec_qe = QueryExpansion(M, N, indri_path, index_path, duplicate, min_df, scoring=2)
    
    # result = tfidf_qe.get_flat_terms(term)
    # log_print(result)
    
    
    # result = word2vec_qe.get_flat_terms(term, embeddings=embeddings)
    # log_print(result)

    # left, right = "haircut", "price"
    # result = tfidf_qe.get_conjunction_terms(left, right)
    # log_print(result)

    # result = word2vec_qe.get_conjunction_terms(left, right, embeddings=embeddings)
    # log_print(result)
    from gensim.test.utils import datapath, get_tmpfile
    from gensim.models import KeyedVectors
    from gensim.scripts.glove2word2vec import glove2word2vec

    glove_file = datapath('/fs/clip-scratch/srnair/podcasts/glove.6B.300d.txt')
    tmp_file = get_tmpfile("test_word2vec.txt")

    _ = glove2word2vec(glove_file, tmp_file)

    model = KeyedVectors.load_word2vec_format(tmp_file)
    word2vec_qe = QueryExpansion(10, 10, None, None, False, 2, scoring=2)
    lines=[]
    with open("test_queries.json") as f:
        for line in f:
            terms = json.loads(line.strip())["title"]
            lines.append(json.dumps(word2vec_qe.get_flat_terms(terms, embeddings=model)))

    with open("test_exp_title_queries.json", "w") as f:
        f.write("\n".join(lines)+"\n")
