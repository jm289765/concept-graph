import json

from networkx.readwrite import json_graph
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Tuple, Callable, Dict, List, Any, Union

from graphmanager import GraphManager


class GraphAPI:
    """
    api will have to update title/content, add, delete, link, unlink
add will need node type and starting content and starting connections
unlink will just need id

    update: node id, attribute, value
    add: node type, title, content, parent
    delete: node id
    link: parent id, child id, link type
    unlink: parent id, child id, two_way

    later, i'll need something to get json of a node + predecessors and successors, and
    something to get a list of all title attributes and/or a search function
    """

    def __init__(self, g: GraphManager):
        self.g: GraphManager = g

        self.get_handlers:Dict[str, Tuple[Callable[[Dict[str, List[str]]], Any], str]] = {
            "add": (self.add, "text/text"),  # todo: add should be a POST request
            "list-node-ids": (self.list_node_ids, "text/text"),
            "get-node": (self.get_node, "text/text"),
            "get-all-nodes": (self.get_all_nodes, "text/json"),
        }

        self.post_handlers:Dict[str, Tuple[Callable[[Dict[str, List[str]]], Any], str]] = {
            "add": (self.add, "text/text"),  # todo: add should be a POST request
            "link": (self.link, "text/text"),
        }

        self.put_handlers:Dict[str, Tuple[Callable[[Dict[str, List[str]]], Any], str]] = {
            "update": (self.update, "text/text"),
        }

        self.delete_handlers:Dict[str, Tuple[Callable[[Dict[str, List[str]]], Any], str]] = {
            "delete": (self.delete, "text/text"),
            "unlink": (self.unlink, "text/text"),
        }

        GraphAPIHandler.api = self
        self.server = HTTPServer(("localhost", 8080), GraphAPIHandler)

    def start_server(self):
        print(f"Starting server on port {self.server.server_port}...")
        self.server.serve_forever()

    def apply_func(self, keys:List[str], defaults:List[Union[str,int]], func:Callable, args:Dict[str,List[str]]) -> Any:
        """
        finds keys in args and uses them, else uses defaults. then applies func to those values.

        useful so that you don't need to check if args has a value or if you need to use a default.

        if a default is an int, the corresponding value in args will be converted to an int.

        :param keys: list of keys in the args dict
        :param defaults: default values for keys. must be in same order as keys.
        :param func: function to apply
        :param args: dict with keys and values
        :return: returns func's return value
        """
        app = []  # args to be given to func
        for k in range(len(keys)):
            if keys[k] in args:
                if type(defaults[k]) is int:
                    app.append(int(args[keys[k]][0]))
                elif type(defaults[k]) is bool:
                    app.append("true" == args[keys[k]][0].lower())
                else:
                    app.append(args[keys[k]][0])
            else:
                app.append(defaults[k])

        return func(*app)

    def add(self, args:Dict[str, List[str]]):
        """
        adds a node to the graph.
        :param args: can have keys "type", "title", "content", "parent"
        :return: node id
        """
        keys = ["type", "title", "content", "parent"]
        defaults = ["comment", "Untitled", "", 0]
        func = self.g.add_node
        return self.apply_func(keys, defaults, func, args)

    def delete(self, args):
        keys = ["id"]
        defaults = [0]
        func = self.g.add_node
        return self.apply_func(keys, defaults, func, args)

    def update(self, args):
        """

        :param args: can have keys "id", "attr", and "val". "attr" can be "title", "content", "type"
        :return:
        """
        keys = ["id", "attr", "val"]
        defaults = [0, None, None]
        func = self.g.set_node_attr
        return self.apply_func(keys, defaults, func, args)

    def link(self, args):
        keys = ["parent", "child", "two-way"]
        defaults = [0, 0, False]
        func = self.g.set_node_attr
        return self.apply_func(keys, defaults, func, args)

    def unlink(self, args):
        keys = ["parent", "child", "two-way"]
        defaults = [0, 0, False]
        func = self.g.set_node_attr
        return self.apply_func(keys, defaults, func, args)

    def list_node_ids(self, args):
        keys = []
        defaults = []
        func = lambda: self.g.nodes
        return self.apply_func(keys, defaults, func, args)

    def get_node(self, args):
        keys = ["id"]
        defaults = [0]
        func = lambda _id: self.g.nodes[_id]
        return self.apply_func(keys, defaults, func, args)

    def get_all_nodes(self, args):
        """

        :param args:
        :return: string containing json of all nodes
        """
        def make_json_nodes():
            nl_dat = json_graph.node_link_data(self.g)
            return json.dumps(nl_dat)
        keys = []
        defaults = []
        func = make_json_nodes
        return self.apply_func(keys, defaults, func, args)


class GraphAPIHandler(BaseHTTPRequestHandler):

    # todo: is there a way to do this without a class variable?
    # the __init__ function won't work for this class because of how BaseHTTPRequestHandler works.
    # but i need a specific instance of GraphAPI here
    api: GraphAPI = None

    def do_handle(self, handlers):
        try:
            req = urlparse(self.path)
            cmd = req.path[1:]
            args = parse_qs(req.query)
            func, mime_type = GraphAPIHandler.api.get_handlers.get(cmd, (None, "text/text"))

            if func is None:
                # todo: handle invalid request
                raise AttributeError(f"Invalid API request: {cmd}")

            res = func(args)
            self.send_response(200)
            self.send_header("Content-type", mime_type)
            self.end_headers()
            self.wfile.write(bytes(str(res), "utf-8"))
        except Exception as e:
            self.send_response(400)
            self.send_header("Content-type", "text/text")
            self.end_headers()
            self.wfile.write(bytes(f"An error occurred: {str(e)}", "utf-8"))
            # todo: better error logging

    def do_GET(self):
        self.do_handle(self.api.get_handlers)

    def do_POST(self):
        self.do_handle(self.api.post_handlers)

    def do_PUT(self):
        self.do_handle(self.api.put_handlers)

    def do_DELETE(self):
        self.do_handle(self.api.delete_handlers)
