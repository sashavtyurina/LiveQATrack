__author__ = 'Alex'

from twisted.internet.protocol import Protocol  # is instantiated per connection
from twisted.internet.protocol import Factory  # saves persistent configuration
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver

import sys
from nltk import tokenize
import math
import operator
import re
import time, threading
import bing
from ParseHTML import HTMLStripper
import requests
# from inv_index import InvertedIndex
from inv_ind1 import InvertedIndex
import json

# dictionary contains our bg model - words and their counts.
# TODO: change the filename to valid.

DICTIONARY_FILENAME = 'dict.txt'
QUERY_LENGTH = 4
NO_ANSWER = 'no answer'
ACCOUNT_KEY = '/Mf56CFpuSUUQKdutUsoquPduXPWJBjflVKxHC3GQAk'
TOP_DOC = 5 # how many documents we want to retrieve from Bing
SHORT_QUESTIONS_THRESHOLD = 120



# this script is the foundation on our WebQA system.
# it receives a question and replies back with an answer


# 1. let's change the names of the classes to make them more inline with our project - ok
# 2. load the dictionary in memory.

class CrystalBall:
    def __init__(self, q_protocol, data):
        self.protocol = q_protocol

        # data is a json object with qid, title, body, category
        json_obj = json.loads(data)
        self.qid = json_obj['qid']
        self.title = json_obj['title']
        self.body = json_obj['body']
        self.category = json_obj['category']


    def give_me_the_answer(self):
        # we separate questions into short and long
        # for short questions the usual passage scoring approach seems to be good
        # long questions are work in progress
        if len(self.title + self.body) < SHORT_QUESTIONS_THRESHOLD:
            query = self.make_query(self.title + ' ' + self.body)
            answer = self.ask_bing(' '.join(query))
            return answer
        else:
            print('Not processing long questions at this time')
            title_query = self.make_query(self.title)
            body_query = self.make_query(self.body)
            print('TITLE QUERY: ', title_query)
            print('BODY QUERY: ', body_query)
            return NO_ANSWER

    # # main method that will return back an answer
    # def ask_question(self):
    #     # question = title + ' ' + body
    #     query = self.make_query(question) 
    #     return query

    def preprocess_question(self):  # , question):
        return ''
        # remove links from initial question
        # return re.subn('(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?', '', question)[0]

    def ask_bing(self, question):
        # question is string!
        def fetchDocumentByURL(url):
            req = requests.get(url)
            return req.text
        bing_api = bing.Api(ACCOUNT_KEY)
        print('QUERY: ', question)
        json_results = bing_api.query(question, source_type='Web', top=TOP_DOC)

        text_docs = []
        stripper = HTMLStripper()  # removes HTML tags from the document
        i = 0
        covers = []
        times = []
        passages = []
        for result in json_results:
            print('SNIPPET: ', result['Description'])
            try:
                start_time = time.clock()
                # print('fetching document...')
                # temp_url = 'https://lib.unb.ca/winslow/franklin.html'

                url = result['Url']
                # TODO: add qid into consideration. If qid mathes than skip
                if 'answers.yahoo.com' in url:
                    continue
                # TODO: proper detection of file extension. Allow only html/shtml/etc
                if url.endswith('.pdf') or url.endswith('.doc'):
                    continue

                # print(url)
                html_doc = fetchDocumentByURL(url)
                # print(result['Url'])
            except:
                print('error')
                continue

                # TODO: remove. This is just for debugging. 
            
            # with open('HTML_cleaning.txt', 'a') as f:
            #     f.write(url)
            #     f.write('\n')

            # print('Removing HTML tags...')
            stripper.feed(html_doc)
            text_document = stripper.getDataAsString()
            # text_document = cleaner.stem_words(text_document)
            # print('Building index...')
            index = InvertedIndex(text_document)
            # index.clean_corpus()

            # print('Getting covers...')
            # print ('Question is: ', question)
            covers = index.get_top_covers(question)

            # print('COVERS: ', str(covers))
            for c in covers:
                # print('COVER: ', c)
                passage = (index.get_passage(c[0][0], c[0][1]+1), c[1], url)
                # print('PASSAGE: ', passage)
                passages.append(passage)

            stripper.clearData()
            end_time = time.clock()
            times.append(end_time - start_time)

        # # print('Sorting covers...')
        passages_sorted = sorted(passages, key=lambda x: x[1], reverse=True)
        print('How many passages we have? ', len(passages_sorted))
        # i = 1
        # for c in passages_sorted:
        #     if c[0] != '':
        #         # print(c[1])
        #         # print(c[0])
        #         # print('%d -- %s\n%f\n%s' % (i, c[2], c[1], c[0]))
        #         i += 1
        #         if i > 5:
        #             break
        if not len(passages_sorted):
            return NO_ANSWER


        best_passage = passages_sorted[0]
        reply = self.make_json(best_passage[0], best_passage[2])
        # print(passages_sorted[0])
        print('REPLY: ', reply)

        # best_passage = 'best dummy passage'
        return reply  # best_passage


    def make_json(self, answer, source):
        return json.dumps({'answer': answer, 'source': source})

    # splits question into words, filters out garbage tokens
    # computes KL values and returns words with the highest KL values
    def make_query(self, question):
        def make_tokens():
            # split question into tokens and does basic cleaning
            t_init = tokenize.word_tokenize(question)
            t_clean = []

            for t in t_init:
                t = t.lower().strip()

                # if empty, ot length < 3, or contains garbage symbols --> skip
                if t == '' or len(t) < 3 or not bool(re.match('[a-z0-9]+', t)):
                    continue
                t_clean.append(t)

            return t_clean

        def make_dict(tokens):
            # takes in a list of words, converts them into dictionary word - freq
            local_freq = {}
            local_count = {}
            total_words = len(tokens)

            for t in tokens:
                local_count[t] = local_count.get(t, 0) + 1

            for p in local_count.items():
                local_freq[p[0]] = p[1]/total_words

            return local_freq

        def count_KL_values(local_freq):
            kl_vaues = {}
            # computes values for each word, returns a dictionary
            for word in local_freq.keys():
                f = local_freq[word]
                g = self.protocol.get_word_freq(word)
                if g == 0:
                    # if there's no such word in our dictionary, skip it
                    continue
                else:
                    kl = float(f) * math.log(float(f) / float(g), math.e)

                kl_vaues[word] = kl
            return kl_vaues

        tokens = make_tokens()
        # print('Initial tokenization: ', tokens)
        local_distr = make_dict(tokens)
        # print('Local distribution: ', local_distr)
        kl_values = count_KL_values(local_distr)
        # print('KL values: ', kl_values)

        query_pairs = sorted(kl_values.items(), key=operator.itemgetter(1), reverse=True)
        query_words = [q[0] for q in query_pairs[:QUERY_LENGTH]]

        sorted_query = []
        # we should preserve the initial order of words in the question
        for t in tokens:
            if t in query_words and t not in sorted_query:
                sorted_query.append(t)

        # print('Query words: ', query_words)
        return sorted_query


