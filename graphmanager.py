import json
from typing import List
import networkx as nx
import os.path


def load_from_file(file_name):
    if os.path.exists(file_name):
        g = nx.readwrite.read_gml(file_name, label=None)
        return GraphManager(g)

    return False


class GraphManager(nx.DiGraph):

    load_from_file = load_from_file

    # todo: maybe don't hardcode this? or put it somewhere else, it's more of an api thing
    MAX_LIST_SIZE = 100  # for nodes_list() and edges_list(). edges_list uses 10 times this

    def __init__(self, incoming_graph_data=None, **attr):
        if "next_id" in attr:  # could replace "next_id" with self.number_of_nodes
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

    def nodes_list(self, ids: List):
        """
        :param ids: ids of nodes to return
        :return: list of node data items. a node data item is a dict with the node's attributes
        """
        ret = []
        for x in (ids if len(ids) > 0 else self.nodes):
            n = self.nodes[x]
            n["id"] = x  # already set when the node is added,
            # but networkx's generate_gml and read_gml don't let me keep an id attribute in nodes
            ret.append(n)
            if len(ret) >= GraphManager.MAX_LIST_SIZE:
                break
        return ret

    def edges_list(self, ids: List):
        """
        :param ids: ids of nodes to return
        :return: list of edges that are connected to any of those nodes
        """
        # list of all edges attached to the given ids
        # if this was a graph instead of a digraph, only self.edges would be needed
        out_e = self.edges(nbunch=ids)
        out_e = out_e if len(out_e) <= GraphManager.MAX_LIST_SIZE * 5 else out_e[:500]
        in_e = self.in_edges(nbunch=ids)
        in_e = in_e if len(in_e) <= GraphManager.MAX_LIST_SIZE * 5 else in_e[:500]
        ret = [*out_e, *in_e]
        return ret

    def nodes_json(self, ids: List):
        return json.dumps(self.nodes_list(ids))

    def edges_json(self, ids: List):
        return json.dumps(self.edges_list(ids))

    def graph_json(self, ids: List):
        ret = {"nodes": self.nodes_list(ids),
               "edges": self.edges_list(ids)}
        return json.dumps(ret)

    def neighbors_edges_json(self, _id:int):
        nodes = self.nodes_list(self.neighbor_ids(_id))
        edges = self.edges_list([_id])
        ret = {"nodes": nodes, "edges": edges}
        return json.dumps(ret)

    def neighbor_ids(self, _id:int):
        """
        :param _id: id of node to list neighbors of
        :return: list of neighbors of node 'id'. includes the node itself, successors, and predecessors.
        """
        return [_id, *self.successors(_id), *self.predecessors(_id)]

    def add_node(self, type="default", title="", content="", tags="", parent=0) -> int:
        """
        :param type: "concept", "explanation", or "comment"
        :param title: title of this node
        :param content: content of this node
        :param tags: node's tags. comma-separated string.
        :param parent: parent of this node
        :return: new node's id
        """
        _id = self.next_id

        typ = type
        if typ == "root" and _id != 0:
            typ = "concept"

        super().add_node(_id, type=typ, title=title, content=content, tags=tags, id=_id)
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

        if attr == "id":
            return False

        if _id == 0 or _id not in self.nodes:
            return False

        if attr not in self.nodes[_id]:
            # todo: make this check against a list of allowed attributes instead?
            return False

        if attr == "tag":
            # todo: handle tag formatting if necessary.
            pass

        self.nodes[_id][attr] = val
        return True

    def save_to_file(self, file_name:str):
        """
        saves this graph to the file specified by fileName

        :param file_name: file to save to
        :return: nothing
        """

        with open(file_name + ".new", "w+") as f:
            f.write("\n".join(nx.readwrite.generate_gml(self)))

        # make a backup of the old version of the graph
        if os.path.exists(file_name):
            if os.path.exists(file_name + ".old"):
                os.remove(file_name + ".old")
            os.rename(file_name, file_name + ".old")

        os.rename(file_name + ".new", file_name)
