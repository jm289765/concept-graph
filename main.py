from graphmanager import GraphManager
from api import GraphAPI
import threading


def main():
    g = GraphManager()
    # to reindex the search thing, call g.reindex() after deleting existing index

    api = GraphAPI(g)
    t = threading.Thread(target=api.start_server)
    t.start()
    # while True:
    #    x = input()
    #    todo: save db and exit if input tells you to


if __name__ == '__main__':
    main()