class QuestionProtocol(Protocol):
    # this class is doing all the work.

    # we want to kee access to the factory (and hence to the dictionary)
    def __init__(self, factory):
        print('Constructing another question protocol')
        self.factory = factory

    def dataReceived(self, data):
        print('data received')
        data = data.decode(encoding='utf_8').strip()

        print('DATA RECEIVED: ', data)

        # TODO: insert answer computations here.
        
        myCrystalBall = CrystalBall(self, data)
        best_passage = myCrystalBall.give_me_the_answer()

        # best_passage = myCrystalBall.answer_question()
        # best_passage = myCrystalBall.ask_bing(query)
        self.sendData(best_passage)

    def sendData(self, reply):
        self.transport.write(reply.encode(encoding='utf_8'))
        print('sent the data back to sender')

    def connectionLost(self, reason):
        print('!!! Connection lost !!!')

    def get_word_freq(self, word):
        return self.factory.get_frequency(word)

    def timeout(self):
        # self.sendData(NO_ANSWER)
        self.transport.abortConnection()
        



class QuestionFactory(Factory):
    # this class keeps persistent configuration
    # we will load the dictionary here once and access it multiple times later.

    # the only method that we need from here is buildProtocol
    # that returns an instance of Question processor, that does all the work.

    def __init__(self):
        self.dictionary = eval(open(DICTIONARY_FILENAME).read())

    def buildProtocol(self, addr):
        protocol = QuestionProtocol(self)
        # threading.Timer(5, protocol.stop_protocol).start()
        # threading.Timer(1, self.destruct_protocol, [protocol], {}).start()
        return protocol

    def get_frequency(self, word):
        # word = word.decode(encoding='utf_8')

        # lookup the word in the dictionary
        # if doesn't exist return 0
        return self.dictionary.get(word, 0)

    def destruct_protocol(self, protocol):
        print('Everything breaks now.')
        protocol.timeout()
        # del protocol
        print('Killed protocol')




endpoint = TCP4ServerEndpoint(reactor, 11001)
print('endpoint established')
endpoint.listen(QuestionFactory())
print('endpoint started to listen')
reactor.run()
print('We\'re done.')
