# Hyperlinks crawler

Everybody must implement at least one crawler

```
Hyper-links Crawler

Traverse the Web as a linked graph from the starting --url finding
all outgoing links (<a> tag).
It will store each outgoing link for the URL, and then repeat the process
for each or them, until --limit URLs will have been traversed.

USAGE:
    hyperlinks [options] --url <start-url> --limit <limit>
    hyperlinks -h | --help
    hyperlinks --version

OPTIONS:
    -h --help             Show this screen
    --version             Show version
    --url <start-url>     URL where to start hyper-links crawling
    --limit <limit>       Limit of URLs to traverse
    --out <dest-file>     File path to the JSON file where to store output,
                          if not specified output JSON to STDOUT
    --pretty-print        JSON output will be pretty printed
    --dbout               Causes the data to be stored in a MongoDB collection
    --concurrent          Run crawler using async HTTP requests (experimental)

```

## Initialization

To install dependencies in `virtualenv` and run tests use 

    start_from_scratch.sh

## Running tests

    make test


