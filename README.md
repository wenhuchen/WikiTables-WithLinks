# WikiTables-WithLinks
Crawled Wikipedia Tables with Passages for [HybridQA dataset](https://github.com/wenhuchen/HybridQA).

# Folder Structure
- tables_tok/: containing all the tables
```
  {
  "url": "https://en.wikipedia.org/wiki/National_Register_of_Historic_Places_listings_in_Johnson_County,_Arkansas",
  "title": "National Register of Historic Places listings in Johnson County, Arkansas",
  "header": [
    [#cell 1
      [#all the field separated with a list
        "Name on the Register"
      ],
      [
      ]
    ],
    [#cell 2
      [#all the field separated with a list
        "Date listed"
      ],
      [
      ]
    ],
  ]
  "data":[
    [#row 1
        [#cell 1
          cell_text
          [hyperlink 1, hyperlink 2, ... ,]
        ],
        [#cell 2
          cell_text
          [hyperlink 1, hyperlink 2, ... ,]
        ],
        ...
    ],
    [#row 2
        ...
    ],
    ...
  ]
```
- request_tok/: containing all the tables with tokenized text


# Trouble Shooting
If you have problem with git clone, you can also download it from [Google Drive](https://drive.google.com/file/d/1_p774GShngBw0q8Bq2DMHs0dETucO3AW/view?usp=sharing).
