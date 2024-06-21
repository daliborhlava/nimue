- Optional|Sourcing - Obtain mbox (e.g. from Google takeout)
- Optional|Sourcing - Use tool to convert mbox into email per file (e.g. https://www.recoverytools.com/mbox/migrator/)
- Ingest raw email naming should be: 1-3-2017__Jane doe_ _Jane.Doe@example.com__RE_ XXX XX - lorem ipsum
- Put data into $ingest-dir (variable in secrets.json), all txt files will be recurisively scanned
- Run process.py, which processes files one by one, tags metadata, output goes to ingest-processed. Analytics file is output into analytics directory. Notebook is ready there to be used.
- Optional|Costs - Tokens can be optionally counter by token-counter.py, output stored to analytics directory.
- Run embed.py which embeds the data and creates embedding vector for each file.
- Run load.py to finally load the fully processed data.
- Data is now ready to be used.
- Run email-api.py to expose search capabilities to nimui core.


* TODO
- change to read all txt files; track stats
    - currently it is not obvious if some files are in multiple folders, but if dupes are reported, it should not matter much
- "attachments": "" get NaN treatment