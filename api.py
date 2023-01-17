import socketserver
import urllib.parse
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from typing import Tuple, Callable, Dict, List, Any

from graphmanager import GraphManager

class GraphAPI:
    """
    api will have to update title/content, add, delete, link, unlink
add will need node type and starting content and starting connections
unlink will just need id
    """

    def __init__(self, g: GraphManager):
        self.g: GraphManager = g
        self.server = HTTPServer(("localhost", 8080), partial(GraphAPIHandler, self))

    def start_server(self):
        self.server.serve_forever()

    def update(self, args):
        """
        does not check that _id is in self.g
        :return: nothing
        """
        _id, attr, val = args["id"], args["attr"], args["val"]
        self.g.set_attr(_id, attr, val)

    def add_node(self, args):
        # node_type, title="", content="", parent=0 =
        node_type, title, content, parent = args["type"], args["title"], args["content"], int(args["parent"])
        self.g.add_node_type(node_type, title, content, parent)
        print(self.g.nodes)


class GraphAPIHandler(BaseHTTPRequestHandler):

    def __init__(self, api: GraphAPI, request: bytes, client_address: Tuple[str, int], server: socketserver.BaseServer):
        super().__init__(request, client_address, server)
        self.api = api

        self.get_handlers:Dict[str, Callable[[Dict[str, List[str]]], Any]] = {
            "add": self.api.add_node,  # todo: add should be a POST request
        }

        self.put_handlers:Dict[str, Callable[[Dict[str, List[str]]], Any]] = {
            "update": self.api.update,
        }
        print("init done")

    def do_GET(self):
        print("doing GET")
        req = urlparse(self.path)
        cmd = req.path[1:]
        args = parse_qs(req.query)
        func = self.get_handlers.get(cmd, None)

        if func is None:
            # todo: handle invalid request
            pass

        func(args)

        print(req)
        print(cmd)
        print(args)
