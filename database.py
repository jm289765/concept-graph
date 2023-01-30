import json
import redis
import pysolr
from typing import Dict, Any


class Database:

    def __init__(self):

        # todo: add authentication to redis and solr

        # both of these will raise an error if their respective server isn't already running
        self.db = redis.Redis(decode_responses=True)
        self.solr = pysolr.Solr("http://localhost:8983/solr/graph_core/", always_commit=True)

    def set_attr(self, key, attr, val):
        self.db.hset(key, attr, val)

    def set_attrs(self, key, attrs: Dict[str, Any]):
        """

        :param key:
        :param attrs: dict with attribute names and values to set them to
        :return:
        """
        for pair in attrs.items():
            # using a loop because i have an old redis version. if i ever update it, i'll use the mapping param
            self.db.hset(key, pair[0], pair[1])

    def get_attr(self, key, attr):
        return self.db.hget(key, attr)

    def get_attrs(self, key):
        return self.db.hgetall(key)

    def has_attr(self, key, attr):
        return self.db.hexists(key, attr)

    def set_val(self, key, val):
        self.db.set(key, val)

    def get_val(self, key):
        return self.db.get(key)

    def incr(self, key, amt=1):
        self.db.incr(key, amt)

    def get_all_keys(self):
        return self.db.keys()

    def delete(self, key):
        self.db.delete(key)

    def exists(self, key):
        return self.db.exists(key)

    def add_to_set(self, key, val):
        self.db.sadd(key, val)

    def remove_from_set(self, key, val):
        self.db.srem(key, val)

    def get_from_set(self, key):
        return self.db.smembers(key)

    async def save_db(self):
        await self.db.bgsave()

    def add_search_index(self, data):
        """
        example: add_search_index([{"id": "1", "title": "here's some text"},
         {"id": "2", "title": "text associated with id 2"}])

        :param data: a Dict[str,str] with keys and values for search indexing terms. alternatively, a list
        of such dicts.

        data must include "id" and "title" keys. optional "content" and "tags" keys.
        :return: solr's json response, converted to a python object
        """
        # todo: make "tags" be stored as a list instead of a string
        return json.loads(self.solr.add(data if type(data) is list else [data]))

    def update_search_index(self, _id, new_data:dict):
        """
        :param _id: id of search item to update. int or str.
        :param new_data: dict, same as the one you would use for add_search_index. cannot be a list.
         does not need an "id" key. note that new_data's value will be changed in-place by this function.
        :return: False if solr gives an error, else True
        """

        for k in new_data.keys():
            # https://solr.apache.org/guide/6_6/updating-parts-of-documents.html#UpdatingPartsofDocuments-Example
            new_data[k] = {"set": new_data[k]}

        new_data["id"] = _id
        res = json.loads(self.solr.add(new_data))
        if res["responseHeader"]["status"] != 0:
            # todo: error handling, and figure out why status is 0. do same in self.search_query()
            #  but it looks like pysolr already takes care of this by raising an error
            return False
        return True

    def search_query(self, query:str) -> dict:
        """
        :param query: string to search for in solr search thing
        :return: results of solr search query (python object loaded from json).
        this is a dict with "numFound", "start", "numFoundExact", and "docs" keys
        """
        res = self.solr.search(query)
        return res.docs


if __name__ == "__main__":
    db = Database()
