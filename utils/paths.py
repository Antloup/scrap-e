import sys


def absolute_path(x): return sys.path[0].replace('\\', '/') + '/' + x


scrapers_rel_path = 'config/scrapers.yaml'
db_config_rel_path = 'config/db.yaml'
models_rel_path = 'models.pkl'
img_data_rel_path = 'img_data'

models_path = absolute_path(models_rel_path)
db_config_path = absolute_path(db_config_rel_path)
scrapers_path = absolute_path(scrapers_rel_path)
img_data_path = absolute_path(img_data_rel_path)
