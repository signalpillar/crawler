import collector


def test_simple_collection():
    graph = collector.collect_outgoing_urls("google.com", 1)
    print graph
    assert graph == {"url1": "x"}
