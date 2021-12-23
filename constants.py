import pytz
from pymongo import MongoClient
import os

ZERODATE = "1900-01-01 00:00:00.01"
TZ = pytz.timezone('America/Vancouver')

DBNAME = "discord"
DBCLIENT = MongoClient(os.getenv("mongodb_url"))
DB = DBCLIENT[DBNAME]