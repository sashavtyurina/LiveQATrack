__author__ = 'Alex'
import re
from nltk import PorterStemmer

STOP_WORDS_FILENAME = 'stop_words'
class CleanText(object):
    def __init__(self, words):
        # words - a list of words
        self.words = words
        with open(STOP_WORDS_FILENAME) as f:
            self.stop_words = f.readlines()
            self.stop_words = [w.strip() for w in self.stop_words]

    def remove_stop_words(self):
        result_text = []
        for token in self.words:
            if not token in self.stop_words:
                result_text.append(token)
        self.words = result_text
        return self.words

    def stem_words(self):
        stemmer = PorterStemmer()
        stems = [stemmer.stem(t) for t in self.words]
        self.words = stems
        return self.words
        #
        # stemmed_words = []
        # for token in self.words:
        #     # IF a word ends in “ies,” but not “eies” or “aies”
        #     # THEN “ies” - “v”
        #     if bool(re.match('\w*[^ae]ies$', token)):
        #         token = token[::-1].replace('ies'[::-1], 'y', 1)[::-1]
        #     elif bool(re.match('\w*[^aeo]es$', token)):
        #         token = token[::-1].replace('es'[::-1], 'e', 1)[::-1]
        #     elif bool(re.match('\w*[^us]s$', token)):
        #         token = token[::-1].replace('s'[::-1], '', 1)[::-1]
        #     stemmed_words.append(token)
        # return stemmed_words

