__author__ = 'Alex'

"""
    From a file with a question wrapped in a json object on every line extract sentences.
    Output single sentence on every line.
    Sentences are only taken from questions, not the answers.
"""

import sys
import json
import re

# src = open(sys.argv[1])
# dst = sys.argv[2]


def extract_sentences(src_name, dst_name):

    bad_jsons = 0
    good_sentences = 0

    with open(dst_name, 'w') as dst:
        with open(src_name) as src:
            for line in src:
                try:
                    json_q = json.loads(line)
                    text = json_q['title'] + ' ' + json_q['question']
                    sentences = re.split('(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
                    for sent in sentences:
                        dst.write('%s\n' % sent.strip())
                        good_sentences += 1
                except ValueError:
                    bad_jsons += 1
    print('bad_jsons = ', bad_jsons)
    print('good sentences = ', good_sentences)

extract_sentences(sys.argv[1], sys.argv[2])
