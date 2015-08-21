__author__ = 'Alex'
from sklearn.preprocessing import OneHotEncoder
from sklearn import preprocessing as pp
from Prefixspan import Prefixspan


# first we want to train our model and save it in our persistent configuration
# for every sentence that we want to classify as Q/NQ we will run only clf.predict(X_test)
# here's a tutorial for one class SVM classification http://scikit-learn.org/stable/auto_examples/svm/plot_oneclass.html

# But first we need to collect features that will be used for classification
# 1. First set of features is whether or not a keyword exists in a sentence. (keywords are wh, can't, need, etc)
# 2. # of words in a sentence.

# to be honest I'm pretty certain this isn't going to work,
# so we might as well just skip this step and move on to sequential patterns.
# We will be using prefix span algorithm to find frequent sequences - patterns
# Once we collect enough patterns, we can use them as features for SVM.



# 1. for every incoming sentence translate it into a feature vector =
# + a vector consisting of POS tags and keywords (WH, stop words, etc.)

# 2. pass all the feature vectors to prefix span and save the patterns that it returns.
#  Save them in a persistence configuration.

# 3. Now the dimensionality of feature vectors for SVM is how many patterns we have
# For every sentence that we have we crate a feature-vector that we later will pass to SVM to build a model
# We will do this with One Hot Encoder

# 4. How do we determine if a pattern exists in a sentence?
# we run prefix span one, finding all subsequences and look if there're any from previously calculated frequent patterns

import sys

train_sentenses = open(sys.argv[1]).readlines()


