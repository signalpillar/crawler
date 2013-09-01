""" Hyper-links Crawler

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

"""
import sys
import urlparse
import collector
import docopt
import json
from fn import _ as __


VERSION = "0.0.1"


def cli(args):
    try:
        url, limit, dest_file_name, dbout, pretty_print = _parse_args(
            args,
            ("--url", get_url),
            ("--limit", get_limit),
            ("--out", identity),
            ("--dbout", identity),
            ("--pretty-print", identity))

        graph = collector.collect_outgoing_urls(url, limit)
        print_graph(
            graph,
            dest_file_name=dest_file_name,
            pretty_print=pretty_print)
        dbout and send_to_mongodb(graph)
    except CliException, ce:
        exit_cli(str(ce), 1)


class CliException(Exception):
    pass


class InvalidArgumentValue(CliException):
    pass


identity = __


def exit_cli(msg, error_code):
    sys.stderr.write(msg)
    sys.exit(error_code)


def to_json(graph, pretty_print=False):
    '@types: dict[str, collector.UrlInfo], bool -> str'
    graph = collector.url_to_info_as_pure_dict(graph)
    indent = pretty_print and 4 or 0
    return json.dumps(graph, indent=indent)


def print_graph(graph, dest_file_name=None, pretty_print=False):
    '@types: dict, str?, bool'
    graph_in_json = to_json(graph, pretty_print)
    if dest_file_name:
        with open(dest_file_name, "w+") as f:
            f.write(graph_in_json)
    else:
        print(graph_in_json)


def send_to_mongodb(graph):
    print 'Send to MongoDB'


def get_url(url):
    """
    @types: str -> str
    @raise: InvalidArgumentValue: Invalid URL specified
    """
    if bool(urlparse.urlparse(url).netloc):
        return url
    raise InvalidArgumentValue("Invalid URL specified")


def get_limit(limit):
    '@types: str -> int'
    if limit and limit.isdigit():
        value = int(limit)
        if value > 0:
            return value
    raise InvalidArgumentValue("Invalid limit value specified")


def get_dest_file_name(file_name):
    return file_name


def _parse_args(arg_by_name, *argument_to_fn_pairs):
    '@types: dict[str, O], tuple[str, (str, O -> T)] -> list[T]'
    for arg_name, arg_fn in argument_to_fn_pairs:
        yield arg_fn(arg_by_name.get(arg_name))


if __name__ == '__main__':
    try:
        args = docopt.docopt(__doc__, version=VERSION)
        if args.get("--help"):
            print __doc__
        elif args.get("--version"):
            print VERSION
        else:
            cli(args)
    except KeyboardInterrupt:
        exit_cli("Interrupted\n", 1)
