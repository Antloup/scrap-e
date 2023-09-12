import os
import sys
import yaml
from peewee import SqliteDatabase, Model
from utils.paths import db_config_path, absolute_path

script_dir = os.path.dirname(__file__)

db_config: dict = yaml.load(open(db_config_path), Loader=yaml.FullLoader)
db_path = absolute_path(db_config['db_name'])
db = SqliteDatabase(db_path, pragmas={'foreign_keys': 1})  # Enable foreign keys


class BaseModel(Model):

    class Meta:
        database = db

    @classmethod
    def get(cls, *query, **filters):
        try:
            return super().get(*query, **filters)
        except:
            return None
