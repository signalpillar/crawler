""" Hyperlinks Crawler

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

"""
import collector
import docopt
import re
from fn import _ as __


VERSION = "0.0.1"


class CliException(Exception):
    pass


class InvalidArgumentValue(CliException):
    pass


def cli(args):
    try:
        url, depth, dest_file_name, dbout = parse_args(
            args,
            ("--url", get_url),
            ("--limit", get_depth),
            ("--out", identity),
            ("--dbout", identity))

        graph = collector.collect_links(url, depth)
        print_graph(graph, dest_file_name)
        dbout and send_to_mongodb(graph)
    except CliException, ce:
        exit_cli(str(ce), 1)


identity = (__)


def exit_cli(msg, error_code):
    print msg
    exit(error_code)


def to_json(graph):
    pass


def print_graph(graph, dest_file_name=None):
    '@types: dict, str?'
    graph_in_json = to_json(graph)
    if dest_file_name:
        with open(dest_file_name, "w+") as f:
            print(graph_in_json, f)
    else:
        print(graph_in_json)


def send_to_mongodb(graph):
    print 'Send to MongoDB'


# --------------------------------- argument parsing, validation

URL_RE = re.compile("^(http[s]?:\/\/)?"        # schema           (optional)
                    "(www\.)?"                 # subdomain www    (optional)
                    "[a-zA-Z0-9\.\-]+"         # hostname, subdomain
                    "\.[a-zA-Z]{2,5}[\.]?"     # domain
                    "(?:[\/?].*)?")            # URI              (optional)


def get_url(url):
    """
    @types: str -> str
    @raise: InvalidArgumentValue: Invalid URL specified
    """
    m = URL_RE.match(url)
    if m:
        return url
    raise InvalidArgumentValue("Invalid URL specified")


def get_depth(depth):
    '@types: str -> int'
    if depth and depth.isdigit():
        value = int(depth)
        if value > 0:
            return value
    raise InvalidArgumentValue("Invalid depth value specified")


def get_dest_file_name(file_name):
    return file_name


def parse_args(arg_by_name, *argument_to_fn_pairs):
    '@types: dict[str, O], tuple[str, (str, O -> T)] -> list[T]'
    for arg_name, arg_fn in argument_to_fn_pairs:
        yield arg_fn(arg_by_name.get(arg_name))


if __name__ == '__main__':
    args = docopt.docopt(__doc__, version=VERSION)
    if args.get("--help"):
        print __doc__
    elif args.get("--version"):
        print VERSION
    else:
        cli(args)
