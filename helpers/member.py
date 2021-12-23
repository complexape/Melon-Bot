from pymongo.collection import Collection

from constants import ZERODATE

class FieldNotFoundError(Exception):
    def __init__(self):
        super().__init__(f"'field does not exist")

class DBMember:
    def __init__(self, id, name, guild_collection: Collection):
        self.id = id
        self.name = name
        self.guild_collection = guild_collection
        self.is_new = False
        self.fields = {
                "_id": self.id, # mandatory field
                "name": self.name,
                "totalvctime": ZERODATE,
                "longestvctime": ZERODATE,
                "lastjoined": "",
                "firstjoined": "",
                "birthday": ""
            }
        self.check_member()
    
    def check_member(self):
        # creates a new member document for the user's guild if doesn't already exist 
        if self.guild_collection.count_documents({ '_id': self.id }, limit = 1) == 0:
            self.guild_collection.insert_one(self.fields)
            self.is_new = True
            self.doc =  self.guild_collection.find_one({"_id": self.id})
        else:
            self.doc = self.guild_collection.find_one({"_id": self.id})

            # keeps keys up-to-date in case there are any changes
            self.update_keys()

            # helps keep names in the database up-to-date
            self.check_name()

    def check_name(self):
        if self.doc["name"] != self.name:
            self.update_field("name", self.name)

    def add_field(self, key, new_value=""):
        self.guild_collection.update_one({ "_id": self.id}, { "$set": { key: new_value }})

    def update_field(self, key, new_value=""):
        if key not in self.doc.keys():
            raise FieldNotFoundError(key, self.name)
        
        self.guild_collection.update_one({ "_id": self.id}, { "$set": { key: new_value }})
    
    def delete_field(self, key):
        if key not in self.doc.keys():
            raise FieldNotFoundError

        self.guild_collection.update_one({ }, {"$unset": { key: ""}})
    
    def get_value(self, key):
        if key not in self.doc.keys():
            raise FieldNotFoundError
        
        return self.guild_collection.find_one({"_id": self.id})[key]

    def update_keys(self):
        keys = self.doc.keys()
        new_keys = self.fields.keys()

        if keys != new_keys:
            # adds missing keys in member's document
            [self.add_field(f, self.fields[f]) for f in new_keys if f not in keys]

            # removes extra keys in member's document
            [self.delete_field(f) for f in keys if f not in new_keys]
