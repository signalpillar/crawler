import pytest
import mock

from itertools import izip
from functools import partial as Fn
from contextlib import nested

import hyperlinks


def test_cli_flow_in_general():
    "Check whether all required steps are perfomed"
    # given
    graph = {'key': 'value'}

    args = {"--url": "http://me.at.com",
            "--limit": "20",
            "--dbout": True}

    with nested(mock.patch("collector.collect_outgoing_urls"),
                mock.patch("hyperlinks.print_graph"),
                mock.patch("hyperlinks.send_to_mongodb")) as (
            collect_links,
            print_graph,
            send_to_mongodb):
        collect_links.return_value = graph

        hyperlinks.cli(args)

        collect_links.assert_called_once_with("http://me.at.com", 20)
        print_graph.assert_called_once_with(graph, None)
        send_to_mongodb.assert_called_once_with(graph)


def test_arg_parsing_failed():
    args = {"--limit": "20.0"}
    with pytest.raises(hyperlinks.InvalidArgumentValue):
        list(hyperlinks.parse_args(args, ("--limit", hyperlinks.get_limit)))


def test_arg_parsing_ok():
    args = {"--limit": "20", "--url": "filter.be"}
    hyperlinks.parse_args(args, ("--limit", hyperlinks.get_limit,
                                 "--url", hyperlinks.get_url))


def test_cli_failed_due_to_invalid_url(monkeypatch):
    # given
    args = {"--url": "com",
            "--limit": "20"}
    # when
    (msg, error_code), _ = get_exit_params(args, monkeypatch)
    # then
    assert msg == 'Invalid URL specified'
    assert error_code == 1


def test_cli_flow_with_correct_args(monkeypatch):
    "Test arguments based on passed arguments"
    # given
    args = {"--url": "http://fake.com",
            "--limit": "20"}

    # when
    exit_params = get_exit_params(args, monkeypatch)
    # then
    assert exit_params == []


def test_limit_value_parsing():
    are_valid(hyperlinks.get_limit,
              hyperlinks.InvalidArgumentValue,
              "20", True,
              "-20", False,
              "0", False,
              "1.6", False,
              "1e6", False,
              None, False)


def test_get_url():
    are_valid(hyperlinks.get_url,
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
