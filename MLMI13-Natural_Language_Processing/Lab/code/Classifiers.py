import os
from subprocess import call
from nltk.util import ngrams
from Analysis import Evaluation
import numpy as np
from sklearn import svm
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

class NaiveBayesText(Evaluation):
    def __init__(self,smoothing,bigrams,trigrams,discard_closed_class,kappa=1):
        """
        initialisation of NaiveBayesText classifier.

        @param smoothing: use smoothing?
        @type smoothing: booleanp

        @param bigrams: add bigrams?
        @type bigrams: boolean

        @param trigrams: add trigrams?
        @type trigrams: boolean

        @param discard_closed_class: restrict unigrams to nouns, adjectives, adverbs and verbs?
        @type discard_closed_class: boolean
        """
        # set of features for classifier
        self.vocabulary=set()
        # prior probability
        self.prior={}
        # conditional probablility
        self.condProb={}
        # use smoothing?
        self.smoothing=smoothing
        # add bigrams?
        self.bigrams=bigrams
        # add trigrams?
        self.trigrams=trigrams
        # restrict unigrams to nouns, adjectives, adverbs and verbs?
        self.discard_closed_class=discard_closed_class
        # kappa value if laplace smoothing is used
        self.kappa = kappa
        # stored predictions from test instances
        self.predictions=[]

    def extractVocabulary(self,reviews):
        """
        extract features from training data and store in self.vocabulary.

        @param reviews: movie reviews
        @type reviews: list of (string, list) tuples corresponding to (label, content)
        """
        for sentiment,review in reviews:
            for token in self.extractReviewTokens(review):
                self.vocabulary.add(token)

    def extractReviewTokens(self,review):
        """
        extract tokens from reviews.

        @param reviews: movie reviews
        @type reviews: list of (string, list) tuples corresponding to (label, content)

        @return: list of strings
        """
        text=[]
        for token in review:
            # check if pos tags are included in review e.g. ("bad","JJ")
            if len(token)==2 and self.discard_closed_class:
                if token[1][0:2] in ["NN","JJ","RB","VB"]: text.append(token)
            else:
                text.append(token)
        if self.bigrams:
            for bigram in ngrams(review,2): text.append(bigram)
        if self.trigrams:
            for trigram in ngrams(review,3): text.append(trigram)
        return text

    def create_vocab_dict(self):
        vocab_to_id = {}
        for word in self.vocabulary:
            #vocab_to_id[word] = len(vocab_to_id)
            vocab_to_id[word] = 0
        return vocab_to_id

    def train(self,reviews):
        """
        train NaiveBayesText classifier.

        1. reset self.vocabulary, self.prior and self.condProb
        2. extract vocabulary (i.e. get features for training)
        3. get prior and conditional probability for each label ("POS","NEG") and store in self.prior and self.condProb
           note: to get conditional concatenate all text from reviews in each class and calculate token frequencies
                 to speed this up simply do one run of the movie reviews and count token frequencies if the token is in the vocabulary,
                 then iterate the vocabulary and calculate conditional probability (i.e. don't read the movie reviews in their entirety
                 each time you need to calculate a probability for each token in the vocabulary)

        @param reviews: movie reviews
        @type reviews: list of (string, list) tuples corresponding to (label, content)
        """
        # TODO Q1
        # resetting self.vocabulary
        self.vocabulary = set()
        self.extractVocabulary(reviews)

        # resetting self.prior
        self.prior = {}
        total_pos_reviews = 0
        total_neg_reviews = 0
        # resetting self.condProb
        self.condProb = {}
        self.condProb["POS"] = self.create_vocab_dict()
        self.condProb["NEG"] = self.create_vocab_dict()

        for sentiment,review in reviews:
            if sentiment == "POS":
                # calculating total number of positive reviews
                total_pos_reviews += 1
            else:
                # calculating total number of negative reviews
                total_neg_reviews += 1

            if self.bigrams:
                review_bigrams = list(ngrams(review, 2))
                for bigram in review_bigrams:
                    if bigram in self.vocabulary:
                        if sentiment == "POS":
                            self.condProb["POS"][bigram] += 1
                        else:
                            self.condProb["NEG"][bigram] += 1
            
            elif self.trigrams:
                review_trigrams = ngrams(review, 3)
                for trigram in review_trigrams:
                    if trigram in self.vocabulary:
                        if sentiment == "POS":
                            self.condProb["POS"][trigram] += 1
                        else:
                            self.condProb["NEG"][trigram] += 1
            
            # calculating appearences for each token (word + tag)
            for token in review:
                if token in self.vocabulary:
                    if sentiment == "POS":
                        self.condProb["POS"][token] += 1
                    else:
                        self.condProb["NEG"][token] += 1

        # TODO Q2 (use switch for smoothing from self.smoothing)
        # Laplace smoothing if specified
        if self.smoothing:
            for token in self.vocabulary:
                self.condProb["POS"][token] += self.kappa # usually = 1
                self.condProb["NEG"][token] += self.kappa # usually = 1

        # calculating priors
        self.prior["POS"] = np.log(total_pos_reviews/len(reviews))
        self.prior["NEG"] = np.log(total_neg_reviews/len(reviews))

        # calculating conditional probabilities by calculating frequencies per class
        total_words_in_pos = sum(self.condProb["POS"].values())
        total_words_in_neg = sum(self.condProb["NEG"].values())
        for token in self.vocabulary:
            if self.condProb["POS"][token] > 0:
                self.condProb["POS"][token] = np.log(self.condProb["POS"][token]/total_words_in_pos)
            if self.condProb["NEG"][token] > 0:
                self.condProb["NEG"][token] = np.log(self.condProb["NEG"][token]/total_words_in_neg)


    def test(self,reviews):
        """
        test NaiveBayesText classifier and store predictions in self.predictions.
        self.predictions should contain a "+" if prediction was correct and "-" otherwise.

        @param reviews: movie reviews
        @type reviews: list of (string, list) tuples corresponding to (label, content)
        """
        # TODO Q1
        for sentiment,review in reviews:
            arg_pos = self.prior["POS"]
            arg_neg = self.prior["NEG"]

            for token in review:
                if token in self.vocabulary:
                    arg_pos += self.condProb["POS"][token]
                    arg_neg += self.condProb["NEG"][token]
            
            if self.bigrams:
                review_bigrams = list(ngrams(review, 2))
                for bigram in review_bigrams:
                    if bigram in self.vocabulary:
                        arg_pos += self.condProb["POS"][bigram]
                        arg_neg += self.condProb["NEG"][bigram]

            if self.trigrams:
                review_trigrams = ngrams(review, 3)
                for trigram in review_trigrams:
                    if trigram in self.vocabulary:
                        arg_pos += self.condProb["POS"][trigram]
                        arg_neg += self.condProb["NEG"][trigram]

            if arg_pos > arg_neg and sentiment == "POS":
                self.predictions.append("+")
            elif arg_pos < arg_neg and sentiment == "NEG":
                self.predictions.append("+")
            elif arg_pos == arg_neg:
                # If posterior is equal for both classes, then we choose the class with highest prior
                if self.prior["POS"] > self.prior["NEG"] and sentiment == "POS":
                    self.predictions.append("+")
                elif self.prior["POS"] < self.prior["NEG"] and sentiment == "NEG":
                    self.predictions.append("+")
                else:
                    self.predictions.append("-")
            else:
                self.predictions.append("-")


