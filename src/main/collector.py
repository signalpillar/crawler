from fn.iters import partition
from collections import defaultdict, namedtuple
from itertools import repeat, izip, ifilterfalse, starmap, tee, imap
import logging
import logging.config
import requests
import urlparse
import re
import grequests


#logging.config.fileConfig("logging.ini")
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("collector")

SUPPORTED_MIME_TYPES = ('text/html',)

UrlInfo = namedtuple("UrlInfo", ("incomming", "outgoing"))


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


def collect(start_url, limit):
    ''' Collect recursively incoming and outgoing information
    starting from specified URL

    Algorithm applied below is very similar to BFS
    @types: str, int -> dict[str, UrlInfo]
    '''
    logger.info("staring url with limit %s: %s" % (limit, start_url))
    info_by_url = defaultdict(new_url_info)
    parent_to_url_queue = [(None, _normalize_url(start_url))]
    while parent_to_url_queue and limit > 0:

        urls_to_process = parent_to_url_queue[:limit]
        del parent_to_url_queue[:limit]

        results = _get_outgoings([url for _, url in urls_to_process])
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
                logging.debug("OK     %s <-- %s" % (url, parent_url))
            else:
                logging.debug("FAILED     %s <-- %s" % (url, parent_url))
    return info_by_url


HeadResponse = namedtuple("HeadResponse", ("status_code", "mime_type"))


def _get_resource_head(url):
    '''
    Perform HEAD request to get headers by URL
    @types: str -> HeadResponse
    '''
    r = requests.head(url)
    code, type_ = r.status_code, r.headers.get('content-type')
    if type_:
        # truncate charset information
        type_ = type_.split(';', 1)[0]
    logger.debug("HEAD: %s Code: %s, Content-Type: %s" % (url, code, type_))
    return HeadResponse(code, type_)


def _get_resource_content(url, head):
    ''' Get content based on passed URL and its head
    @types: str, HeadResponse -> tuple[bool, str?]'''
    mime_type = head and head.mime_type
    skip = mime_type and mime_type not in SUPPORTED_MIME_TYPES
    is_successful, content = False, None
    if not skip:
        r = requests.get(url)
        is_successful = r.status_code == requests.codes.ok
        logger.debug("GET: %s, Success ?: %s" % (url, is_successful))
        if is_successful:
            content = r.text
    return is_successful, content


def _is_fragment_ref(url):
    '@types: str -> bool'
    return url.startswith("#")


def _get_outgoings(urls):
    ''' Get outgoing URLs for each specified URL
    @types: iterable[str] -> iterable[bool, list[str]]
    @return: pair of flag whether page is reached at all
             and parsed URLs from it'''
    urls_for_heads, urls_for_contents = tee(urls)
    heads = imap(_get_resource_head, urls_for_heads)
    contents = starmap(_get_resource_content, izip(urls_for_contents, heads))
    return imap(_parse_a_tag_urls, contents)


A_TAG_HREF_RE = re.compile("<a\s+.*?href=\"(.*?)\"")


def _parse_a_tag_urls(content_info):
    '@types: tuple[bool, str] -> tuple[bool, set[str]]'
    is_page_reached, content = content_info
    return (is_page_reached,
            set(is_page_reached
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
