# Hyperlinks crawler

UPDATE: The latest thing that I am interesting in is 

    Successfully installed geventhttpclient gevent greenlet



Everybody must write at least one crawler

```
Hyperlinks Crawler

Traverse the Web as a linked graph from the starting --url finding
all outgoing links (<a> tag).
It will store each outgoing link for the URL, and then repeat the process
for each or them, until --limit URLs will have been traversed.

USAGE:
    hyperlinks --url <start-url> --limit <depth> [--dbout] [--out <dest-file>]
    hyperlinks -h | --help
    hyperlinks --version

OPTIONS:
    -h --help         Show this screen
    --version         Show version
    --url             URL where to start hyper links crawling
    --limit           Depth of hyper links crawling
    --out <dest-file> File path to the JSON file where to store output,
                      if not specified output JSON to STDOUT
    --dbout           Causes the data to be stored in a MongoDB collection
```

## Initialization

To install requirements, recommended to use `virtualenv`

    mkdir -p ~/tmp/crawler-env
    virtualenv ~/tmp/crawler-env
    pip install -U -r requirements.txt

## Running tests

    ./run_tests


