import json
import json
from transformers import *
import torch
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import pairwise_distances
import nltk.data
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
from utils import *
import re

stopWords = set(stopwords.words('english'))
tfidf = TfidfVectorizer(strip_accents="unicode", ngram_range=(2, 3), stop_words=stopWords)
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
	
def longestSubstringFinder(S,T):
	S = S.lower()
	T = T.lower()
	m = len(S)
	n = len(T)
	counter = [[0]*(n+1) for x in range(m+1)]
	longest = 0
	lcs_set = set()
	for i in range(m):
		for j in range(n):
			if S[i] == T[j]:
				c = counter[i][j] + 1
				counter[i+1][j+1] = c
				if c > longest:
					lcs_set = set()
					longest = c
					lcs_set.add(S[i-c+1:i+1])
				elif c == longest:
					lcs_set.add(S[i-c+1:i+1])
	
	return longest, lcs_set

def longest_match_distance(str1s, str2s):
	longest_string = []
	for str1 in str1s:
		longest_string.append([])
		for str2 in str2s:
			length, _ = longestSubstringFinder(str1, str2)
			longest_string[-1].append(1 - length / len(str1))
	return longest_string

def searchForAnswer(answer, table, passages, mapping_entity_loc, mapping_entity_word):
	results = {}
	for i, row in enumerate(table['data']):
		for j, cell in enumerate(row):
			if answer in cell[0] or answer == ' , '.join(cell[0]):
				content = ' , '.join(cell[0])
				if content not in results:
					results[content] = [[(i, j)], None]
				else:
					results[content][0].append((i, j))
			elif len(answer) > 3 and answer.lower() in ' , '.join(cell[0]).lower():
				content = ' , '.join(cell[0])
				if content not in results:
					results[content] = [[(i, j)], None]
				else:
					results[content][0].append((i, j))
	 
	if len(results) > 0:
		return results
		
	for k, v in passages.items():
		if " " + answer.lower() + " " in " " + v.lower() + " ":
			results[mapping_entity_word[k]] = [mapping_entity_loc[k], k]
	
	return results

def searchForAnswerWithoutSpace(answer, passages, mapping_entity_loc, mapping_entity_word):
	correction = None
	results = {}
	for k, v in passages.items():
		v = " " + v.lower()
		tmp = v.find(" " + answer.lower())
		if tmp != -1:
			length = len(answer)
			while tmp + length < len(v) and v[tmp + length] != " ":
				length += 1
			correction = v[tmp:tmp + length]
			results[mapping_entity_word[k]] = [mapping_entity_loc[k], k]
			break

	return correction, results

def get_edit_distance_equal_1(answer, table):
	results = {}
	for i, row in enumerate(table['data']):
		for j, cell in enumerate(row):
			for tmp in cell[0]:
				dist = nltk.edit_distance(answer, tmp)
				if dist == 1:
					if tmp in results:
						results[tmp][0].append((i, j))
					else:
						results[tmp] = ([(i, j)], None, None)
	return results

def fixing_answer(string):
	if ',' in string:
		tmp = string.split(',')[0].strip()
		if not tmp.isdigit():
			string = [tmp]
		else:
			return None
	elif 'and' in string:
		tmp = string.split('and')[0].strip()
		string = [tmp]
	elif '(' and ')' in string:
		tmp = re.sub(r'([^\(\)]+) \((.+)\)$', r'\1###\2', string)
		string = [_.strip() for _ in tmp.split('###')]
	elif '-' in string:
		string = [string.replace(' ', ''), string.split('-')[0].strip(), string.split('-')[1].strip()]
	else:
		return None
	
	return string
		
