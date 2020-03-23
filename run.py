import json
import re
import sys

with open('tables.json') as f:
    results = []
    count = 0
    for line in f:
        sys.stdout.write('finished {}/{} \r'.format(count, '1652771'))
        count += 1
        try:
            d = json.loads(line)
            page_id = d['pgTitle']

            local_results = []
            for row in d['tableData']:
                tmp = []
                for cell in row:
                    text = cell['text']
                    group = re.search(r'href="([^ ]+)"', cell['tdHtmlString'])
                    if group:
                        hyperlink = group.group(1)
                    else:
                        hyperlink = None
                    tmp.append((text, hyperlink))

                local_results.append(tmp)

            local_headers = []
            for h in d['tableHeaders'][0]:
                local_headers.append(h['text'])

            results.append({'title': page_id, 'header': local_headers, 'data': local_results})

        except Exception:
            continue

    with open('processed_table.json', 'w') as f:
        json.dump(results, f, indent=2)
