import os
import sys
import json
from multiprocessing import Pool
from nltk.tokenize import sent_tokenize
sys.path.append("./")
from utils import tokenize
import urllib.parse

def tokenization_req(f_n):
    if f_n.endswith('.json'):
        with open('{}/{}'.format('request', f_n)) as f:
            request_document = json.load(f)

        for k, v in request_document.items():
            sents = tokenize(v)
            request_document[k] = sents

        with open('request_tok/{}'.format(f_n), 'w') as f:
            json.dump(request_document, f, indent=2)

def tokenization_tab(f_n):
    if f_n.endswith('.json'):
        with open('{}/{}'.format('tables', f_n)) as f:
            table = json.load(f)
        
        for row_idx, row in enumerate(table['data']):
            for col_idx, cell in enumerate(row):
                for i, ent in enumerate(cell[0]):
                    if ent:
                        table['data'][row_idx][col_idx][0][i] = tokenize(ent, True)
                    if table['data'][row_idx][col_idx][1][i]:
                        table['data'][row_idx][col_idx][1][i] = urllib.parse.unquote(table['data'][row_idx][col_idx][1][i])
        
        for col_idx, header in enumerate(table['header']):
            for i, ent in enumerate(header[0]):
                if ent:
                    table['header'][col_idx][0][i] = tokenize(ent, True)
                if table['header'][col_idx][1][i]:
                    table['header'][col_idx][1][i] = urllib.parse.unquote(table['header'][col_idx][1][i])

        with open('tables_tok/{}'.format(f_n), 'w') as f:
            json.dump(table, f, indent=2)


if __name__ == "__main__":
    option = sys.argv[1]

    pool = Pool(64)

    if option == 'request':
        folder = 'request'
        pool.map(tokenization_req, os.listdir(folder))
        
        pool.close()
        pool.join()

    elif option == 'tables':
        folder = 'tables'
        pool.map(tokenization_tab, os.listdir(folder))

        pool.close()
        pool.join()

    else:
        raise NotImplementedError("not recognized")
"""
count = 0
for f in os.listdir(folder):
    sys.stdout.write("finished {} tables \r".format(count))
    tokenization(f)
    count += 1
"""
