from twisted.internet.protocol import Protocol  # is instantiated per connection
from twisted.internet.protocol import Factory  # saves persistent configuration

from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
# DICTIONARY_FILE = 'dict_temp.txt'
# dictionary = eval(' '.join(open(self.DICTIONARY_FILE).readlines()))


class Dictionary(Protocol):
    # def __init__(self):
    #     self.DICTIONARY_FILE = 'dict_temp.txt'
    #     self.dictionary = eval(' '.join(open(self.DICTIONARY_FILE).readlines()))

    # def __init__(self):
    #     self.factory = factory

    def dataReceived(self, data):
        print('data received')
        print(data)        
        # self.transport.write(data)

        reply = 'our default reply' #input()
        self.transport.write(reply.encode(encoding='utf_8'))
        print('sent the data back to sender')

    def dataReceived111(self, data):

        print('data received')
        # if data:
        #     print('data received: %s' % data.decode(encoding='utf_8'))


        # if data == 'exit':
        #     self.transport.loseConnection()
        #     self.transport.write(data)

        # freq = self.factory.get_word_frequency(data)
        # message = (data.decode(encoding='utf_8') + ' -- ' + str(freq)).encode(encoding='utf_8')
        # message = 'our response message'

        self.transport.write(data)
        print('sent a reply')
        #
        # word = str(data)
        # if dictionary.get(word):
        #     self.transport.write(dictionary[word])
        # else:
        #     # return None
        #     self.transport.write(None)


class DictionaryFactory(Factory):
	# this class keeps persistent configuration
	# we will load the dictionary here once and access it multiple times later.
    
    # def __init__(self):
    #     i = 0
        # self.DICTIONARY_FILE = 'dict_temp.txt'
        # self.dictionary = eval(' '.join(open(self.DICTIONARY_FILE).readlines()))

    def buildProtocol(self, addr):
        return Dictionary()

    # def get_word_frequency(self, word):
    #     word = word.decode(encoding='utf_8')
    #     if self.dictionary.get(word):
    #         return self.dictionary[word]
    #     else:
    #         return 0

# 8007 is the port you want to run under. Choose something >1024
endpoint = TCP4ServerEndpoint(reactor, 11001)
print('endpoint established')
endpoint.listen(DictionaryFactory())
print('endpoint started to listen')
reactor.run()
print('We\'re done.')
