from xml.etree.ElementTree import iterparse
from xml.etree.ElementTree import ParseError
from xml.etree.ElementTree import XMLParser
import sys

def parse_and_remove(filename, out):

    doc = iterparse(filename, ('start', 'end'))
    categories = {}
    questions = {}

    for event, elem in doc:
        if event == 'end':
            if elem.tag == 'message':
                if 'QID' in elem.text and 'TITLE' in elem.text and 'BODY' in elem.text and 'CATEGORY' in elem.text:
                    start_ind = elem.text.rfind('CATEGORY:')
                    if start_ind != -1:
                        cat = elem.text[start_ind+len('CATEGORY:'):].strip()
                        if not categories.get(cat):
                            categories[cat] = 1
                            questions[cat] = [elem.text]
                        else:
                            categories[cat] += 1
                            questions[cat].append(elem.text)

    print(categories)
    with open(out, 'w') as outfile:
    	for item in sorted(questions.items(), key=lambda x: x[0]):
          outfile.write('***%s***\n' % item[0])
          for q in item[1]:
            outfile.write('%s\n' % q)


def extract(filename, out):
    question = ''
    categories = {}
    start_question = False
    with open(out, 'a') as ff:
        with open(filename) as f:
            for line in f:
                if '<message>' in line:
                    start_question = True
                    # question += line.strip()
                if '</message>' in line and start_question:
                    start_question = False
                    question += line.strip()
                    if 'CATEGORY: null' not in question:
                        ff.write('%s\n' % question)
                    question = ''
                if start_question:
                    question += line.strip() + ' '


                # if start_question and 'CATEGORY:' in line:
                #     # print(line)
                #     start_ind = line.rfind('CATEGORY:')
                #     cat = line[start_ind + len('CATEGORY:'):].strip()
                #     if not categories.get(cat):
                #         categories[cat] = 1
                #     else:
                #         categories[cat] += 1
    # with open(out, 'w') as ff:
    #     print(categories)
    #     ff.write(str(categories))




name = sys.argv[1]
out = sys.argv[2]
extract(name, out)
# parse_and_remove(name, out)
