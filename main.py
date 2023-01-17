from graphmanager import GraphManager
import networkx as nx


def draw_graph(g):
    import matplotlib.pyplot as plt

    nx.draw(g, pos=nx.planar_layout(g))
    plt.show()


if __name__ == '__main__':

    g = GraphManager()
    for x in range(1, 11):
        g.add_concept("A" * x)

    g.link_nodes(1, 5)
    g.link_nodes(2, 7)
    g.link_nodes(5, 7)
    g.link_nodes(7, 4)

    print()
    print(g.nodes)
    print(g.edges)

    nx.write_gml(g, "test.gml")

    draw_graph(g)
