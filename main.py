from graphmanager import GraphManager
from api import GraphAPI
import networkx as nx


def draw_graph(g):
    import matplotlib.pyplot as plt

    nx.draw(g, pos=nx.planar_layout(g))
    plt.show()


def run_parser(g):
    api = GraphAPI(g)
    api.start_server()
    while True:
        try:
            inp = input("> ").split(" ")
            if len(inp) == 0:
                continue
            cmd = inp[0]
            args = inp[1:]

            if cmd == "exit":
                break
            elif cmd == "nodes":
                print(g.nodes)
            elif cmd == "edges":
                print(g.edges)
            elif cmd == "get":
                node = int(args[0])
                print(g.nodes[node])
            elif cmd == "draw":
                draw_graph(g)
            elif cmd == "link":
                parent, child = int(args[0]), int(args[1])
                g.link_nodes(parent, child)
                print("Done")
            elif cmd == "save":
                file = args[0]
                nx.write_gml(g, file)
            elif cmd == "load":
                file = args[0]

                def destringizer(s:str):
                    if s.isnumeric():
                        return int(s)
                    return s

                g = GraphManager(nx.read_gml(file, destringizer=destringizer))
            elif cmd == "add":
                type, title, content, parent = args[0], args[1], args[2], int(args[3])
                api.add_node(type, title, content, parent)
            elif cmd == "update":
                _id, attr, val = int(args[0]), args[1], args[2]
                api.update(_id, attr, val)

        except Exception as e:
            import traceback
            traceback.print_exc()


if __name__ == '__main__':

    g = GraphManager()
    run_parser(g)
