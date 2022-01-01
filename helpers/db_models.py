from pymongo.collection import Collection

from constants import DB, ZERODATE

class DocNotFoundError(Exception):
    def __init__(self):
        super().__init__(f"document does not exist")

class FieldNotFoundError(Exception):
    def __init__(self):
        super().__init__(f"'field does not exist")


class DBGuild:
    def __init__(self, id: int):
        self.id = str(id)
        self.is_new = False
        self.collection = self.initalize_guild()
    
    def initalize_guild(self):
        # creates creates guild collection if it doesn't already exist
        if not self.id in DB.list_collection_names():
            self.is_new = True
            DB.create_collection(self.id)

        return DB[self.id]
    
    def get_all_members(self, projection={}):
        # gets all member docs in collection
        members = self.collection.find(projection)

        # creates a DBMember instance for each member doc
        return [DBMember(m["_id"], m["name"], self.collection) for m in members]

    def get_sorted_values(self, field_key, is_reverse=True):
        # gets all members, along with their target field
        members = list(self.collection.find({}, {"_id": 1, "name": 1, field_key:1}))

        # returns a sorted list of user dictionaries
        return sorted(members, key=lambda doc: doc[field_key], reverse=is_reverse)

    def delete_member(self, name):
        if self.collection.count_documents({ "name": name }, limit = 1) == 0:
            raise DocNotFoundError

        self.collection.delete_one({"name": name})

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
    
    @classmethod
    def from_member(cls, member):
        guild = DBGuild(member.guild.id)
        db_member = cls(member.id, member.name, guild.collection)
        return db_member
    
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