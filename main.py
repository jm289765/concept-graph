from graphmanager import GraphManager
from api import GraphAPI
import threading


def main():
    g = GraphManager()
    # to reindex the search thing, call g.reindex() after deleting existing index

    reindex = False
    if reindex:
        print("Reindexing solr...")
        g.reindex()
        print("Done reindexing!")
    else:
        api = GraphAPI(g)
        t = threading.Thread(target=api.start_server)
        t.start()


if __name__ == '__main__':
    main()
