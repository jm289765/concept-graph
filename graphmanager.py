import networkx as nx


class GraphManager(nx.DiGraph):

    def __init__(self, incoming_graph_data=None, **attr):
        super().__init__(incoming_graph_data, **attr)
        if 0 not in self.nodes:
            # root node
            # might be good to throw an error if there's no node 0 but there are other nodes
            self.add_node(0, next_id=1)
        elif "next_id" not in self.nodes[0]:
            raise AttributeError("Graph node 0 does not have 'next_id' attribute.")

    @property
    def next_id(self):
        x = self.nodes[0]["next_id"]
        self.nodes[0]["next_id"] += 1
        return x

    def add_node_type(self, type, title="", content="", parent=0) -> int:
        """
        :param type: "concept", "explanation", or "comment"
        :param title: title of this node
        :param content: content of this node
        :param parent: parent of this node
        :return: new node's id
        """
        _id = self.next_id
        self.add_node(_id, type=type, title=title, content=content)
        self.add_edge(parent, _id)
        return _id

    def add_concept(self, title: str, parent=0) -> int:
        return self.add_node_type("concept", title=title, parent=parent)

    def add_explanation(self, content: str, parent=0) -> int:
        return self.add_node_type("explanation", content=content, parent=parent)

    def add_comment(self, content: str, parent=0) -> int:
        return self.add_node_type("comment", content=content, parent=parent)

    def link_nodes(self, parent: int, child: int):
        self.add_edge(parent, child)
        # todo: make a way for concept nodes to be linked to root via explanation's dependencies??
        # or make concepts dependents of explanations instead of the other way around? make explanation point to concept?
        # or make explanations have two-way edges.
        if self.has_edge(0, child):
            self.remove_edge(0, child)

        # later, this function will also add edge type attributes based on the type of the parent and child

    def set_attr(self, _id, attr, val):
        # todo: better error handling
        if attr == "type":
            return False

        if _id not in self.nodes:
            return False

        if attr not in self.nodes[_id]:
            return False

        self.nodes[_id][attr] = val
        return True
