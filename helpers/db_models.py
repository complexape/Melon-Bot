from datetime import datetime

from constants import DB, ZEROSTR


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
        return [DBMember(m, self) for m in members]

    def get_sorted_values(self, field_key, is_reverse=True):
        # gets only the members that don't have the default empty value for the target field
        members = list(self.collection.find({field_key: {"$ne": DBMember.BASE_FIELDS[field_key]}}))
        return sorted(members, key=lambda doc: doc[field_key], reverse=is_reverse)

    def delete_member(self, name):
        self.collection.delete_one({"name": name})

class DBMember:
    BASE_FIELDS = {
        "_id": "",
        "name": "",
        "totalvctime": ZEROSTR,
        "longestvctime": ZEROSTR,
        "lastjoined": "",
        "firstjoined": "",
        "birthday": "",
        "totaldrip": 0,
        "dripreset": ""
    }

    def __init__(self, document: dict, guild: DBGuild):
        self.doc = document
        self.id = document["_id"]
        self.name = document["name"]
        self.guild_collection = guild.collection
    
    @classmethod
    def from_new(cls, member):
        guild = DBGuild(member.guild.id)

        if guild.collection.count_documents({ '_id': member.id }, limit = 1) == 0:
            document = DBMember.BASE_FIELDS.update({
                "_id": str(member.id),
                "name": member.name
            })
            guild.collection.insert_one(document)

        else: # updates database document if member already exists
            document = guild.collection.find_one({"_id": member.id})

            if document["name"] != member.name:
                guild.collection.update_one({ "_id": member.id}, { "$set": { "name": member.name }})
                document["name"] = member.name
         
            if document.keys() != DBMember.BASE_FIELDS.keys():
                for key, value in DBMember.BASE_FIELDS.items():
                    if key not in document.keys():
                        guild.collection.update_one({ "_id": member.id}, { "$set": { key: value }})
                        document[key] = value

        return cls(document, guild)

    @staticmethod
    def value_as_datetime(str):
        try:
            return datetime.strptime(str , "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            return datetime.strptime(str , "%m/%d/%Y") 

    def update_field(self, key, new_value=""):
        if isinstance(new_value, datetime):
            new_value = new_value.strftime("%Y-%m-%d %H:%M:%S.%f")

        self.guild_collection.update_one({ "_id": self.id}, { "$set": { key: new_value }})
    
    def delete_field(self, key):
        self.guild_collection.update_one({ }, {"$unset": { key: ""}})
    
    def get(self, key, as_dt=False):
        value = self.doc[key]
        return DBMember.value_as_datetime(value) if as_dt else value
    
    def is_new(self):
        base_fields = DBMember.BASE_FIELDS
        return self.doc == base_fields.update({"_id": self.id, "name": self.name})