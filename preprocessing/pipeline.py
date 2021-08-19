import time
import os
import sys
import json
import re
from multiprocessing import Pool
import multiprocessing
from bs4 import BeautifulSoup
import urllib3
http = urllib3.PoolManager()
urllib3.disable_warnings()
import copy
from shutil import copyfile
from nltk.tokenize import word_tokenize, sent_tokenize
import glob
sys.path.append('/data/wenhu')
from table_utils.utils import *

output_folder = 'data'
input_htmls = '../htmls'

if os.path.exists('old_merged_unquote.json'):
	with open('old_merged_unquote.json') as f:
		dictionary = json.load(f)
else:
	dictionary = {}
	
with open('../orig_id_to_uid.json', 'r') as f:
	uid_mapping = json.load(f)
	white_list = set(uid_mapping.values())
default_setting = {'miniumu_row': 8, 'ratio': 0.7, 'max_header': 6, 'min_header': 2}

def harvest_tables(f_name):
	results = []
	with open(f_name, 'r') as f:
		soup = BeautifulSoup(f, 'html.parser')
		rs = soup.find_all(class_='wikitable sortable')
		
		for it, r in enumerate(rs):
			heads = []
			rows = []
			for i, t_row in enumerate(r.find_all('tr')):
				if i == 0:
					for h in t_row.find_all(['th', 'td']):
						h = remove_ref(h)
						if len(h.find_all('a')) > 0:
							heads.append((h.get_text(separator=" ").strip(), process_link(h)))
						else:
							heads.append((h.get_text(separator=" ").strip(), []))
						assert isinstance(heads[-1][0], str)
						assert isinstance(heads[-1][1], list)
				else:
					row = []
					for h in t_row.find_all(['th', 'td']):
						h = remove_ref(h)
						if len(h.find_all('a')) > 0:
							row.append((h.get_text(separator=" ").strip(), process_link(h)))
						else:
							row.append((h.get_text(separator=" ").strip(), []))
						assert isinstance(row[-1][0], str)
						assert isinstance(row[-1][1], list)

					if all([len(cell[0]) == 0 for cell in row]):
						continue
					else:
						rows.append(row)

			rows = rows[:20]
			uid = os.path.basename(f_name.replace('.html', '')) + "_{}".format(it)
			if (any([len(row) != len(heads) for row in rows]) or len(rows) < 8) and uid not in white_list:
				continue
			else:
				try:
					section_title = get_section_title(r)
				except Exception:
					section_title = ''
				try:
					section_text = get_section_text(r)
				except Exception:
					section_text = ''
				title = soup.title.string
				title = re.sub(' - Wikipedia', '', title)
				url = 'https://en.wikipedia.org/wiki/{}'.format('_'.join(title.split(' ')))
				results.append({'url': url, 'title': title, 'header': heads, 'data': rows, 
								'section_title': section_title, 'section_text': section_text,
								'uid': uid})
	return results


def get_summary(page):
	if page.startswith('https'):
		pass
	elif page.startswith('/wiki'):
		page = 'https://en.wikipedia.org{}'.format(page)
	else:
		page = 'https://en.wikipedia.org/wiki/{}'.format(page)
	
	# Using shortcut
	tmp = page.replace('https://en.wikipedia.org', '')
	if urllib.parse.unquote(tmp) in dictionary:
		return dictionary[urllib.parse.unquote(tmp)]

	r = http.request('GET', page)
	if r.status == 200:
		data = r.data.decode('utf-8')
		data = data.replace('</p><p>', ' ')        
		soup = BeautifulSoup(data, 'html.parser')

		div = soup.body.find("div", {"class": "mw-parser-output"})

		children = div.findChildren("p" , recursive=False)
		summary = 'N/A'
		for child in children:
			if child.get_text().strip() != "":
				html = str(child)
				html = html[html.index('>') + 1:].strip()
				if not html.startswith('<'):
					summary = child.get_text(separator=" ").strip()
					break
				elif html.startswith('<a>') or html.startswith('<b>') or \
						html.startswith('<i>') or html.startswith('<a ') or html.startswith('<br>'):
					summary = child.get_text(separator=" ").strip()
					break
				else:
					continue
		return summary
	elif r.status == 429:
		time.sleep(1)
		return get_summary(page)
	else:
		raise

