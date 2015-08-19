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
        # corpus is a list
        # No, corpus is a STRING!

        self.corpus = corpus
        print('CORPUS: ', self.corpus)
        self.index = {}
        self.index_working_copy = {}

        self.corpus = self.insert_sentence_separators(self.corpus)
        self.tokens = self.tokenize(self.corpus)
        self.index_working_copy = self.build_index(self.tokens)  # we will use this index to retrieve passages

        self.stemmed = self.stem(self.tokens)
        self.stemmed = self.lower(self.stemmed)
        self.index = self.build_index(self.stemmed)

        # self.tokenize()  # split text into tokens
        # self.clean_corpus()  # populates self.stemmed
        # self.lower()  # brings all tokens to lowercase
        # self.build_index()  # build inverted index
        # print(self.tokens)
        # print(self.index)

    def lower(self, words):
        return [token.lower() for token in words]

    # def set_new_corpus(self, new_corpus):
    #     self.corpus = new_corpus
    #     self.tokenize()
    #     self.clean_corpus()  # populates self.stemmed
    #     self.build_index()

    def stem(self, words):
        cleaner = CleanText(words)
        return cleaner.stem_words()

    def insert_sentence_separators(self, text):
        # text here is STRING
        new_text = 'SENTENCE_START '
        new_text += re.subn('(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', ' SENTENCE_END SENTENCE_START ', text)[0]
        new_text += ' SENTENCE_END'

        print('SENTENCE_SEPARATED: ', new_text)
        return new_text

    def tokenize(self, text):
        return tokenize.word_tokenize(text)

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

    def get_index(self):
        return self.index

    def first(self, token):
        if self.index.get(token):
            return self.index[token][0]
        return INFINITY

    def last(self, token):
        if self.index.get(token):
            return self.index[token][-1]
        return INFINITY

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

    def nextCover(self, queryTermSet, pos, m): #where m <= |query|
        # find the next m-cover after position pos

        V = []
        # we fisrt look at the smallest interval, that contains m query terms
        for q in queryTermSet:
            nextq = self.next(q, pos)
            # print(nextq)
            # if not nextq:
            #     return (None, None), []  #((None, None), [])
            V.append((q, nextq))

        #print V, m
        # take m-th biggest value. We only want m query terms to appear in our snippet
        v = sorted(V, key=lambda x: x[1])[m-1][1]  # index of m-th term
        V_m = sorted(V, key=lambda x: x[1])[0:m]

        if not v < INFINITY:
            return (INFINITY, INFINITY), []

        # v - the biggest index
        # print(v)
        # print(V)
        # if not v:  # this should not ever happen. We check all the value in the previous step
        #     return (None, None), []

        # now start to move back from v
        u = v
        qprime = []  # query terms that our m-cover contains
        # U = []
        for q, qpos in V_m:  # we go again along the entire vocabulary

            # if qpos < v and self.prev(q, v + 1) < u:
            u = min(self.prev(q, v + 1), u)
            qprime.append(q)

        print('QPRIME: ', qprime)
        print('PASSAGE: ', self.tokens[u:v])

        # u = sorted(U, key=lambda x: x[1])[0][1]

        # print('QPRIME: ', qprime)


        return (u, v), qprime #, qprime  # , qprime

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

    # not used.
    def getTopCovers(self, query, u=0, v=-1, top=1):
        # query - a list of terms
        if v == -1:
            v = len(self.corpus)
        query_term_set = set(query)
        if len(query_term_set) == 1:
            bi = 0
        elif len(query_term_set) >= 2:
            bi = 1

        covers = []
        u = v
        # print(len(query_term_set)-1)
        for m in range(len(query_term_set)-1, bi, -1):
            i = u
            print('u = %d, v = %d, i = %d' % (u, v, i))
            while i < v and i:
                interval, qprime = self.nextCover(query_term_set, i, m)
                # print(interval, qprime)
                i = interval[0]
                if i != None:
                    coverscore = self.passageScore(qprime, interval, m)
                    covers.append((coverscore, interval, qprime))
        #print covers
        return sorted(covers, key=lambda x: x[0], reverse=True)[:top]

    def get_top_covers(self, query):
        u = 0
        v = 0
        covers = []
        for m in range(len(query), 1, -1):
            while u < INFINITY and v < INFINITY:
                (u, v), qprime = self.nextCover(query, u, m)
                # interval, qprime = self.nextCover(query, u, m)
                # u = interval[0]
                # v = interval[1]
                if u < INFINITY and v < INFINITY and (v - u) <= MAX_INTERVAL:  # and (v - u) >= MIN_INTERVAL:
                # if interval[0] != None and interval[1] != None:

                    coverscore = self.passageScore(query, (u, v), m)
                    # !!!covers.append(((u, v), coverscore))

                    
                    # print('SCORE: ', coverscore)
                    # covers.append((u, v))
            u = 0
            v = 0
        return covers

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
        # if b > 0:
        #     print('')
        # if e < len(self.corpus):
        #     print('')
        #     e = re.search('(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', self.corpus[e:])

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


def main():
    index = InvertedIndex('aaa. ss jjj ddd, dd. sssss. lllll? ddsd')
    print(index.get_passage(5, 7, 0))
    # index.insert_sentence_separators()
    # index = InvertedIndex('how much wood would a more wood woodchuck chuck, if a woodchuck could chuck wood?')
    # index = InvertedIndex(' '.join(open('dogs').readlines()))
    # covers = index.get_top_covers(['dog', 'animal', 'people'])
    # for c in covers:
    #     print(c)

    # cover = (0, 0)
    # while cover[1] != None:
    #     cover = index.nextCover(['dogs', 'animal'], cover[1], 0)
    #     print(cover)

    # print('result:')
    # print(index.getTopCovers(set(['chuck', 'would']), 2, 2))
    # print(index.getTopCovers(['chuck', 'wood', 'would']))
    # print(index.nextCover(['chuck', 'wood'], 7, 2))
    # print(index.get_top_covers(['chuck', 'wood']))

if __name__ == "__main__":
    main()
