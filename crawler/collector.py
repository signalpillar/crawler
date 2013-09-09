from fn.iters import partition, nth
from fn import F

from functools import partial
from collections import defaultdict, namedtuple
from itertools import repeat, izip, ifilterfalse, imap, ifilter

import requests
import grequests

import re
import urlparse
import logging
import logging.config


logging.config.fileConfig("logging.ini")
logger = logging.getLogger("collector")

SUPPORTED_MIME_TYPES = ('text/html',)

UrlInfo = namedtuple("UrlInfo", ("incomming", "outgoing"))


def collect(start_url, limit):
    do_heads = partial(do_request, requests.head, list)
    do_gets = partial(do_request, requests.get, list)
    return _collect(start_url, limit, do_heads, do_gets)


def pcollect(start_url, limit):
    pdo_heads = partial(do_request, grequests.head, grequests.map)
    pdo_gets = partial(do_request, grequests.get, grequests.map)
    return _collect(start_url, limit, pdo_heads, pdo_gets)


def _collect(start_url, limit, do_head_fn, do_get_fn):
    ''' Collect recursively incoming and outgoing information
    starting from specified URL

    @note: If one of the pages cannot be reached - limit doesn't decrease
    @note: Algorithm applied below is very similar to BFS

    @types: str, int, callable, callable -> dict[str, UrlInfo]

    @type do_head_fn: (iterable[str] -> iterable[requests.Response])
    @param do_head_fn: function takes iterable of URLs and returns list
                       of Response for HEAD requests
    @type do_get_fn: (iterable[str] -> iterable[requests.Response])
    @param do_get_fn: function takes iterable of URLs and returns list
                      of responses for GET requests
    '''
    logger.info("staring url with limit %s: %s" % (limit, start_url))
    info_by_url = defaultdict(new_url_info)
    parent_to_url_queue = [(None, _normalize_url(start_url))]
    while parent_to_url_queue and limit > 0:

        urls_to_process = parent_to_url_queue[:limit]
        del parent_to_url_queue[:limit]

        urls = (url for _, url in urls_to_process)
        results = _get_outgoings(urls, do_head_fn, do_get_fn)
        results = izip(urls_to_process, results)

        for result in results:
            (parent_url, url), (is_page_reached, urls) = result
            if is_page_reached:
                limit = limit - 1
                urls = ifilterfalse(_is_fragment_ref, urls)
                urls = [_normalize_url(url, u) for u in urls]

                info = info_by_url[url]
                info.outgoing.update(urls)

                parent_url and info.incomming.add(parent_url)

                candidates, visited = partition(info_by_url.has_key, urls)

                [info_by_url.get(u).incomming.add(url) for u in visited]

                parent_to_url_queue.extend(izip(repeat(url), candidates))
                logging.debug("OK         %s <-- %s" % (url, parent_url))
            else:
                logging.debug("FAILED     %s <-- %s" % (url, parent_url))
    return info_by_url


def _get_outgoings(urls, do_head_fn, do_get_fn):
    ''' Get outgoing URLs for each specified URL

    Approach used here is
    1) determine wheter URL refers resource of required type,
       in our case it is 'text/html'
    2) get content only for the URLs where content-type is absent or valid
    3) return result in such order so it will correspond to the order of
       asked URLs

    @types: iterable[str], callable, callable -> iterable[bool, list[str]]
    @return: list of pairs where first is flag whether page is reached
             and parsed URLs from it'''
    urls = tuple(urls)

    # get head information for all passed URLs
    heads = do_head_fn(urls)
    heads = imap(_parse_head_response, heads)

    # get content for only those URLs where head information is appropriate
    n_heads = ifilter(F(_has_required_mime_type) << second, enumerate(heads))
    n_urls = list(_common_by_index(enumerate(urls), n_heads))

    urls_with_outgoings = map(second, n_urls)
    contents = do_get_fn(urls_with_outgoings)
    outgoings = imap(F(_parse_a_tag_urls) << _parse_get_response, contents)

    outgoings_per_n_url = dict(izip(urls_with_outgoings, outgoings))
    # restore order of results according to passed URLs
    return (outgoings_per_n_url.get(u, (False, None)) for u in urls)


def do_request(request_fn, realize_fn, urls):
    '@types: callable, callable, list[str] -> list[requests.Response]'
    return realize_fn((request_fn(u) for u in urls))


def _parse_head_response(r):
    '@types: requests.Response -> HeadResponse'
    code = None
    type_ = None
    if r:
        code, type_ = r.status_code, r.headers.get('content-type')
        if type_:
            # truncate charset information
            type_ = type_.split(';', 1)[0]
    return HeadResponse(code, type_)


def _parse_get_response(r):
    '@types: requests.Response -> tuple[bool, str]'
    if r:
        is_successful = r.status_code == requests.codes.ok
        content = is_successful and r.text or None
        return is_successful, content
    return False, None


HeadResponse = namedtuple("HeadResponse", ("status_code", "mime_type"))


def _is_fragment_ref(url):
    '@types: str -> bool'
    return url.startswith("#")


def _has_required_mime_type(head):
    '@types: HeadResponse -> bool'
    return not head or head.mime_type in SUPPORTED_MIME_TYPES


def second(xs):
    '@types: iterable[T] -> T?'
    return nth(xs, 1)


def _common_by_index(dst, src):
    '@types: iterable[[int, A]], iterable[[int, B]] -> iterable[[int, A]]'
    dst_dict = dict(dst)
    src_dict = dict(src)
    for idx in src_dict:
        if idx in dst_dict:
            yield idx, dst_dict[idx]


A_TAG_HREF_RE = re.compile("<a\s+.*?href=\"(.*?)\"")


def _parse_a_tag_urls(content_info):
    '@types: tuple[bool, str] -> tuple[bool, set[str]]'
    is_page_reached, content = content_info
    return (is_page_reached,
            set((is_page_reached and content)
                and A_TAG_HREF_RE.findall(content)
                or ()))


def _normalize_url(url, uri=None):
    '@types: str, str? -> str'
    result = uri or url
    if uri and not urlparse.urlparse(uri).netloc:
        result = urlparse.urljoin(url, uri)
    if not urlparse.urlparse(result).scheme:
        result = "http://%s" % result
    return result


def new_url_info(incomming=None, outgoing=None):
    '@types: set, set -> UrlInfo'
    return UrlInfo(set(incomming or ()),
                   set(outgoing or ()))


def url_to_info_as_pure_dict(graph):
    '@types: dict[str, UrlInfo] -> dict[str, dict[str, list]]'
    return dict(
        (
            (k, {"incomming": list(v.incomming), "outgoing": list(v.outgoing)})
            for k, v in graph.iteritems()
        )
    )
