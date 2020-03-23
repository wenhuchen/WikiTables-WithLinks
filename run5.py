import wikipedia
import json
import sys
from multiprocessing import Pool
import multiprocessing
from bs4 import BeautifulSoup
import urllib3
import time
import re
import os

http = urllib3.PoolManager()
urllib3.disable_warnings()

def get_summary(page):
    if page.startswith('https'):
        pass
    elif page.startswith('/wiki'):
        page = 'https://en.wikipedia.org{}'.format(page)
    else:
        page = 'https://en.wikipedia.org/wiki/{}'.format(page)
    
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
                    summary = child.get_text().strip()
                    break
                elif html.startswith('<a>') or html.startswith('<b>') or \
                        html.startswith('<i>') or html.startswith('<a ') or html.startswith('<br>'):
                    summary = child.get_text().strip()
                    break
                else:
                    continue
        return summary
    elif r.status == 429:
        time.sleep(1)
        return get_summary(page)
    else:
        raise


def sub_func(inputs):
	table, index = inputs
	dictionary = {}
	for cell in table['header']:
		if cell[1]:
			for tmp in cell[1]:
				if tmp not in dictionary:                
					try:
						summary = get_summary(tmp)
						dictionary[tmp] = summary
					except Exception:
						dictionary[tmp] = 'N/A'
		
	for row in table['data']:
		for cell in row:
			if cell[1]:
				for tmp in cell[1]:
					if tmp not in dictionary:
						try:
							summary = get_summary(tmp)
							dictionary[tmp] = summary
						except Exception:
							dictionary[tmp] = 'N/A'
	
	with open('hyperlinks/{}.json'.format(index), 'w') as f:
		json.dump(dictionary, f, indent=2)

def sub_func2(table):
	tmp = '_'.join(table['title'].split(' '))
	name = '/wiki/{}'.format(tmp)
	try:
		summary = get_summary(table['url'])
	except Exception:
		summary = 'N/A'
	return name, summary

if __name__ == "__main__":
	option = sys.argv[1]
	with open('processed_new_table_postfiltering.json', 'r') as f:
		tables = json.load(f)

	if option == 'debug':
		for i, table in enumerate(tables):
			sub_func((table, i))
	elif option == 'map':
		cores = multiprocessing.cpu_count()
		pool = Pool(cores)
		
		print("finished loading the tables")
		pool.map(sub_func, zip(tables, range(len(tables))))
		
		dictionary = {}
		for f in os.listdir('hyperlinks/'):
			if f.endswith('json'):
				with open('hyperlinks/' + f, 'r') as fw:
					d = json.load(fw)
					dictionary.update(d)

		rs = pool.map(sub_func2, tables)
		title_dictionary = dict(rs)
				
		dictionary.update(title_dictionary)

		print('totally {}'.format(len(dictionary)))
		failed = [k for k, v in dictionary.items() if v == 'N/A']
		print('failed {} items'.format(len(failed)))

		for k, v in dictionary.items():
			dictionary[k] = re.sub(r'\[[\d]+\]', '', v).strip()
			
		merged_unquote = {}
		for k, v in dictionary.items():
			merged_unquote[urllib.parse.unquote(k)] = v

		with open('wikipedia/merged_unquote.json', 'w') as f:
			json.dump(merged_unquote, f, indent=2)
	else:
		raise NotImplementedError
