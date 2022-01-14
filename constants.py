import pytz
from datetime import datetime, time
from pymongo import MongoClient
import os

TZ = pytz.timezone('Canada/Pacific')

DBCLIENT = MongoClient(os.getenv("mongodb_url"))
DB = DBCLIENT[os.getenv("dbname")]

BDAY_CHECK = time(8, 0, 0) # Checks for birthdays at 8AM UTC (12AM PST)
ZEROSTR = "1900-01-01 00:00:00.01"
ZERODATE = datetime.strptime(ZEROSTR , "%Y-%m-%d %H:%M:%S.%f")

VALID_TYPES = ("image", "video", "audio")
ALBUM_DB = DBCLIENT["archivedb"]