def func(d):
	results = []
	table_id = d[0]
	#if table_id != 1129:
	#    return []

	with open('request_tok/{}.json'.format(table_id)) as f:
		requested_documents = json.load(f)
	
	with open('tables_tok/{}.json'.format(table_id)) as f:
		table = json.load(f)
	
	threshold = 85

	#title_wiki = table['url'][len('https://en.wikipedia.org'):]
	#del requested_documents[title_wiki]
	# Finding the answer and links to table
	qs = []
	ans = []
	links = []
	
	# Mapping entity link to cell, entity link to surface word
	mapping_entity_loc = {}
	mapping_entity_word = {}
	for row_idx, row in enumerate(table['data']):
		for col_idx, cell in enumerate(row):
			for i, ent in enumerate(cell[1]):
				if ent:
					ent = urllib.parse.unquote(ent)
					tmp = mapping_entity_loc.get(ent, [])
					if (row_idx, col_idx) not in tmp:
						tmp.append((row_idx, col_idx))
					
					mapping_entity_loc[ent] = tmp
					mapping_entity_word[ent] = cell[0][i]
	
	for col_idx, header in enumerate(table['header']):
		for i, ent in enumerate(header[1]):
			if ent:
				ent = urllib.parse.unquote(ent)
				tmp = mapping_entity_loc.get(ent, [])
				if (-1, col_idx) not in tmp:
					tmp.append((-1, col_idx))

				mapping_entity_loc[ent] = tmp
				mapping_entity_word[ent] = header[0][i]   
	
	# loop through the qa pairs
	for q, a in d[1:]:
		a = tokenize(a)
		tmp = searchForAnswer(a, table, requested_documents, mapping_entity_loc, mapping_entity_word)
		if len(tmp) == 0 and len(a) > 4 and not a.isdigit():
			# See if the space becomes a problem
			correction, tmp = searchForAnswerWithoutSpace(a, requested_documents, mapping_entity_loc, mapping_entity_word)
			if len(tmp) > 0:
				print("correct span! {} -> {}".format(a, correction))
				a = correction
			else:
				# correct the spelling                
				tmp = get_edit_distance_equal_1(a, table)
				if len(tmp) > 0:
					print("correct spelling! {} -> {}".format(a, list(tmp.keys())[0]))
					a = list(tmp.keys())[0]
				else:
					# Split the answer
					fixed_as = fixing_answer(a)
					if fixed_as:
						for correction in fixed_as:
							if correction:
								tmp = searchForAnswer(correction, table, requested_documents, mapping_entity_loc, mapping_entity_word)
								if len(tmp) > 0:
									print("correct splitting! {} -> {}".format(a, correction))
									a = correction
									break

		ans.append((a, tmp))
		qs.append(q)
		
		tmp_link = {}
		for row_idx, row in enumerate(table['data']):
			for col_idx, cell in enumerate(row):
				if cell[0] != ['']:
					for ent in cell[0]:
						ent = tokenize(ent)
						ratio = fuzz.partial_ratio(ent, q)
						if ratio > threshold:
							if ent in tmp_link:
								tmp_link[ent][0].append((row_idx, col_idx))
							else:
								tmp_link[ent] = ([(row_idx, col_idx)], None, ratio)

		links.append(tmp_link)
	
	keys = []
	paras = []
	for k, v in requested_documents.items():
		for _ in tokenizer.tokenize(v):
			keys.append(k)
			paras.append(_)
	
	para_feature = tfidf.fit_transform(paras)    
	
	q_feature = tfidf.transform(qs)
	
	dist_match = longest_match_distance(qs, paras)
	dist = pairwise_distances(q_feature, para_feature, 'cosine')
	
	for i in range(len(qs)):
		min_dist = {}
		tfidf_best_match = ('N/A', 1.)
		for k, d in zip(keys, dist[i]):
			if d < min_dist.get(k, 1):
				min_dist[k] = d
				if d < tfidf_best_match[-1]:
					if k not in mapping_entity_word:
						print(table_id, k)
					else:
						tfidf_best_match = (k, d)

		min_dist = {}
		string_best_match = ('N/A', 1.)
		
		for k, d in zip(keys, dist_match[i]):
			if d < min_dist.get(k, 1):
				min_dist[k] = d
				if d < string_best_match[-1]:
					if k not in mapping_entity_word:
						print(table_id, k)
					else:
						string_best_match = (k, d)
		
		if tfidf_best_match[0] != 'N/A':
			tfidf_best_match = {mapping_entity_word[tfidf_best_match[0]]: 
								(mapping_entity_loc[tfidf_best_match[0]], tfidf_best_match[0], tfidf_best_match[1])}
		else:
			tfidf_best_match = None

		if string_best_match[0] != 'N/A': 
			string_best_match = {mapping_entity_word[string_best_match[0]]:
								(mapping_entity_loc[string_best_match[0]], string_best_match[0], string_best_match[1])}
		else:
			string_best_match = None
		
		results.append({'table_id': table_id, 'question': qs[i], 'answer': ans[i], 'tf-idf': tfidf_best_match, 
						'string-overlap': string_best_match, 'link': links[i]})
	
	return results

with open('Mixed-Reasoning/collected_data.json') as f:
	data = json.load(f)


from multiprocessing import Pool

pool = Pool(64)
results_func = pool.map(func, data)

pool.close()
pool.join()

results = []
for _ in results_func:
	results.extend(_)
"""
results = []
for d in data:
	results.extend(func(d))
"""
with open('Mixed-Reasoning/processed_step1.json', 'w') as f:
	json.dump(results, f, indent=2)
