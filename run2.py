import json

with open('processed_table.json') as f:
    data = json.load(f)

import sys
import requests
import urllib.request, urllib.error, urllib.parse
import os

print('original data has {} entries'.format(len(data)))
new_data = []
for i, d in enumerate(data):
    sys.stdout.write("finished {}/{} \r".format(i, len(data)))
        
    if len(d['data']) > 8 and len(d['data']) < 30 and len(d['data'][0]) >= 3:
        headers = set(d['header'])
        if len(headers) == len(d['header']):
            cols = len(d['header'])
            count = 0
            for g in d['data'][0]:
                if g[1] is not None:
                    count += 1
            if count < 0.5 * cols:
                continue
            
            # process if there are enough hyperlinks
            title = d['title']
            title = '_'.join(title.split(' '))
                
            if not os.path.exists('htmls/{}.html'.format(title)):
                try:
                    response = urllib.request.urlopen(page)
                    webContent = response.read()
                    f = open('htmls/{}.html'.format(title), 'wb')
                    f.write(webContent)
                    f.close()
                except Exception:
                    continue

            d['page'] = '{}.html'.format(title)
            d['url'] = 'https://en.wikipedia.org/wiki/{}'.format(title)
            new_data.append(d)

print('filtered data has {} entries'.format(len(new_data)))
with open('processed_table_with_page.json', 'w') as f:
    json.dump(new_data, f, indent=2)