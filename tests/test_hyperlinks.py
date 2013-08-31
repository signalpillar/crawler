import hyperlinks
import pytest
from functools import partial as Fn
from itertools import izip


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


def test_get_url():
    are_valid(hyperlinks.get_url,
              hyperlinks.InvalidArgumentValue,
              "http://m.com", True,
              "http://m.com/", True,
              "https://rambler.ru/?downloadFrom=http://google.com", True,
              "http://", False,
              "m.c", False,
              "mo.co", True)


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
