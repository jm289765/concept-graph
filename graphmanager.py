import json
from typing import List
import database


class GraphManager:
    # todo: maybe don't hardcode this? or put it somewhere else, it's more of an api thing
    MAX_LIST_SIZE = 100  # for nodes_list() and edges_list(). edges_list uses 10 times this

    def __init__(self):
        """
        GraphManager provides functions to interact with the graph
        """
        self.db = database.Database()
        # todo: handle invalid redis connection
        if not self.db.exists("next_id"):
            self.db.set_val("next_id", 0)
            self.add_node("root", "root", "", "")

    @property
    def next_id(self):
        """
        :return: the next node ID to be used
        """
        x = int(self.db.get_val("next_id"))
        return x

    @property
    def nodes(self):
        """
        :return: list of node ids
        """
        return range(0, self.next_id)

    def nodes_list(self, ids: List) -> List:
        """
        :param ids: ids of nodes to return
        :return: list of node data items. a node data item is a dict with the node's attributes
        """
        ret = []
        for x in ids:
            n = self.db.get_attrs(x)
            ret.append(n)
            if len(ret) >= GraphManager.MAX_LIST_SIZE:
                break
        return ret

    def edges_list(self, ids: List) -> List:
        """
        edges attached to earlier ids are first. if the max list size is a problem, put more important nodes
        at the beginning of the ids list.

        :param ids: ids of nodes to return
        :return: list of edges that are connected to any of those nodes
        """
        # todo: add a way to only include edges that are between two of the nodes listed in the ids param
        ret = []
        for _id in ids:
            parents = self.db.get_from_set(str(_id) + ".parents")
            children = self.db.get_from_set(str(_id) + ".children")
            ret += [[int(p), _id] for p in parents]
            ret += [[_id, int(c)] for c in children]
            if len(ret) >= GraphManager.MAX_LIST_SIZE * 5:
                break
        return ret

    def nodes_json(self, ids: List):
        return json.dumps(self.nodes_list(ids))

    def edges_json(self, ids: List):
        return json.dumps(self.edges_list(ids))

    def graph_json(self, ids: List):
        """
        :param ids: list of ids to be included
        :return: json with "nodes" and "edges" attributes
        """
        ret = {"nodes": self.nodes_list(ids),
               "edges": self.edges_list(ids)}
        return json.dumps(ret)

    def neighbors_edges_json(self, _id: int):
        nodes = self.nodes_list(self.neighbor_ids(_id))
        edges = self.edges_list([_id])
        ret = {"nodes": nodes, "edges": edges}
        return json.dumps(ret)

    def successors(self, _id):
        """
        :param _id: id of the node whose successors you want
        :return: immediate children of node _id
        """
        return self.db.get_from_set(str(_id) + ".children")

    def predecessors(self, _id):
        """
        :param _id: id of the node whose predecessors you want
        :return: immediate parents of node _id
        """
        return self.db.get_from_set(str(_id) + ".parents")

    def neighbor_ids(self, _id: int):
        """
        :param _id: id of node to list neighbors of
        :return: list of neighbors of node 'id'. includes the node itself along with successors and predecessors.
        """
        return [_id, *self.successors(_id), *self.predecessors(_id)]

    def add_node(self, type="default", title="", content="", tags="", parent=0) -> int:
        """
        :param type: "concept", "explanation", "comment", etc
        :param title: title of this node
        :param content: content of this node
        :param tags: node's tags. comma-separated string.
        :param parent: parent of this node
        :return: new node's id
        """
        _id = self.next_id

        attrs = {"type": "concept" if type == "root" and _id != 0 else type,
                 "title": title,
                 "content": content,
                 "tags": tags,
                 "id": _id}

        self.db.set_attrs(_id, attrs)
        self.db.incr("next_id")
        self.link_nodes(parent, _id)
        return _id

    def remove_node(self, _id: int):
        if not self.db.exists(_id):
            return False

        if _id == 0:
            raise ValueError("Cannot delete root node (node ID 0).")

        for n in self.predecessors(_id):
            self.unlink_nodes(n, _id)

        for n in self.successors(_id):
            self.unlink_nodes(_id, n)
            # todo: if successor has no other links, link it to root

        # things like e.g. self.nodes rely on nodes not being deletable. so it stays in the db, just unlinked
        # self.db.delete(_id)

    def has_link(self, parent: int, child: int):
        # todo: make get_from_set return ints instead of strings. needing to convert child to a
        #  string is a database implementation detail, shouldn't be necessary to consider it here
        #  same thing with self.next_id needing to convert str to int
        return str(child) in self.db.get_from_set(str(parent) + ".children")

    def link_nodes(self, parent: int, child: int, two_way: bool = False):
        # removal of edge to root node has to happen first
        # in case someone calls link_nodes with the root node

        def add_edge(_from, _to):
            self.db.add_to_set(str(_to) + ".parents", _from)
            self.db.add_to_set(str(_from) + ".children", _to)

        # todo: make sure parent and child are valid nodes

        self.unlink_nodes(0, child)  # unlink_nodes won't error if this link doesn't exist

        add_edge(parent, child)

        if two_way:
            add_edge(child, parent)

        # later, this function will also add edge type attributes based on the type of the parent and child.
        # will have to make sure to update edge type when node types are updated in self.set_node_attr()

        # todo: make a way for concept nodes to be linked to root via explanation's dependencies??
        # or make concepts dependents of explanations instead of the other way around? make explanation
        # point to concept? or make explanations have two-way edges.

    def unlink_nodes(self, parent: int, child: int, two_way: bool = False):

        # todo: if child has no other links, link it to root. same thing for two_way
        def remove_edge(_from, _to):
            self.db.remove_from_set(str(_to) + ".parents", _from)
            self.db.remove_from_set(str(_from) + ".children", _to)

        # todo: make sure parent and child are valid nodes

        if self.has_link(parent, child):
            remove_edge(parent, child)

        if two_way and self.has_link(child, parent):
            remove_edge(child, parent)

    def set_node_attr(self, _id, attr, val):
        """
        :param _id: id of node whose attribute you want to set
        :param attr: which attribute to set. "type", "title", "tags", etc
        :param val: value to set the attribute to
        :return: True if the attribute is updated, False or error otherwise
        """
        # todo: louder error handling. return a message
        if attr is None or val is None:
            return False

        if attr == "id":
            return False

        # make sure the node isn't the root and exists. relies on nodes not being deletable.
        if _id == 0 or _id >= self.next_id:
            return False

        if not self.db.has_attr(_id, attr):
            # todo: make this check against a list of allowed attributes instead?
            return False

        if attr == "tag":
            # todo: handle tag formatting if necessary.
            pass

        self.db.set_attr(_id, attr, val)
        return True

    def delete_node(self, _id):
        # remove all links to and from this node and add it to a "deleted" set in the db.
        # make sure the deleted node isn't automatically linked as a child of the root node.
        # when adding a new node, first check if there are any in the "deleted" set that
        # can be repurposed.
        raise NotImplementedError("Function \"GraphManager.delete_node(self, _id)\" not implemented")
