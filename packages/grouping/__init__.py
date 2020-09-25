from __future__ import print_function

import json, hashlib, re, pandas as pd, nltk, statistics as stat, numpy as np, math
from random import randint

from sklearn.externals import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans


# load nltk's English stopwords as variable called 'stopwords'
stemmer = nltk.stem.snowball.SnowballStemmer("english")
stopwords = nltk.corpus.stopwords.words('english')


def tokenize_and_stem(text):
    filtered_tokens = []

    # tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    tokens = [word for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]

    # filter out tokens not containing letters
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)

    return [stemmer.stem(t) for t in filtered_tokens]


def tokenize_only(text):
    filtered_tokens = []

    # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    tokens = [word.lower() for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]

    # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)

    return filtered_tokens


class DocumentCluster(object):
    def __init__(self, gsd_list, local_grp_no=None, global_grp_no=None):
        # GSD: Group Supported Document(s)
        if type(gsd_list) is list:
            self.gsd = gsd_list
        else:
            raise TypeError

        self.gsd_text_list = self.text_list()

        self.random_state = 3

        self.model = None
        self.num_clusters = None

        self.df_vocab = self.get_vocab()
        self.tfidf_terms = None

        self.local_grp_no = local_grp_no
        self.global_grp_no = global_grp_no

    def tfidf(self, max_df=0.8, min_df=0.2, stop_words="english", ngram_range=(1, 3), max_features=20000):
        if len(self.gsd_text_list) > 0 and type(self.gsd_text_list) is list:
            '''
                Define vectorizer parameters:
                max_df: the maximum frequency within the documents a given a given feature can be used.
                min_df: an amount that that insures that a term is at least above said amount to be considered.    
            '''
            tfidf_vectorizer = TfidfVectorizer(
                max_df=max_df,
                max_features=max_features,
                min_df=min_df,
                stop_words=stop_words,
                use_idf=False,
                tokenizer=tokenize_and_stem,
                ngram_range=ngram_range,
                dtype=np.int64
            )
            '''
                Create TF-IDF (Term Frequency-Inverse Document Frequency) Matrix 
                from corpus and return it along with the temrs
            '''
            matrix = tfidf_vectorizer.fit_transform(self.gsd_text_list)
            terms = tfidf_vectorizer.get_feature_names()

            return terms, matrix
        else:
            print(self.gsd_text_list)
            raise Exception

    def get_k(self, tfidf_matrix):
        sse = {}

        # limit number of clusters to 10
        iterations = len(self.gsd_text_list) if len(self.gsd_text_list) < 15 else 15

        for k in range(1, iterations):
            kmeans = KMeans(n_clusters=k, max_iter=2000, n_init=20, random_state=self.random_state).fit(tfidf_matrix)
            sse[k] = kmeans.inertia_  # Inertia: Sum of distances of samples to their closest cluster center

        if self.local_grp_no is not None:
            num_clusters = self.local_grp_no
        elif self.global_grp_no is not None:
            num_clusters = self.global_grp_no
        else:
            num_clusters = int(min(sse.keys(), key=lambda x: abs(x - stat.median(list(sse.values())))))-1
        return num_clusters

    def cluster_list(self):
        tfidf_terms, matrix = self.tfidf()
        self.tfidf_terms = tfidf_terms
        k = self.get_k(matrix)
        self.num_clusters = k
        kmeans = KMeans(n_clusters=k, max_iter=5000, n_init=20, random_state=self.random_state, n_jobs=-1)
        kmeans.fit(matrix)
        self.model = kmeans
        print("Random state: "+str(self.random_state))

        return kmeans.labels_.tolist(), [item["location"] for item in self.gsd]

    def get_vocab(self):
        total_vocab_stemmed = []
        total_vocab_tokenized = []

        for text in self.gsd_text_list:
            total_vocab_stemmed.extend(tokenize_and_stem(text))
            total_vocab_tokenized.extend(tokenize_only(text))

        return pd.DataFrame({'words': total_vocab_tokenized}, index=total_vocab_stemmed)

    def terms(self, n):
        main_terms = []
        vocab = self.df_vocab
        order_centroids = self.model.cluster_centers_.argsort()[:, ::-1]

        for i in range(self.num_clusters):
            main_terms.append([
                vocab.ix[self.tfidf_terms[ind].split(' ')].values.tolist()[0][0].encode('utf-8').decode()
                for ind in order_centroids[i, : n]
            ])

        return main_terms

    def text_list(self):
        text_list = []

        for item in self.gsd:
            if "text" in item:
                text_list.append(item["text"])
            else:
                raise Exception("Imposter file item found: "+item["name"])

        return text_list

    @staticmethod
    def process_raw(corpus):
        processed_list = []

        for raw_text in corpus:
            raw_text = re.sub(' +', ' ', raw_text.replace("\n", "")).strip(" ").lower()
            processed = ""

            for word in raw_text.split(" "):
                word = str(word).strip()

                if len(word) > 2 and word not in ('b', 'j', 'c', 'ii', 'w'):
                    processed += " " + word

            processed = processed.strip(" ").replace("'s", "")
            processed_list.append(processed)

        return processed_list


