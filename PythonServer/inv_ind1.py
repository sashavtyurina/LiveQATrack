__author__ = 'Alex'
from nltk import tokenize
import math
import operator
from CleanText import CleanText
import re


INFINITY = float('inf')
MAX_INTERVAL = 300  # max number of tokens in the interval
MIN_INTERVAL = 10
MAX_CHARACTERS = 1000

SENTENCE_START = 'sentence_start'
SENTENCE_END = 'sentence_end'

class InvertedIndex(object):
    def __init__(self, corpus):
        # No, corpus is a STRING!
        if not isinstance(corpus, str):
            raise TypeError('Corpus must be string')

        self.corpus = corpus
        # print('CORPUS: ', self.corpus)
        # self.index = {}
        # self.index_working_copy = {}

        self.corpus = self.insert_sentence_separators(self.corpus)
        self.tokens = self.tokenize(self.corpus)
        # self.index_working_copy = self.build_index(self.tokens) 
        self.lower_tokens = [t.lower() for t in self.tokens]
        self.index = self.build_index(self.lower_tokens) 

        # self.index_not_modified = self.build_index(self.tokens)

        # print('TOKENS: ', str(self.tokens)) # ok
        # print('INDEX: ', str(self.index_working_copy)) # ok

    def insert_sentence_separators(self, text):
        # text here is STRING
        new_text = 'SENTENCE_START '
        new_text += re.subn('(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', ' SENTENCE_END SENTENCE_START ', text)[0]
        new_text += ' SENTENCE_END'

        # print('SENTENCE_SEPARATED: ', new_text) # ok
        return new_text

    def get_top_covers(self, question):
        query = question.split(' ')
        # print('Now in get_top_covers')

        # with open('index.txt', 'w') as f:
        #     f.write(str(self.index))

        covers = []
        # print('Query length is :' , len(query))
        for m in range(len(query), 1, -1):
            # print('m = ', m)
            u = 0
            v = 0
            # print ('u = ', u, 'v = ', v)
            while u < INFINITY and v < INFINITY:
                (u, v), qprime = self.nextCover(query, u, m)
                # print('NEXT COVER: \n QPRIME: ', qprime, '(u, v) (', u, ', ', v, ')')
                # print('v-u = ', v - u)
                if u < INFINITY and v < INFINITY and (v - u) <= MAX_INTERVAL:  # and (v - u) >= MIN_INTERVAL:
                    coverscore = self.passageScore(query, (u, v), m)
                    # print('COVERSCORE: ', coverscore)
                    covers.append(((u, v), coverscore))

        return covers

    def nextCover(self, queryTermSet, pos, m): #where m <= |query|
        # print('Now in nextCover. Looking for %d-cover' % m)
        # find the next m-cover after position pos
        V = []
        # we first look at the smallest interval, that contains m query terms
        for q in queryTermSet:
            nextq = self.next(q, pos)
            V.append((q, nextq))

        # take m-th biggest value. We only want m query terms to appear in our snippet
        # print('V: ', V)
        v = sorted(V, key=lambda x: x[1])[m-1][1]  # index of m-th term
        V_m = sorted(V, key=lambda x: x[1])[0:m]
        # print('V_m: ', V_m)


        if not v < INFINITY:
            # print('RETURNING INF')
            return (INFINITY, INFINITY), []

        # now start to move back from v
        u = v
        qprime = []  # query terms that our m-cover contains
        # U = []
        for q, qpos in V_m:  # we go again along the entire vocabulary

            # if qpos < v and self.prev(q, v + 1) < u:
            u = min(self.prev(q, v + 1), u)
            qprime.append(q)

        # print('QPRIME: ', qprime)
        # print('PASSAGE: ', self.tokens[u:v])

        return (u, v), qprime

    def passageScore(self, qprime, interval, m):
        score = 0.0
        u, v = interval
        l = v - u + 1
        # lc = len(self.corpus)  # lc is the total length of the collection
        lc = len(self.tokens)

        #print 'm l lc', m, l, lc
        for t in qprime:
            if self.index.get(t):
                lt = len(self.index[t])  # lt is the total number of times t appears in the collection
                # print(type(lt))
                x1 = math.log(float(lc)/float(lt))
                #print t, lt, x1
                score += x1
            else:
                score += 0
        #print score, math.log(l), m * math.log(l)
        score -= len(qprime) * m*math.log(l)
        #print score
        return score

    def get_passage(self, begin, end, margin=10):
        # margin - tokens left from start and right after the end
        if end >= len(self.tokens) or begin > end:
            return None
        # b = begin - margin if (begin - margin) >= 0 else 0
        # e = end + margin if (end + margin) <= len(self.corpus) else len(self.corpus)
        b = max(0, begin - margin)
        e = min(len(self.tokens), end + margin)

        # start = b
        # finish = e
        start = self.prev(SENTENCE_START, b)
        if not start < INFINITY:
            start = b

        finish = self.next(SENTENCE_END, e)
        if not finish < INFINITY:
            finish = e

        # print(start, finish)

        # find the closest beginning of the sentence from the left
        # find the closest end of the sentence from the right
        candidate = ' '.join(self.tokens[start + 1:finish])
        candidate = candidate.replace(SENTENCE_END.upper(), '')
        candidate = candidate.replace(SENTENCE_START.upper(), '')
        if True:  # len(candidate) <= MAX_CHARACTERS:
            return candidate
        else:
            candidate = ' '.join(self.tokens[begin + 1:end])
            candidate = candidate.replace(SENTENCE_END.upper(), '')
            candidate = candidate.replace(SENTENCE_START.upper(), '')
            return candidate

    def tokenize(self, corpus):
        i = 0
        return tokenize.word_tokenize(corpus)

    # builds postings list
    def build_index(self, tokens):
        index = {}
        i = 0
        for token in tokens:
            if not index.get(token):
                index[token] = [i]
            else:
                index[token].append(i)
            i += 1
        return index

    def prev(self, token, pos):
        if not self.index.get(token):
            return INFINITY
        if pos > self.last(token):
            return self.last(token)
        if pos <= self.first(token):
            return INFINITY
        l = len(self.index[token]) - 1
        ind = self.binary_search_prev(token, 0, l, pos)
        return self.index[token][ind]

    def next(self, token, pos):
        if not self.index.get(token):
            return INFINITY
        if self.last(token) <= pos:
            return INFINITY
        if self.first(token) > pos:
            return self.first(token)

        l = len(self.index[token]) - 1
        ind = self.binary_search_next(token, 0, l, pos)
        # print('ind = %d' % ind)
        return self.index[token][ind]

    def binary_search_next(self, token, low, high, current):
        if not self.index.get(token):
            return INFINITY
        while high - low > 1:
            mid = math.floor((high+low)/2)
            if self.index[token][mid] <= current:
                low = mid
            else:
                high = mid
        return high

    def binary_search_prev(self, token, low, high, current):
        if not self.index.get(token):
            return INFINITY
        while high - low > 1:
            mid = math.floor((high+low)/2)
            if self.index[token][mid] >= current:
                high = mid
            else:
                low = mid
        return low

    def last(self, token):
        if self.index.get(token):
            return self.index[token][-1]
        return INFINITY

    def first(self, token):
        if self.index.get(token):
            return self.index[token][0]
        return INFINITY

