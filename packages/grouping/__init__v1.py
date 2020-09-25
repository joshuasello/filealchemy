from __future__ import print_function
from numpy import int64 as np_int64
import json, hashlib
import pandas as pd
from statistics import mean
import re

from sklearn.externals import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

import nltk
from nltk.stem.snowball import SnowballStemmer

# load nltk's English stopwords as variable called 'stopwords'
stemmer = SnowballStemmer("english")
stopwords = nltk.corpus.stopwords.words('english')


class KMeansClustering(object):
    def __init__(self):
        self._last_text_list_file_path = "_user_folders/_last_text_list.json"
        self.last_text_list = []
        self.centroid_main_terms = None

    def cluster_text(self, text_list, num_clusters=None, max_centroid_terms=5, verbose=False):
        vocab_df = self.get_total_vocab(text_list)

        if len(text_list) > 0:
            '''
                Define vectorizer parameters:
                max_df: the maximum frequency within the documents a given a given feature can be used.
                min_df: an amount that that insures that a term is at least above said amount to be considered.    
            '''
            tfidf_vectorizer = TfidfVectorizer(
                max_df=0.8,
                max_features=20000,
                min_df=0.2,
                stop_words='english',
                use_idf=True,
                tokenizer=self.tokenize_and_stem,
                ngram_range=(1, 3),
                dtype=np_int64
            )
            '''
                Create TF-IDF (Term Frequency-Inverse Document Frequency) Matrix 
                from supported file content
            '''
            tfidf_matrix = tfidf_vectorizer.fit_transform([text for text in text_list])
            terms = tfidf_vectorizer.get_feature_names()

            '''
                Use K Means Cluster (an unsupervised machine learning algorithm) to create groups from
                the TF-IDF matrix.

                I used the elbow method to find the optimal value for K using the Sum of Squared Errors (SSE).
                Reference: https://stackoverflow.com/questions/19197715/scikit-learn-k-means-elbow-criterion
            '''
            sse = {}

            if self.data_mutated(text_list):

                print("Content changes noticed. Performing re-clustering...")

                rand_state = 7

                if num_clusters is None:
                    for k in range(1, int(len(text_list))):
                        kmeans = KMeans(n_clusters=k, max_iter=1000, random_state=rand_state).fit(tfidf_matrix)
                        sse[k] = kmeans.inertia_  # Inertia: Sum of distances of samples to their closest cluster center

                    num_clusters = int(min(sse, key=lambda x: abs(x - mean(list(sse.values())))))
                else:
                    num_clusters = int(num_clusters)

                num_clusters = 10 if num_clusters > 10 else num_clusters
                kmeans = KMeans(n_clusters=num_clusters, max_iter=1000, n_init=20, random_state=rand_state,
                                n_jobs=-1).fit(tfidf_matrix)

                self.save_text_list(text_list)
                joblib.dump(kmeans, '_user_folders/_text_doc_cluser.pkl')
            else:
                print("Content static...")
                kmeans = joblib.load('_user_folders/_text_doc_cluser.pkl')
                num_clusters = len(kmeans.cluster_centers_)

            centroid_main_terms = []
            order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]

            for i in range(num_clusters):
                centroid_main_terms.append([
                    vocab_df.ix[terms[ind].split(' ')].values.tolist()[0][0].encode('utf-8').decode()
                    for ind in order_centroids[i, : 1]
                ])

            if verbose:
                print("Textual content has been clustered. Information on outcome below:")
                print("Calculated number of clusters (Elbow Method): " + str(num_clusters))
                print("Number of documents: " + str(len(text_list)))
                print("Top terms per cluster: ")
                for k, c in enumerate(centroid_main_terms):
                    print("Cluster %d words: " % k, end="")
                    for i in c:
                        print(' %s' % i, end=',')
                    print()
                print("-" * 20 + "END OF CLUSTER INFO" + 20 * "-")

            del num_clusters, sse, terms, tfidf_vectorizer, tfidf_matrix, text_list, order_centroids

            self.centroid_main_terms = centroid_main_terms

            return kmeans.labels_.tolist()
        else:
            raise Exception("Error. No elements found in text_list.")

    def get_total_vocab(self, text_list):
        text_list = list(text_list)
        total_vocab_stemmed = []
        total_vocab_tokenized = []

        for text in text_list:
            total_vocab_stemmed.extend(self.tokenize_and_stem(text))
            total_vocab_tokenized.extend(self.tokenize_only(text))

        return pd.DataFrame({'words': total_vocab_tokenized}, index=total_vocab_stemmed)

    def data_mutated(self, text_list):
        old_list = self.get_saved_text_list()

        if len(text_list) != len(old_list):
            return True
        for i, ref_text in enumerate(old_list):
            hasher = hashlib.new('SHA256')
            hasher.update(text_list[i].encode())

            if hasher.hexdigest() != ref_text:
                return True

        return False

    def save_text_list(self, text_list):
        for i in range(len(text_list)):
            hasher = hashlib.new('SHA256')
            hasher.update(text_list[i].encode())
            text_list[i] = hasher.hexdigest()

        f = open(self._last_text_list_file_path, "w")
        f.write(json.dumps(text_list))

    def get_saved_text_list(self):
        f = open(self._last_text_list_file_path, "r")
        return json.load(f)

    @staticmethod
    def tokenize_and_stem(text):
        filtered_tokens = []

        # tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
        tokens = [word for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]

        # filter out tokens not containing letters
        for token in tokens:
            if re.search('[a-zA-Z]', token):
                filtered_tokens.append(token)
        del tokens

        return [stemmer.stem(t) for t in filtered_tokens]

    @staticmethod
    def tokenize_only(text):
        filtered_tokens = []

        # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
        tokens = [word.lower() for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]

        # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
        for token in tokens:
            if re.search('[a-zA-Z]', token):
                filtered_tokens.append(token)
        del tokens

        return filtered_tokens


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

