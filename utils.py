from nltk.tokenize import word_tokenize, sent_tokenize
import urllib.parse
import sys

def tokenize(string, remmove_dot=False):
    def func(string):
        return " ".join(word_tokenize(string))
    
    string = string.rstrip('.')
    """
    if maintain_dot and string.endswith('.'):
        tmp = string.split(' ')
        if len(tmp) <= 5 and tmp[-1][0].isupper() and string.find('.') != len(string) - 1:
            # If the phrase is short enough
            string = string.rstrip('.')
            return func(string) + '.'
    """
    return func(string)

def url2dockey(string):
    string = urllib.parse.unquote(string)
    return string

def filter_firstKsents(string, k):
    string = sent_tokenize(string)
    string = string[:k]
    return " ".join(string)
