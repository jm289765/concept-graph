from graphmanager import GraphManager
from api import GraphAPI
import threading

graph_path = "data/graph.gml"

if __name__ == '__main__':
    g = GraphManager()

    api = GraphAPI(g)
    t = threading.Thread(target=api.start_server)
    t.start()
    while True:
        x = input()
        # todo: save db and exit if input tells you to