def crawl_hyperlinks(inputs):
	table = inputs
	dictionary = {}
	for cell in table['header']:
		for tmp in cell[1]:
			if tmp not in dictionary:                
				try:
					summary = get_summary(tmp)
					dictionary[tmp] = summary
				except Exception:
					dictionary[tmp] = 'N/A'
		
	for row in table['data']:
		for cell in row:
			for tmp in cell[1]:
				if tmp not in dictionary:
					try:
						summary = get_summary(tmp)
						dictionary[tmp] = summary
					except Exception:
						dictionary[tmp] = 'N/A'

	assert '.org' in table['url']
	name = re.sub(r'.+\.org', '', table['url'])
	try:
		summary = get_summary(name)
		dictionary[name] = summary
	except Exception:
		dictionary[name] = 'N/A'

	return dictionary

def summarize(table):
	tmp = '_'.join(table['title'].split(' '))
	name = '/wiki/{}'.format(tmp)
	try:
		summary = get_summary(table['url'])
	except Exception:
		summary = 'N/A'
	return {name: summary}

def tokenization_tab(f_n):
	with open(f_n) as f:
		table = json.load(f)
	
	for col_idx, cell in enumerate(table['header']):
		table['header'][col_idx][0] = tokenize(cell[0], True)
		for i, ent in enumerate(cell[1]):
			table['header'][col_idx][1][i] = urllib.parse.unquote(table['header'][col_idx][1][i])

	for row_idx, row in enumerate(table['data']):
		for col_idx, cell in enumerate(row):
			table['data'][row_idx][col_idx][0] = tokenize(cell[0], True)
			for i, ent in enumerate(cell[1]):
				table['data'][row_idx][col_idx][1][i] = urllib.parse.unquote(table['data'][row_idx][col_idx][1][i])
	
	f_n = f_n.replace('/tables/', '/tables_tok/')
	with open(f_n, 'w') as f:
		json.dump(table, f, indent=2)

def tokenization_req(f_n):
	with open(f_n) as f:
		request_document = json.load(f)

	for k, v in request_document.items():
		sents = tokenize(v)
		request_document[k] = sents

	f_n = f_n.replace('/request/', '/request_tok/')
	with open(f_n, 'w') as f:
		json.dump(request_document, f, indent=2)

def recover(string):
	string = string[6:]
	string = string.replace('_', ' ')
	return string
	
def inplace_postprocessing(tables, default_setting):
	deletes = []
	for i, table in enumerate(tables):
		# Remove sparse columns
		to_remove = []
		for j, h in enumerate(table['header']):
			if 'Coordinates' in h[0] or 'Image' in h[0]:
				to_remove.append(j)
				continue
			
			count = 0
			total = len(table['data'])
			for d in table['data']:
				if d[j][0] != '':
					count += 1
			
			if count / total < 0.5:
				to_remove.append(j)
		
		bias = 0
		for r in to_remove:
			del tables[i]['header'][r - bias]
			for _ in range(len(table['data'])):
				del tables[i]['data'][_][r - bias]
			bias += 1
		
		# Remove sparse rows
		to_remove = []
		for k in range(len(table['data'])):
			non_empty = [1 if _[0] != '' else 0 for _ in table['data'][k]]
			if sum(non_empty) < 0.5 * len(non_empty):
				to_remove.append(k)
		
		bias = 0
		for r in to_remove:        
			del tables[i]['data'][r - bias]
			bias += 1

		if table['uid'] in white_list:
			continue
		elif len(table['header']) > default_setting['max_header']:
			deletes.append(i)
		elif len(table['header']) <= default_setting['min_header']:
			deletes.append(i)
		else:
			count = 0
			total = 0
			for row in table['data']:
				for cell in row:
					if len(cell[0]) != '':
						if cell[1] == []:
							count += 1                    
						total += 1
			if count / total >= default_setting['ratio']:
				deletes.append(i)

	print('out of {} tables, {} need to be deleted'.format(len(tables), len(deletes)))

	bias = 0
	for i in deletes:
		del tables[i - bias]
		bias += 1