class ImageCluster(object):
    def __init__(self, gsi_list, local_grp_no=None, global_grp_no=None):
        # GSD: Group Supported Image(s)
        if type(gsi_list) is list:
            self.gsi = gsi_list
        else:
            raise TypeError

        self.gsi_vector_list = self.vector_list()

        self.random_state = 5

        self.model = None
        self.num_clusters = None

        self.local_grp_no = local_grp_no
        self.global_grp_no = global_grp_no

    def cluster_list(self):
        self.snip_vectors()
        print(self.gsi_vector_list)
        print(len(self.gsi_vector_list))
        print([len(v) for v in self.gsi_vector_list])
        print(len(self.gsi_vector_list[0]))
        print(len(self.gsi_vector_list[1]))
        kmeans = KMeans(n_clusters=3, max_iter=5000, n_init=40, random_state=self.random_state, n_jobs=-1)

        X = np.array(self.gsi_vector_list)
        #print(X)
        #k = self.get_k(X)
        #print("K: "+str(k))
        #self.num_clusters = k
        kmeans.fit(X)
        self.model = kmeans
        print(kmeans.labels_.tolist())
        return kmeans.labels_.tolist(), [item["location"] for item in self.gsi]

    def get_k(self, X):
        sse = {}

        # limit number of clusters to 10
        iterations = np.size(self.gsi_vector_list) if np.size(self.gsi_vector_list) < 15 else 15

        for k in range(1, iterations):
            kmeans = KMeans(n_clusters=k, max_iter=5000, n_init=20, random_state=self.random_state).fit(X)
            sse[k] = kmeans.inertia_  # Inertia: Sum of distances of samples to their closest cluster center

        if self.local_grp_no is not None:
            num_clusters = self.local_grp_no
        elif self.global_grp_no is not None:
            num_clusters = self.global_grp_no
        else:
            num_clusters = int(min(sse.keys(), key=lambda x: abs(x - stat.median(list(sse.values())))))
        return num_clusters

    def snip_vectors(self):
        min_vect_len = 0

        for vect in self.gsi_vector_list:
            if min_vect_len < len(vect):
                min_vect_len = len(vect)

        min_vect_len = 27307
        print(min_vect_len)

        for i in range(len(self.gsi_vector_list)):
            vect_len = len(self.gsi_vector_list[i])
            start = int(math.floor((vect_len - min_vect_len)/2))
            end = vect_len - start
            self.gsi_vector_list[i] = self.gsi_vector_list[i][start:end]
            if len(self.gsi_vector_list[i]) > min_vect_len:
                self.gsi_vector_list[i].pop()

    def vector_list(self):
        vector_list = []

        for item in self.gsi:
            if "sparse_array" in item:
                vector_list.append(item["sparse_array"])
            else:
                raise Exception("Imposter file item found: " + item["name"])

        return vector_list


class Groups(object):
    def __init__(self, cluster_result):
        self.cluster_result = cluster_result

    def train_on_groups(self):
        pass

    def add_corpus(self, corpus_id, data):
        pass

    def assoc_group_label(self, grp_num):
        pass

    def do_rearrange(self, file_name, grp_num):
        pass

    def evaluate_performance(self, score):
        pass

