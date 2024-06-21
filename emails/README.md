- Optional|Sourcing - Obtain mbox (e.g. from Google takeout)
- Optional|Sourcing - Use tool to convert mbox into email per file (e.g. https://www.recoverytools.com/mbox/migrator/)
- Ingest raw email naming should be: 1-3-2017__Jane doe_ _Jane.Doe@example.com__RE_ XXX XX - lorem ipsum
- Put data into data/ingest-raw as individual text files, one file per email
- Run process.py, which processes files one by one, tags metadata, output goes to ingest-processed. Analytics file is output.
- Optional|Costs - Tokens can be optionally counter by token-counter.py.
- Optional|Reporting - Resulting metadata dataframe can be analyzed through results.ipynb notebook.
- Run embed.py which embeds the data and puts it to ingest-embedded.
- Run load.py to finally load data into data from ingest-embedded.
- Data is now ready to be used.
- Run email-api.py to expose search capabilities to nimui core.


* TODO
- create error queue with emails that failed processing instead of termination
    - strange "header" keys - finalize list and read only known ones
- "attachments": "" get NaN treatment