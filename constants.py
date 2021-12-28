import pytz
from datetime import time
from pymongo import MongoClient
import os

ZERODATE = "1900-01-01 00:00:00.01"
TZ = pytz.timezone('America/Vancouver')
SLEEP_TIME = time(11, 0, 0)

DBNAME = os.getenv("dbname")
DBCLIENT = MongoClient(os.getenv("mongodb_url"))
DB = DBCLIENT[DBNAME]