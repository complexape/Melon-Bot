import pytz
from datetime import time
from pymongo import MongoClient
import os

TZ = pytz.timezone('Canada/Pacific')

DBCLIENT = MongoClient(os.getenv("mongodb_url"))
DB = DBCLIENT[os.getenv("dbname")]

BDAY_CHECK = time(8, 0, 0) # Checks for birthdays at 8AM UTC (12AM PST)
ZERODATE = "1900-01-01 00:00:00.01"