class SVMText(Evaluation):
    def __init__(self,bigrams,trigrams,discard_closed_class):
        """
        initialisation of SVMText object

        @param bigrams: add bigrams?
        @type bigrams: boolean

        @param trigrams: add trigrams?
        @type trigrams: boolean

        @param svmlight_dir: location of smvlight binaries
        @type svmlight_dir: string

        @param svmlight_dir: location of smvlight binaries
        @type svmlight_dir: string

        @param discard_closed_class: restrict unigrams to nouns, adjectives, adverbs and verbs?
        @type discard_closed_class: boolean
        """
        self.svm_classifier = svm.SVC()
        self.predictions=[]
        self.vocabulary=set()
        # add in bigrams?
        self.bigrams=bigrams
        # add in trigrams?
        self.trigrams=trigrams
        # restrict to nouns, adjectives, adverbs and verbs?
        self.discard_closed_class=discard_closed_class


    def extractVocabulary(self,reviews):
        self.vocabulary = set()
        for sentiment, review in reviews:
            for token in self.extractReviewTokens(review):
                if type(token) is tuple:
                    self.vocabulary.add("_".join(token))
                else:
                    self.vocabulary.add(token)

    def extractReviewTokens(self,review):
        """
        extract tokens from reviews.

        @param reviews: movie reviews
        @type reviews: list of (string, list) tuples corresponding to (label, content)

        @return: list of strings
        """
        text=[]
        for term in review:
            # check if pos tags are included in review e.g. ("bad","JJ")
            if len(term)==2 and self.discard_closed_class:
                if term[1][0:2] in ["NN","JJ","RB","VB"]: text.append(term)
            else:
                text.append(term)
        if self.bigrams:
            for bigram in ngrams(review,2): text.append(bigram)
        if self.trigrams:
            for trigram in ngrams(review,3): text.append(trigram)
        return text


    def _buildFeatures(self, reviews, mode='train'):
        all_reviews = []
        for sentiment, review in reviews:
            # storing sentiment a.k.a. label
            if mode == 'train':
                self.labels.append(sentiment)
            else:
                self.true_labels.append(sentiment)

            # joining words to feed it to scikit-learn
            if type(review[0]) is tuple:
                joined_word_tag_list = ["_".join(word_tag_tuple) for word_tag_tuple in review]
                joined_word_tag_list = [elem for elem in joined_word_tag_list if elem in self.vocabulary]
                all_reviews.append(" ".join(joined_word_tag_list))
            else:
                filtered_word_list = [word for word in review if word in self.vocabulary]
                all_reviews.append(" ".join(filtered_word_list))

        if mode == 'train':
            self.vectorizer = CountVectorizer()
            self.tf_transformer = TfidfTransformer()
            # counting occurrences
            x_counts = self.vectorizer.fit_transform(all_reviews)
            # from occurrences to frequences
            x_tf = self.tf_transformer.fit_transform(x_counts)
            self.input_features = x_tf
        else:
            # counting occurrences
            x_counts = self.vectorizer.transform(all_reviews)
            # from occurrences to frequences
            x_tf = self.tf_transformer.transform(x_counts)
            self.test_features = x_tf


    def getFeatures(self,reviews):
        """
        determine features and labels from training reviews.

        1. extract vocabulary (i.e. get features for training)
        2. extract features for each review as well as saving the sentiment
        3. append each feature to self.input_features and each label to self.labels
        
        @param reviews: movie reviews
        @type reviews: list of (string, list) tuples corresponding to (label, content)
        """

        self.input_features = []
        self.labels = []

        # TODO Q6.0
        self.extractVocabulary(reviews)
        self._buildFeatures(reviews, mode='train')



    def train(self,reviews):
        """
        train svm. This uses the sklearn SVM module, and further details can be found using
        the sci-kit docs. You can try changing the SVM parameters. 

        @param reviews: training data
        @type reviews: list of (string, list) tuples corresponding to (label, content)
        """
        # function to determine features in training set.
        self.getFeatures(reviews)

        # reset SVM classifier and train SVM model
        self.svm_classifier = svm.SVC()
        self.svm_classifier.fit(self.input_features, self.labels)


    def test(self,reviews):
        """
        test svm

        @param reviews: test data
        @type reviews: list of (string, list) tuples corresponding to (label, content)
        """

        # TODO Q6.1
        self.true_labels = []
        self.test_features = []

        self._buildFeatures(reviews, mode='test')
        self.pred_labels = self.svm_classifier.predict(self.test_features)

        n_labels = len(self.true_labels)
        for i in range(n_labels):
            if self.pred_labels[i] == self.true_labels[i]:
                self.predictions.append("+")
            else:
                self.predictions.append("-")
        
