from fn import F
from collections import defaultdict, namedtuple
from itertools import repeat, izip
import logging


logging.basicConfig(levle=logging.DEBUG)


UrlInfo = namedtuple("UrlInfo", ("incomming", "outgoing"))


def collect_outgoing_urls(start_url, limit):
    info_by_url = defaultdict(F(UrlInfo, set(), set()))
    parent_to_url_queue = [(None, start_url)]
    while parent_to_url_queue and limit > 0:
        parent_url, url = parent_to_url_queue.pop(0)
        if url not in info_by_url:
            limit = limit - 1
            outgoing_urls = get_page_urls(url)
            info = info_by_url[url]
            info.outgoing.update(outgoing_urls)
            if parent_url:
                info.incomming.add(parent_url)
            candidates = outgoing_urls[:limit]
            parent_to_url_queue.extend(izip(repeat(url), candidates))
    return info_by_url


def get_page_urls(url):
    return []


def parse_a_tag_urls(content):
    pass


def is_non_resource_url(url):
    pass


def normalize_url(url, uri):
    pass
