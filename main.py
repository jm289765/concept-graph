from time import sleep, localtime, strftime
from graphmanager import GraphManager
from api import GraphAPI, api_lock
import threading

graph_path = "data/graph.gml"

if __name__ == '__main__':
    g = GraphManager.load_from_file(graph_path)
    if not g:
        print("Graph not loaded from file, creating new graph...")
        g = GraphManager()

    api = GraphAPI(g)
    t = threading.Thread(target=api.start_server)
    t.start()
    while True:
        sleep(30)
        with api_lock:
            g.save_to_file(graph_path)
        print(f"Graph saved at {strftime('%H:%M:%S %Y-%m-%d', localtime())}")
