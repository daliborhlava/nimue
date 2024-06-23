## Flow
- Optional|Sourcing - Obtain mbox (e.g. from Google takeout)
- Optional|Sourcing - Use tool to convert mbox into email per file (e.g. https://www.recoverytools.com/mbox/migrator/)
- Ingest raw email naming should be: DATE+FROM+SUBJECT, e.g. 1-3-2017__Jane doe_ _Jane.Doe@example.com__RE_ XXX XX - lorem ipsum
- Put data into $ingest-dir (variable in secrets.json), all txt files will be recurisively scanned
- Run process.py, which processes files one by one, tags metadata, output goes to ingest-processed. Analytics file is output into analytics directory. Notebook is ready there to be used.
- Optional|Costs - Tokens can be optionally counter by token-counter.py, output stored to analytics directory.
- Run embed.py which embeds the data and creates embedding vector for each file.
- Run load.py to finally load the fully processed data.
- Data is now ready to be used.
- Run email-api.py to expose search capabilities to nimui core.


## TODO
- process: some attribs are with _ and some with -, unify to -
- data alt after sorting out names
- embeddings, incl. resume (rename token counter to support both)
- utilize arg parser: just count..., review other pieces
- proper config management?
- API search
- API LLM-based to properly construct the query

## Gmail MBOX Extractor
In the exported directory structure as exported by the tool (https://www.recoverytools.com/mbox/),
there are lots of duplicates stores in different directories. Simple filename based matching eliminates vast majority, but about 3k out of 282k turned out to be missing with this approach hence it is better to process
all the files regardless since computing resources used and compute time spent are not significant.