if __name__ == "__main__":
	if len(sys.argv) == 2:
		steps = sys.argv[1].split(',')
	else:
		steps = ['1', '2', '3', '4', '5']

	cores = multiprocessing.cpu_count()
	pool = Pool(cores)
	print("Initializing the pool of cores")

	if not os.path.exists(output_folder):
		os.mkdir(output_folder)
	if not os.path.exists('{}/tables'.format(output_folder)):
		os.mkdir('{}/tables'.format(output_folder))
	if not os.path.exists('{}/request'.format(output_folder)):
		os.mkdir('{}/request'.format(output_folder))
	
	if '1' in steps:
		# Step1: Harvesting the tables
		rs = pool.map(harvest_tables, glob.glob(input_htmls + '/*.html'))
		tables = []
		for r in rs:
			tables = tables + r
		print("Step1: Finishing harvesting the tables")
		# Step2: Postprocessing the tables
		inplace_postprocessing(tables)
		with open('{}/processed_new_table_postfiltering.json'.format(output_folder), 'w') as f:
			json.dump(tables, f, indent=2)
		print("Step1: Finsihing postprocessing the tables")

	if '2' in steps:
		# Step3: Getting the hyperlinks
		with open('{}/processed_new_table_postfiltering.json'.format(output_folder), 'r') as f:
			tables = json.load(f)
		print("Step2-1: Total of {} tables".format(len(tables)))
		rs = pool.map(crawl_hyperlinks, tables)
		for r in rs:
			dictionary.update(r)
		merged_unquote = {}
		for k, v in dictionary.items():
			if k is None:
				continue
			v = re.sub(r'\[[\d]+\]', '', v).strip()
			merged_unquote[url2dockey(k)] = clean_text(v)
		with open('{}/merged_unquote.json'.format(output_folder), 'w') as f:
			json.dump(merged_unquote, f, indent=2)
		print("Step2-2: Finishing collecting all the links")

	if '3' in steps:
		# Step5: distribute the tables into separate files
		with open('{}/processed_new_table_postfiltering.json'.format(output_folder), 'r') as f:
			tables = json.load(f)
		with open('{}/merged_unquote.json'.format(output_folder), 'r') as f:
			merged_unquote = json.load(f)

		for idx, table in enumerate(tables):
			for row_idx, row in enumerate(table['data']):
				for col_idx, cell in enumerate(row):
					table['data'][row_idx][col_idx][0] = clean_cell_text(cell[0])
			
			for col_idx, header in enumerate(table['header']):
				table['header'][col_idx][0] = clean_cell_text(header[0])

			headers = table['header']
			if headers[0] == '':
				for i in range(len(table['data'])):
					del table['data'][i][0]
				del headers[0]

			headers = table['header']
			if any([_[0] == 'Rank' for _ in headers]):
				if table['data'][0][0] == '':
					for i in range(len(table['data'])):
						if table['data'][i][0][0] == '':
							table['data'][i][0][0] = str(i + 1)
					
			if any([_[0] == 'Place' for _ in headers]):
				assert isinstance(table['data'][0][0][0], str)
				if table['data'][0][0][0] == '':
					for i in range(len(table['data'])):
						if table['data'][i][0][0] == '':
							table['data'][i][0][0] = str(i + 1)

			name = url2dockey(re.sub(r'.+\.org', '', table['url']))
			table['intro'] = merged_unquote[name]
			table['uid'] = urllib.parse.unquote(table['uid'])
			with open('{}/tables/{}.json'.format(output_folder, table['uid']), 'w') as f:
				json.dump(table, f, indent=2)

		print("Step3: Finishing distributing the tables")

	if '4' in steps:
		# Step 6: distribute the request into separate files 
		with open('{}/merged_unquote.json'.format(output_folder), 'r') as f:
			merged_unquote = json.load(f)
		for k in merged_unquote:
			merged_unquote[k] = clean_text(merged_unquote[k])
		
		def get_request_summary(f_id):
			with open(f_id) as f:
				table = json.load(f)
		
			local_dict = {}
			for d in table['header']:
				for url in d[1]:
					url = urllib.parse.unquote(url)
					local_dict[url] = merged_unquote[url]
			
			for row in table['data']:
				for cell in row:
					for url in cell[1]:
						url = urllib.parse.unquote(url)
						local_dict[url] = merged_unquote[url]

			with open(f_id.replace('/tables/', '/request/'), 'w') as f:
				json.dump(local_dict, f, indent=2)
		
		for f in glob.glob('{}/tables/*.json'.format(output_folder)):
			get_request_summary(f)
		print("Step4: Finishing distributing the requests")

	if '5' in steps:
		# Step7: tokenize the tables and request
		if not os.path.exists('{}/request_tok'.format(output_folder)):
			os.mkdir('{}/request_tok'.format(output_folder))
		if not os.path.exists('{}/tables_tok'.format(output_folder)):
			os.mkdir('{}/tables_tok'.format(output_folder))
		pool.map(tokenization_req, glob.glob('{}/request/*.json'.format(output_folder)))
		pool.map(tokenization_tab, glob.glob('{}/tables/*.json'.format(output_folder)))

		pool.close()
		pool.join()
		print("Step5: Finishing tokenization")

