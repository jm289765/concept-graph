import redis
from typing import Dict, Any


class Database:

    def __init__(self):
        self.db = redis.Redis(decode_responses=True)

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


if __name__ == "__main__":
    db = Database()
    db.set_attr(0, "type", "root")
    print(db.get_attrs("0"))
    print(db.get_attr(0, "type"))
    print(db.get_all_keys())
