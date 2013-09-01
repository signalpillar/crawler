import pytest
import mock

from itertools import izip
from functools import partial as Fn
from contextlib import nested

import docopt
import json

import hyperlinks
import collector


class TestCliArgumentsParsingUsingUsageHelpDefined:
    def test_several_optional_options_specified(self):
        # given
        argv = ['--url', 'url', '--limit', '3', '--out', "output.json",
                '--dbout']
        expected = {'--url': 'url', '--limit': '3',
                    '--help': False, '--version': False,
                    '--out': 'output.json', '--dbout': True}

        # when
        args = docopt.docopt(hyperlinks.__doc__, argv=argv)

        # then
        assert set(expected.items()).issubset(args.items())

    def test_out_option_specified(self):
        # given
        argv = ['--url', 'url', '--limit', '3', '--out', "output.json"]
        expected = {'--url': 'url', '--limit': '3',
                    '--help': False, '--version': False,
                    '--out': 'output.json'}

        # when
        args = docopt.docopt(hyperlinks.__doc__, argv=argv)

        # then
        assert set(expected.items()).issubset(args.items())

    def test_db_out_option_specified(self):
        # given
        argv = ['--url', 'url', '--limit', '3', '--dbout']
        expected = {'--url': 'url', '--limit': '3',
                    '--help': False, '--version': False,
                    '--dbout': True}

        # when
        args = docopt.docopt(hyperlinks.__doc__, argv=argv)

        # then
        assert set(expected.items()).issubset(args.items())

    def test_pretty_print_option_specified(self):
        # given
        argv = ['--url', 'url', '--limit', '3', '--pretty-print']
        expected = {'--url': 'url', '--limit': '3',
                    '--help': False, '--version': False,
                    '--pretty-print': True}

        # when
        args = docopt.docopt(hyperlinks.__doc__, argv=argv)

        # then
        assert set(expected.items()).issubset(args.items())

    @mock.patch("sys.exit")
    def test_help_option_specified(self, exit_fn, capsys):
        # given
        argv = ['--help', '--url', 'url', '--limit', '3']

        with pytest.raises(docopt.DocoptExit):
            # when
            docopt.docopt(hyperlinks.__doc__, argv=argv)
        out, err = capsys.readouterr()
        assert hyperlinks.__doc__.strip() == out.strip()

    def test_order_of_mandatory_parameters(self):
        # given

        argv = ['--url', 'url', '--limit', '3']
        expected = {'--url': 'url', '--limit': '3',
                    '--help': False, '--version': False}

        # when
        args = docopt.docopt(hyperlinks.__doc__, argv=argv)

        # then
        assert set(expected.items()).issubset(args.items())

        # given
        argv = ['--limit', '3', '--url', 'url']

        # when
        args = docopt.docopt(hyperlinks.__doc__, argv=argv)

        # then
        assert set(expected.items()).issubset(args.items())


class TestCli:

    def test_cli_flow_in_general(self, capsys):
        "Check whether all required steps are perfomed"
        graph = {'url1':
                 collector.new_url_info(
                     incomming=['x', 'y', 'z'],
                     outgoing=[]),
                 'url2':
                 collector.new_url_info(
                     incomming=['m', 'x'],
                     outgoing=['y', 'z'])}

        args = {"--url": "http://me.at.com",
                "--limit": '20',
                "--dbout": True,
                "--pretty-print": True}

        with nested(mock.patch("collector.collect_outgoing_urls"),
                    mock.patch("hyperlinks.send_to_mongodb")) as (
                collect_links,
                send_to_mongodb):
            collect_links.return_value = graph

            hyperlinks.cli(args)

            collect_links.assert_called_once_with("http://me.at.com", 20)
            send_to_mongodb.assert_called_once_with(graph)

            # assert
            out, _ = capsys.readouterr()
            dict_ = collector.url_to_info_as_pure_dict(graph)
            assert json.loads(out) == dict_

    def test_arg_parsing_failed(self):
        args = {"--limit": "20.0"}
        with pytest.raises(hyperlinks.InvalidArgumentValue):
            list(hyperlinks._parse_args(args,
                                       ("--limit", hyperlinks.get_limit)))

    def test_arg_parsing_ok(self):
        args = {"--limit": "20", "--url": "filter.be"}
        hyperlinks._parse_args(args, ("--limit", hyperlinks.get_limit,
                                      "--url", hyperlinks.get_url))

    def test_cli_failed_due_to_invalid_url(self, monkeypatch):
        # given
        args = {"--url": "com",
                "--limit": "20"}
        # when
        (msg, error_code), _ = get_exit_params(args, monkeypatch)
        # then
        assert msg == 'Invalid URL specified'
        assert error_code == 1


class TestArgumentValidation:

    def test_limit_value_parsing(self):
        are_valid(
            hyperlinks.get_limit,
            hyperlinks.InvalidArgumentValue,
            "20", True,
            "-20", False,
            "0", False,
            "1.6", False,
            "1e6", False,
            None, False)

    def test_get_url(self):
        are_valid(
            hyperlinks.get_url,
            hyperlinks.InvalidArgumentValue,
            "http://m.com", True,
            "http://m.com/", True,
            "https://rambler.ru/?downloadFrom=http://google.com", True,
            "http://", False,
            "m.c", False,
            "mo.co", False)


def get_exit_params(args, monkeypatch):
    "Helper to test cli function and capture exit error if happens"
    exit_params = []
    monkeypatch.setattr(hyperlinks, 'exit_cli',
                        Fn(capture_input, exit_params.append))
    hyperlinks.cli(args)
    return exit_params


def are_valid(fn, exception, *statements):
    """Accepts bunch of data for the validation
    For instance,

    >> is_valid(int, TypeError,
                10, True,
                "10", True,
                10.01, False,
                "10.2", False,
                False, False)
    """
    for args, is_valid in pairwise(statements):
        if not isinstance(args, (list, tuple)):
            args = (args,)
        if is_valid:
            fn(*args)
        else:
            with pytest.raises(exception):
                fn(*args)


def capture_input(fn, *args, **kwargs):
    fn(args)
    fn(kwargs)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    it = iter(iterable)
    return izip(it, it)
