__author__ = 'Alex'

from nltk import tokenize
import nltk
import enchant.checker as checker

KEYWORDS_FILENAME = 'keywords.txt'
KEYWORDS = [k.strip() for k in open(KEYWORDS_FILENAME).readlines()]

SPELL_CHECKER = checker.SpellChecker('en_US')

# generalize a given sentence:
# we don't touch keywords - wh, stopwords, etc
# for the rest of the words we replace them with their POS tag

def generalize_sentence(sentence):
    sentence = sentence.lower()
    # TODO: tokenize, remove punctuation symbols
    tokens = tokenize.word_tokenize(sentence)

    # TODO: if a woken is not a valid english word, leave it be. - Done
    # Most likely it is a typo or a online-content specific word

    gen_sentence = []
    for t in tokens:
        if t in KEYWORDS or not SPELL_CHECKER.check(t):
            gen_sentence.append(t)

        else:
            pos = nltk.pos_tag([t])
            gen_sentence.append(pos[0][1])  # we want only the tag

    return gen_sentence
