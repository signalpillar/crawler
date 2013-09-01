from fn import F
from collections import defaultdict, namedtuple
from itertools import repeat, izip, ifilterfalse
import logging
import requests
import urlparse
import re


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SUPPORTED_MIME_TYPES = ('text/html',)

UrlInfo = namedtuple("UrlInfo", ("incomming", "outgoing"))


def new_url_info(incomming=None, outgoing=None):
    '@types: set, set -> UrlInfo'
    return UrlInfo(set(incomming or ()),
                   set(outgoing or ()))


def collect_outgoing_urls(start_url, limit):
    '''
    Algorithm applied below is very similar to BFS
    '''
    logger.info("staring url with limit %s: %s" % (limit, start_url))
    info_by_url = defaultdict(new_url_info)
    parent_to_url_queue = [(None, _normalize_url(start_url))]
    while parent_to_url_queue and limit > 0:
        parent_url, url = parent_to_url_queue.pop(0)
        if url not in info_by_url:

            is_page_reached, urls = _get_page_urls(url)
            if is_page_reached:
                limit = limit - 1
                urls = ifilterfalse(_is_fragment_ref, urls)
                urls = map(F(_normalize_url, url), urls)

                info = info_by_url[url]
                info.outgoing.update(urls)
                if parent_url:
                    info.incomming.add(parent_url)
                candidates = urls
                parent_to_url_queue.extend(izip(repeat(url), candidates))
                logging.debug("OK     %s <-- %s" % (url, parent_url))
            else:
                logging.debug("FAILED     %s <-- %s" % (url, parent_url))
        else:
            logging.debug("ALREADY     %s <-- %s" % (url, parent_url))
            info = info_by_url[url]
            info.incomming.add(parent_url)
    return info_by_url


def _get_resource_head(url):
    '''
    Perform HEAD request to get headers by URL
    @types: str -> tuple[int, str?]
    '''
    r = requests.head(url)
    code, type_ = r.status_code, r.headers.get('content-type')
    if type_:
        # truncate charset information
        type_ = type_.split(';', 1)[0]
    logger.debug("HEAD: %s Code: %s, Content-Type: %s" % (url, code, type_))
    return code, type_


def _get_resource_content(url):
    '@types: str -> str?'
    r = requests.get(url)
    is_successful = r.status_code == requests.codes.ok
    logger.debug("GET: %s, Success ?: %s" % (url, is_successful))
    if is_successful:
        return r.text


def _is_fragment_ref(url):
    '@types: str -> bool'
    return url.startswith("#")


def _get_page_urls(url):
    ''' Get URLs on page by specified URL
    @types: str -> bool, list[str]
    @return: pair of flag whether page is reached at all
             and parsed URLs from it'''
    is_page_reached = False
    urls = []
    status_code, mime_type = _get_resource_head(url)
    skip = mime_type and mime_type not in SUPPORTED_MIME_TYPES
    if not skip:
        content = _get_resource_content(url)
        if content:
            urls = _parse_a_tag_urls(content)
            is_page_reached = True
    return is_page_reached, urls


A_TAG_HREF_RE = re.compile("<a\s+.*?href=\"(.*?)\"")


def _parse_a_tag_urls(content):
    '@types: str -> list[str]'
    return set(A_TAG_HREF_RE.findall(content))


def _normalize_url(url, uri=None):
    '@types: str, str? -> str'
    result = uri or url
    if uri and not urlparse.urlparse(uri).netloc:
        result = urlparse.urljoin(url, uri)
    if not urlparse.urlparse(result).scheme:
        result = "http://%s" % result
    return result
