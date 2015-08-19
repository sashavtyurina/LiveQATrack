from xml.etree.ElementTree import iterparse
from xml.etree.ElementTree import ParseError
from xml.etree.ElementTree import XMLParser
import sys

def parse_and_remove(filename):

    doc = iterparse(filename, ('start', 'end'))
    categories = {}

    for event, elem in doc:
        if event == 'end':
            if elem.tag == 'message':
                if 'QID' in elem.text and 'TITLE' in elem.text and 'BODY' in elem.text and 'CATEGORY' in elem.text:
                    start_ind = elem.text.rfind('CATEGORY:')
                    if start_ind != -1:
                        cat = elem.text[start_ind+len('CATEGORY:'):].strip()
                        if not categories.get(cat):
                            categories[cat] = 1
                        else:
                            categories[cat] += 1

    print(categories)

name = sys.argv[1]
parse_and_remove(name)