# WikiTables-WithLinks
Crawled Wikipedia Tables with Passages for [HybridQA dataset](https://github.com/wenhuchen/HybridQA).

# Folder Structure
- tables/: containing all the tables
```
  {
  "url": "https://en.wikipedia.org/wiki/National_Register_of_Historic_Places_listings_in_Johnson_County,_Arkansas",
  "title": "National Register of Historic Places listings in Johnson County, Arkansas",
  "header": [
    [#cell 1
      [#all the field separated with a list
        "Name on the Register"
      ],
      [#all the hyperlinks, null indicates no hyperlink
        null
      ]
    ],
    [#cell 2
      [#all the field separated with a list
        "Date listed"
      ],
      [#all the hyperlinks, null indicates no hyperlink
        null
      ]
    ],
  ]
  "data":[
    [#row 1
        [#cell 1
          [field 1, field 2, ... ,]
          [hyperlink 1, hyperlink 2, ... ,]
        ],
        [#cell 2
          [field 1, field 2, ... ,]
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
- tables_tok/: containing all the tables with tokenized text
- requests/: containing all the hyperlinked text for certain table.
- requests/: containing all the tokenized hyperlinked text for certain table.


# Trouble Shooting
If you have problem with git clone, you can also download it from [Google Drive](https://drive.google.com/file/d/1_p774GShngBw0q8Bq2DMHs0dETucO3AW/view?usp=sharing).
