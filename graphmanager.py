import networkx as nx


class GraphManager(nx.DiGraph):

    def __init__(self, incoming_graph_data=None, **attr):
        if "next_id" in attr:
            super().__init__(incoming_graph_data, **attr)
        else:
            super().__init__(incoming_graph_data, next_id=0, **attr)

        if 0 not in self.nodes:
            # root node
            # might be good to throw an error if there's no node 0 but there are other nodes

            # right now, this makes the root node link to itself. this makes it easy to catch
            # graph search algorithms that don't handle loops, so i'll leave it
            self.add_node("root", title="root", content="")
        elif self.nodes[0].get("type", "no type attribute") != "root":
            raise ValueError("Graph node 0 does not have node type 'root'.")

    @property
    def next_id(self):
        x = self.graph["next_id"]
        self.graph["next_id"] += 1
        return x

    def add_node(self, type="default", title="", content="", parent=0) -> int:
        """
        :param type: "concept", "explanation", or "comment"
        :param title: title of this node
        :param content: content of this node
        :param parent: parent of this node
        :return: new node's id
        """
        _id = self.next_id
        super().add_node(_id, type=type, title=title, content=content)
        self.link_nodes(parent, _id)
        return _id

    def remove_node(self, _id):
        if _id not in self.nodes:
            return False

        if _id == 0:
            raise ValueError("Cannot delete node 0")

        for n in self.successors(_id):
            # todo: if successor has no other links, link it to root
            pass

        super().remove_node(_id)

    def link_nodes(self, parent: int, child: int, two_way: bool = False):
        # removal of edge to root node has to happen first
        # in case someone calls link_nodes with the root node
        if self.has_edge(0, child):
            self.remove_edge(0, child)

        self.add_edge(parent, child)

        if two_way:
            self.add_edge(child, parent)
        # todo: make a way for concept nodes to be linked to root via explanation's dependencies??
        # or make concepts dependents of explanations instead of the other way around? make explanation point to concept?
        # or make explanations have two-way edges.

        # later, this function will also add edge type attributes based on the type of the parent and child

    def unlink_nodes(self, parent: int, child: int, two_way: bool = False):

        # todo: if child has no other links, link it to root. same thing for two_way
        if self.has_edge(parent, child):
            self.remove_edge(parent, child)

        if two_way:
            if self.has_edge(child, parent):
                self.remove_edge(child, parent)

    def set_node_attr(self, _id, attr, val):
        # todo: louder error handling. return a message
        if attr is None or val is None:
            return False

        if attr == "type":
            return False

        if _id not in self.nodes:
            return False

        if attr not in self.nodes[_id]:
            return False

        self.nodes[_id][attr] = val
        return True
