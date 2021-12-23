from constants import DB
from helpers.member import DBMember

import bson

class DocNotFoundError(Exception):
    def __init__(self):
        super().__init__(f"document does not exist")

class DBGuild:
    def __init__(self, id: int):
        self.id = str(id)
        self.is_new = False
        self.db = DB
        self.collection = self.initalize_guild()
    
    def initalize_guild(self):
        # creates creates guild collection if it doesn't already exist
        if not self.id in self.db.list_collection_names():
            self.is_new = True
            self.db.create_collection(self.id)

        return self.db[self.id]
    
    def get_all_members(self):
        # gets all member docs in collection
        members = self.collection.find({})

        # creates a DBMember instance for each member doc
        return [DBMember(m["_id"], m["name"], self.collection) for m in members]

    def get_sorted_values(self, field_key, is_reverse=True):
        # gets all members, along with their target field
        members = list(self.collection.find({}, {"_id": 1, "name": 1, field_key:1}))

        # returns a sorted list of user dictionaries
        return sorted(members, key=lambda doc: doc[field_key], reverse=is_reverse)

    def delete_member(self, id):
        if self.collection.count_documents({ "_id": bson.Int64(id) }, limit = 1) == 0:
            raise DocNotFoundError

        self.collection.delete_one({"_id": bson.Int64(id)})