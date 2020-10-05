# WikiTables-WithLinks
Crawled Wikipedia Tables with Passages for [HybridQA dataset](https://github.com/wenhuchen/HybridQA). 

[NOTE]: There was a bug in the previous version, now it's fixed and the tables have a new format listed below. The previous tables are indexed by number, now the new tables are indexed by page_name_position, the mapping can be found in orig_id_to_uid.json file.

# Folder Structure
- tables_tok/: containing all the tables, indexed by its name and its order in the page
```
  {
  "url": "https://en.wikipedia.org/wiki/National_Register_of_Historic_Places_listings_in_Johnson_County,_Arkansas",
  "title": "National Register of Historic Places listings in Johnson County, Arkansas",
  "header": [
    [
      "Name on the Register",
      []
    ],
    [
      "Date listed",
      []
    ],
  ]
  "data":[
    [
        [
          cell_text
          [hyperlink 1, hyperlink 2, ... ,]
        ],
        [
          cell_text
          [hyperlink 1, hyperlink 2, ... ,]
        ],
        ...
    ],
    [
        ...
    ],
    ...
  ]
```
- request_tok/: containing all hyperlinks within a given table
