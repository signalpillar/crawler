# coding: utf-8
import mock

import collector
import contextlib

from collector import _normalize_url, new_url_info


def test_normalize_url():
    base = "http://x.com"
    uri = "/find"
    assert "http://x.com/find" == _normalize_url(base, uri)
    assert "http://x.com" == _normalize_url(base, base)

    assert "http://x.com" == _normalize_url("x.com")


def test_check_for_the_fragment_reference():
    assert True == collector._is_fragment_ref("#header")
    assert False == collector._is_fragment_ref("/find?#mark")
    assert False == collector._is_fragment_ref("http://ty.ru/")


def test_mimetype_guessing():
    import mimetypes
    actual = mimetypes.guess_type("http://at.com/file.exe")
    assert ('application/x-msdownload', None) == actual

    actual = mimetypes.guess_type("http://at.com/")
    assert (None, None) == actual

    actual = mimetypes.guess_type("http://at.com/index.html")
    assert ("text/html", None) == actual


def test_more_than_one_incomming():
    # given
    start_url = "http://today.sunday.in.ua/url1"

    route_table = {
        start_url:
        (200, 'text/html', content_with_urls(
            "http://first.com",
            "http://gogo.go",
            "http://greenlets.hm.let.me.try.us")),

        "http://first.com":
        (200, 'text/html', content_with_urls(
            start_url,
            "http://gogo.go")),

        "http://gogo.go":
        (200, 'text/html', content_with_urls(
            start_url,
            "http://from.go.go.go/index.jsp"))
    }

    # when
    graph = __collect_links(start_url, route_table, 4)
    # then
    assert graph == {
        start_url: new_url_info(
            incomming=[
                "http://first.com",
                "http://gogo.go"],
            outgoing=[
                "http://first.com",
                "http://gogo.go",
                "http://greenlets.hm.let.me.try.us"]),

        "http://first.com": new_url_info(
            incomming=[start_url],
            outgoing=[start_url,
                      "http://gogo.go"]),

        "http://gogo.go": new_url_info(
            incomming=[
                start_url,
                "http://first.com"],
            outgoing=[
                start_url,
                "http://from.go.go.go/index.jsp"])}


def test_limit_value_influence_on_collecting():
    # given
    start_url = "http://today.sunday.in.ua/url1"
    only_one = 1

    route_table = {
        start_url:
        (200, 'text/html', content_with_urls(
            "http://first.com",
            "http://gogo.go",
            "http://greenlets.hm.let.me.try.us")),

        "http://first.com":
        (200, 'text/html', content_with_urls(
            start_url,
            "http://gogo.go")),

        "http://gogo.go":
        (200, 'text/html', content_with_urls(
            "http://from.go.go.go/index.jsp"))
    }

    # when
    graph = __collect_links(start_url, route_table, only_one)
    # then
    assert graph == {
        start_url: new_url_info(
            incomming=[],
            outgoing=[
                "http://first.com",
                "http://gogo.go",
                "http://greenlets.hm.let.me.try.us"
            ])}


def test_cycle_references():
    # given
    start_url = "http://today.sunday.in.ua/url1"

    route_table = {
        start_url:
        (200, 'text/html', content_with_urls(
            "http://first.com")),

        "http://first.com":
        (200, 'text/html', content_with_urls(
            start_url))
    }

    # when
    graph = __collect_links(start_url, route_table, 11)

    # then
    assert graph == {start_url: new_url_info(incomming=["http://first.com"],
                                             outgoing=["http://first.com"]),
                     "http://first.com": new_url_info(incomming=[start_url],
                                                      outgoing=[start_url])}


def __collect_links(start_url, route_table, visit_limit):
    ''' Test how link collecting works in small sandbox

    @types: str, dict[str, tuple[int, str, str]], int -> dict[str, UrlInfo]

    @param route_table:
        routing table defines small subset of WEB
        that will be used for crawler testing
        each record in table is composed of:
        - URL to visit
        - status code and mime type for HEAD request
        - list of outgoing links included in visited page
    '''
    def get_from_route(url):
        record = route_table.get(url)
        code, content = 404, None
        if record:
            code, _, content = record
        response = mock.Mock()
        response.text = content
        response.status_code = code
        return response

    def head_from_route(url):
        r = route_table.get(url, (404, None, None))
        status_code, mimetype, _ = r
        response = mock.Mock()
        response.status_code = status_code
        response.headers.get.return_value = mimetype
        return response

    with contextlib.nested(
            mock.patch("requests.get", get_from_route),
            mock.patch("requests.head", head_from_route)):
        return collector.collect(start_url, visit_limit)


def content_with_urls(*urls):
    '''
    Make sample http document which contains URLs
    @types: list[str] -> str

    >> content_with_urls("url_a", "url_b", "url_c")
    <a href="url_a"></a>
    <a href="url_b"></a>
    <a href="url_c"></a>
    '''
    return "\n".join(
        ('<a href="%s"></a>' % u for u in urls)
    )


def test_has_required_mimetype():
    head = collector.HeadResponse(200, None)
    actual = collector._has_required_mime_type(head)
    assert False == actual

    head = collector.HeadResponse(200, 'text/html')
    actual = collector._has_required_mime_type(head)
    assert True == actual

    head = collector.HeadResponse(200, 'text/xml')
    actual = collector._has_required_mime_type(head)
    assert False == actual


def test_second():
    xs = (u for u in xrange(10))
    assert 1 == collector.second(xs)

    xs = []
    assert None == collector.second(xs)

    xs = {}
    assert None == collector.second(xs)

    xs = {1: 2, 2: 3}
    assert 2 == collector.second(xs)


def test_commong_by_index():
    r = collector._common_by_index(
        enumerate(xrange(10)),
        [(5, 'x'), (6, 'y')])
    assert [(5, 5), (6, 6)] == list(r)


def test_urls_parsed_from_html_content():
    content = '''

            <li>
            <a href="http://stackexchange.com/sites#science" class="more">
            more (7)
            <li><a href="http://stackapps.com" >Stack Apps</a></li>
            <li><a href="http://meta.stackoverflow.com"/> </a></li>
            <li><a href="http://meta.stackoverflow.com"/> </a></li>
            <li><a href="http://meta.stackoverflow.com"/> </a></li>
            <li><a href="http://area51.stackexchange.com">Area 51</a></li>
            <li><a href="http://careers.stackoverflow.com">Stackrs</a></li>
                '''
    expected = True, set(['http://stackexchange.com/sites#science',
                          'http://stackapps.com',
                          'http://meta.stackoverflow.com',
                          'http://area51.stackexchange.com',
                          'http://careers.stackoverflow.com'])
    assert expected == collector._parse_a_tag_urls((True, content))
