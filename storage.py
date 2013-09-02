import pymongo
import pymongo.errors


class _BaseException(Exception):
    ''' Base exception class for the storage operations '''
    pass


class ConnectException(_BaseException):
    pass


class WriteException(_BaseException):
    pass


class GraphStorage:

    def write(self, graph):
        ''' Write graph to storage
        @types: dict[str, UrlInfo]
        @raise storage.WriteException:
        '''
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


class Mongo(GraphStorage):
    def __init__(self, client):
        '@types: pymongo.MongoClient'
        if not client:
            raise ValueError("Mongo client for storage is not specified")
        self._client = client

    def close(self):
        self._client.disconnect()

    def write(self, graph):
        '@types: dict[str, collector.UrlInfo]'
        db = self._client.graph_db
        collection = db.in_out_by_url
        collection.insert(
            ({"url": url,
              "incomming": list(incomming),
              "outgoing": list(outgoing)}
             for url, (incomming, outgoing) in graph.iteritems()))

    @classmethod
    def connect(cls, host, port):
        '@types: str, int -> MongoStorage'
        try:
            client = pymongo.MongoClient(host, port)
            return cls(client)
        except (pymongo.errors.ConnectionFailure,
                pymongo.errors.AutoReconnect), e:
            raise ConnectException(str(e))


def get_default():
    '@types: -> GraphStorage'
    # read data from configuration file
    return Mongo.connect("localhost", 27017)
