import os
from bs4 import BeautifulSoup
import sys
import json
import re
from multiprocessing import Pool
import multiprocessing

def process_link(text):
    tmp = []
    hrefs = []
    for t in text.find_all('a'):
        if len(t.get_text().strip()) > 0:
            if 'href' in t.attrs and t['href'].startswith('/wiki/'):
                tmp.append(t.get_text().strip())
                hrefs.append(t['href'].split('#')[0])
            else:
                tmp.append(t.get_text().strip())
                hrefs.append(None)
    if len(tmp) == 0:
    	return [''], [None]
    else:
    	return tmp, hrefs
    """
    if all([_ is "/wiki/HTTP_404" for _ in hrefs]):
        return ','.join(tmp).strip(), None
    else:
        return ','.join(tmp).strip(), ' '.join(hrefs)
    """

def remove_ref(text):
	for x in text.find_all('sup'):
		x.extract()
	return text

files = os.listdir('htmls/')
cores = multiprocessing.cpu_count()

def sub_func(f_name):
	results = []
	with open('htmls/' + f_name, 'r') as f:
		soup = BeautifulSoup(f, 'html.parser')
		rs = soup.find_all(class_='wikitable sortable')
		
		for r in rs:
			heads = []
			rows = []
			for i, t_row in enumerate(r.find_all('tr')):
				if i == 0:
					for h in t_row.find_all(['th', 'td']):
						h = remove_ref(h)
						if len(h.find_all('a')) > 0:
							heads.append(process_link(h))
						else:
							heads.append(([h.get_text().strip()], [None]))
				else:
					row = []
					for h in t_row.find_all(['th', 'td']):
						h = remove_ref(h)
						if len(h.find_all('a')) > 0:
							row.append(process_link(h))
						else:
							row.append(([h.get_text().strip()], [None]))

					if all([len(cell[0]) == 0 for cell in row]):
						continue
					else:
						rows.append(row)
			
			rows = rows[:20]
			if any([len(row) != len(heads) for row in rows]) or len(rows) < 8:
				continue
			else:
				text = r.previous_sibling
				while text is not None and text.name != 'p' and text.string is not None:
					text = text.previous_sibling

				if text is None or text.string is None:
					context = ''
				else:
					context = text.string.strip()

				title = soup.title.string
				title = re.sub(' - Wikipedia', '', title)
				url = 'https://en.wikipedia.org/wiki/{}'.format('_'.join(title.split(' ')))
				results.append({'url': url, 'title': title, 'header': heads, 'data': rows, 'context': context})
	return results

pool = Pool(cores)
rs = pool.map(sub_func, files)

results = []
for r in rs:
	results = results + r

with open('processed_new_table.json', 'w') as f:
	json.dump(results, f, indent=2)
