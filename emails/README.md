## Ingestion Flow
1. Prepare data into source dir
2. Run process
3. Run embed
4. Run load

## Usage
1. Have emails ingested
2. Use search interface (email semantic search only)
3. Interact with core

### How To
- Optional|Sourcing - Obtain mbox (e.g. from Google takeout)
- Optional|Sourcing - Use tool to convert mbox into email per file (e.g. https://www.recoverytools.com/mbox/migrator/)
- Raw email naming should be: DATE+FROM+SUBJECT, e.g. 1-3-2017__Jane doe_ _Jane.Doe@example.com__RE_ XXX XX - lorem ipsum
- Put data into $source-dir (variable in secrets.json), all txt files will be recurisively scanned
- Run process.py, which processes files one by one, tags metadata, output goes to ingest-processed. Analytics file is output into analytics directory. Notebook is ready there to be used.
- Optional|Costs - Tokens can be optionally counter by token-counter.py, output stored to analytics directory.
- Run embed.py which embeds the data and creates embedding vector for each file.
- Run load.py to finally load the fully processed data.
- Data is now ready to be used.
- Run email-api.py to expose search capabilities to nimui core.


## TODO
- migrate to postresql + pgvector, install done
- run the full load
- think through the database aspect; should that be done as part of process?
- python execution / SQL execution on emails?
- email search api (non semantic, regex, fulltext)
- similar email api
- API LLM-based to properly construct the query; or orchestrate from external agent? no lets have a hierrarchy of agents to test how that works



## Long-Term Features
- attachment handling; tool now does extract links to attachments to metadata, files are on filesystem so definitely possible to extend to embed in some way attachments as well


## Gmail MBOX Extractor
In the exported directory structure as exported by the tool (https://www.recoverytools.com/mbox/),
there are lots of duplicates stores in different directories. Simple filename based matching eliminates vast majority, but about 3k out of 282k turned out to be missing with this approach hence it is better to process
all the files regardless since computing resources used and compute time spent are not significant.