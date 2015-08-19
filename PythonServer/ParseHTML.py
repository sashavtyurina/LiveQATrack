from html.parser import HTMLParser
import requests
import sys
import re
import os

# the minimum # of words that a paragraph should contain to qualify for a useful paragraph
# anything below is either navigational data, link, ads, etc. 
PARAGRAPH_LENGTH = 10
LOG_NAME = 'HTML_cleaning.txt'

"""
Once the page is fetched we want to extract actual text data from it
to further process it and figure out if it's good

For that we first want to strip HTML document from all the tags it might have
We also ignore style and script tags
"""
class HTMLStripper(HTMLParser):

    BAD_TAGS = ['style', 'script', 'title', 'table', 'label',  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'meta']
    BAD_ATTR = ['footer']
    # WANTED_TAGS = ['p']
    def __init__(self):
        
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.data = []
        self.bad_tag = False # ignores script, style tags
        # self.newline = False # adds a newline between paragraphs, otherwise add a space

    def is_bad(self, tag, attrs):
        for t in self.BAD_TAGS:
            if t in tag:
                return True
        for t in self.BAD_ATTR:
            for a in attrs:
                if t in a:
                    return True
        return False

    def handle_starttag(self, tag, attrs):
        # print(attrs)
        if self.is_bad(tag, attrs):
        # if tag in self.BAD_TAGS:
            self.bad_tag = True
        # else:
        #     self.log.write(tag)
        #     self.log.write('\n')

        # if tag in self.NEW_LINE:
        #     self.newline = True



    def handle_endtag(self, tag):
        if tag in self.BAD_TAGS:
            self.bad_tag = False

    def handle_data(self, data):
        def bad_data(data):
            # we want to avoid having useless navigational links, ads , etc. 
            spaced_data = re.subn('\s', ' ', data)[0]
            tokens = spaced_data.split(' ')
            few_words = len(tokens) < PARAGRAPH_LENGTH

            # avoid things like 'click here for detailed map'
            starts_with_click = data.lower().startswith('click') or data.lower().startswith('sign up')
            # not_a_word = single_word and not bool(re.match('[A-Za-z0-9]+', data))
            return few_words

        if not self.bad_tag:
            data = data.strip()
            if data:
                # if self.newline:
                #     self.data.append('\n')
                # else:
                #     self.data.append(' ')

                
                if bad_data(data):
                    # self.log.write('BAD DATA: ') 
                    return
                    
                self.data.append(data.strip())
                with open(LOG_NAME, 'a') as f:
                    f.write(data.strip())
                    f.write('\n')


    def getDataAsList(self):
        # return '\n'.join(self.data)
        return self.data #uncomment this if you want to work with a list of strings instead

    def getDataAsString(self):
        return ' '.join(self.data)

    def clearData(self):
        # print('***Clear data')
        # print(type(self.data), '\n', self.data)
        # self.data.clear()
        del self.data[:]


class WikipediaStripper (HTMLStripper):
    LIST_TAGS = []#['ol', 'ul']
    GOOD_TAGS = ['p']

    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.data = []
        self.record_data = False

    def handle_starttag(self, tag, attrs):
        if tag in self.GOOD_TAGS:
            self.record_data = True

    def handle_endtag(self, tag):
        if tag in self.GOOD_TAGS:
            self.record_data = False

    def handle_data(self, data):
        if self.record_data:
            self.data.append(data)

    def getData(self):
        return ' '.join(self.data)


class DataFilter(object):
    '''
    Cleans provided textual data.
    '''
    @staticmethod
    def clean(input_text):

        # remove brackets like this: (some details provided)
        filtered_text = re.subn('\(\s*[^\)]+\s*\)', '', input_text)[0]

        # remove references like [4], or [i.e. Majlis]
        filtered_text = re.subn('\[\s*[^\]]+\s*\]', '', filtered_text)[0]

        # put periods and commas right after the word, to eliminate this "hello world ."
        filtered_text = re.subn('\s+\.', '.', filtered_text)[0]
        filtered_text = re.subn('\s+,', ',', filtered_text)[0]
        filtered_text = re.subn('\s+\'', '\'', filtered_text)[0]
        # filtered_text = re.subn('\s+"', '"', filtered_text)[0]

        # remove repetitive space characters
        filtered_text = re.subn('\s+', ' ', filtered_text)[0]

        # remove any non English characters
        filtered_text = re.subn('[^\x00-\x7F]+', '', filtered_text)[0]
        return filtered_text


def fetchDocumentByURL(url):
    req = requests.get(url)
    return req.text

#
# # url = sys.argv[1]
# url = 'http://www.history.com/topics/mexico/mexico-timeline'
# html_doc = fetchDocumentByURL(url)
#
# striper = HTMLStripper()
# striper.feed(html_doc)
# lines = striper.getDataAsString()
#
# # filename = sys.argv[2]
# filename = 'output_html.txt'
# with open(filename, 'w') as ff:
# 	ff.write(lines)

# filename = sys.argv[1]
# with open(filename) as f:
#     text = ''.join(f.readlines())
#
# stripper = WikipediaStripper()
# stripper.feed(text)
# text = stripper.getData()
# text_clean = DataFilter.clean(text)
#
# # see if document contains ellipses <...>
# if bool(re.search('\.{3}', text_clean)):
#     print('Attention! Document %s contains ellipses. Sentence splitter will fail. Check it manually afterwards.' % filename)
# if bool(re.search('Politics portal', text_clean)):
#     print('Attention! Document %s contains \'politics portal\'. Remove it manually.' % filename)
#
# with open(filename, 'w') as f:
#     f.write(text_clean)
