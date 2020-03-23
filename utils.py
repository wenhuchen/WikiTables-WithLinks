from nltk.tokenize import word_tokenize, sent_tokenize
import urllib.parse

def tokenize(string):
    return " ".join(word_tokenize(string))

def url2dockey(string):
	string = urllib.parse.unquote(string)
	return string

def filter_firstKsents(string, k):
	string = sent_tokenize(string)
	string = string[:k]
	return " ".join(string)
