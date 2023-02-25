from datetime import datetime
import json
from typing import List, Iterable
import database


def get_current_time():
    """
    :return: current UTC time as UNIX timestamp
    """
    return datetime.utcnow().timestamp()


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
    def nodes(self) -> Iterable:
        """
        :return: iterable of all node ids
        """
        return range(0, self.next_id)

    def nodes_list(self, ids: List) -> List:
        """
        :param ids: ids of nodes to return
        :return: list of node data items. a node data item is a dict with the node's attributes as keys.
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
        :return: list of edges that are connected to any of those nodes. an individual edge
        is a 2-element list: [sourceID, targetID]
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
        """
        :param ids: list of ids to get the json data for
        :return: json data with a list of data objects for the specified nodes, formatted as a string
        """
        return json.dumps(self.nodes_list(ids))

    def edges_json(self, ids: List):
        """
        :param ids: list of node ids to get edge data for
        :return: json data with a list of edges of the specified nodes, formatted as a string. an individual edge
        is a 2-element list: [sourceID, targetID]
        """
        return json.dumps(self.edges_list(ids))

    def graph_json(self, ids: List):
        """
        :param ids: list of ids to be included
        :return: json with "nodes" and "edges" attributes containing data as described in GraphManager.nodes_list and
        GraphManager.edges_list
        """
        ret = {"nodes": self.nodes_list(ids),
               "edges": self.edges_list(ids)}
        return json.dumps(ret)

    def neighbors_edges_json(self, _id: int):
        """
        gets all immediate successors and predecessors of a node, along with all edges connecting the node to those
        successors and predecessors.

        :param _id: id of node to get neighbors and edges of
        :return: string json with "nodes" and "edges" attributes. "nodes" is a list of node data objects. "edges"
        is a list of 2-element lists: [sourceID, targetID]
        """
        nodes = self.nodes_list(self.neighbor_ids(_id))
        edges = self.edges_list([_id])
        ret = {"nodes": nodes, "edges": edges}
        return json.dumps(ret)

    def successors(self, _id):
        """
        :param _id: id of the node whose successors you want
        :return: immediate children of node _id (list of ids)
        """
        return self.db.get_from_set(str(_id) + ".children")

    def predecessors(self, _id):
        """
        :param _id: id of the node whose predecessors you want
        :return: immediate parents of node _id (list of ids)
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

        current_time = get_current_time()
        attrs = {"type": "concept" if type == "root" and _id != 0 else type,
                 "title": title,
                 "content": content,
                 "tags": tags,
                 "id": _id,
                 "created": current_time,
                 "last_modified": current_time,
                 }

        # add node to database
        self.db.set_attrs(_id, attrs)
        self.db.incr("next_id")
        self.link_nodes(parent, _id)

        # if updating these, also update solr schema and self.reindex and self.set_node_attr
        search_attrs = {"type": "concept" if type == "root" and _id != 0 else type,
                        "title": title,
                        "content": content,
                        "tags": tags,
                        "id": _id}
        # add node to search index
        self.db.add_search_index(search_attrs)
        return _id

    def remove_node(self, _id: int):
        # remove all links to and from this node and add it to a "deleted" set in the db.
        # make sure the deleted node isn't automatically linked as a child of the root node.
        # when adding a new node, first check if there are any in the "deleted" set that
        # can be repurposed.
        # also, remember to remove this node's solr search index
        raise NotImplementedError("Function \"GraphManager.delete_node(self, _id)\" not implemented")

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

        add_edge(parent, child)

        if parent != 0:
            self.unlink_nodes(0, child)  # unlink_nodes won't error if this link doesn't exist

        if two_way:
            add_edge(child, parent)

        # later, this function will also add edge type attributes based on the type of the parent and child.
        # will have to make sure to update edge type when node types are updated in self.set_node_attr()

        # todo: make a way for concept nodes to be linked to root via explanation's dependencies??
        # or make concepts dependents of explanations instead of the other way around? make explanation
        # point to concept? or make explanations have two-way edges.

    def unlink_nodes(self, parent: int, child: int, two_way: bool = False):

        if parent == 0 and child == 0:
            raise ValueError("Cannot unlink node 0 from node 0.")

        # todo: if child has no other links, link it to root. same thing for two_way
        def remove_edge(_from, _to):
            self.db.remove_from_set(str(_to) + ".parents", _from)
            self.db.remove_from_set(str(_from) + ".children", _to)

        # todo: make sure parent and child are valid nodes

        if self.has_link(parent, child):
            remove_edge(parent, child)

        if two_way and self.has_link(child, parent):
            remove_edge(child, parent)

        # link to root if no other links exist
        if len(self.predecessors(child)) == 0:
            self.link_nodes(0, child)

    def set_node_attr(self, _id, attr, val):
        """
        :param _id: id of node whose attribute you want to set
        :param attr: which attribute to set. "type", "title", "tags", etc
        :param val: value to set the attribute to
        :return: id of updated node
        """
        # todo: louder error handling. return a message
        if attr is None:
            raise TypeError("set_node_attr: attr must not be None.")

        unchangeable = ["id", "created", "last_modified"]
        if attr in unchangeable:
            raise ValueError(f'set_node_attr: cannot set attributes {unchangeable}.')

        # make sure the node isn't the root and exists. relies on nodes not being deletable.
        if _id == 0:
            raise ValueError("set_node_attr: cannot set root node's attributes (node id 0).")

        if attr == "type" and val == "root":
            raise ValueError("set_node_attr: cannot set node's 'type' attribute to 'root'")

        if _id >= self.next_id:
            raise ValueError(f"set_node_attr: node {_id} does not exist.")

        if not self.db.has_attr(_id, attr):
            # todo: make this check against a list of allowed attributes instead?
            raise ValueError(f"set_node_attr: attribute '{attr}' does not exist in node '{_id}'.")

        self.db.set_attr(_id, attr, val)
        self.db.set_attr(_id, "last_modified", get_current_time())

        # if updating these, also update in self.add_node and self.reindex
        if attr in ["title", "type", "content", "tags"]:  # probably shouldn't hardcode this,
            # should get list of allowed attributes from the database instead
            self.db.update_search_index(_id, {attr: val})

        return _id

    def search(self, query):
        """
        :param query: search query
        :return: list of dicts {"id": x, "title": y} of some nodes that match the query
        """
        res = self.db.search_query(query)
        ret = []
        for doc in res:
            # remove "_version_", use str title instead of list
            ret.append({"id": doc["id"], "title": doc["title"][0]})
        # if we want to make a "get more results" thing, use res["numFound"] and res["start"]
        return json.dumps(ret)  # json.dumps should probably be in api.py

    def reindex(self):
        """
        will add all nodes to the search index. before you use this, make sure the search index data
        has been cleared from solr manually.

        :return: none
        """
        for n in self.nodes:
            try:
                ndat = self.db.get_attrs(n)
                sdat = {  # if updating these, also update in self.add_node and self.set_node_attr
                    "id": n,
                    "title": ndat["title"],
                    "type": ndat["type"],
                    "content": ndat["content"],
                    "tags": ndat["tags"]
                }
                self.db.add_search_index(sdat)
            except Exception as e:
                print(f"GraphManager.reindex(): Failed to index node {n}.")
