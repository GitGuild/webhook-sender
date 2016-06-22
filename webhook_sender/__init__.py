import ConfigParser
import logging
import os
import requests
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy import create_engine
from webhook_sender import model

CFG = ConfigParser.ConfigParser()
CFG.read(os.environ.get('WEBHOOK_SENDER_CONFIG_FILE', 'example_cfg.ini'))

# database stuff
eng = sa.create_engine(CFG.get('db', 'SA_ENGINE_URI'))
ses = orm.sessionmaker(bind=eng)()

def setup_database():
    for m in model.__all__:
        getattr(model, m).metadata.create_all(eng)

setup_database()

models = model # rename loaded models to avoid ambiguity

logfile = CFG.LOGFILE if hasattr(CFG, 'LOGFILE') else 'server.log'
loglevel = CFG.LOGLEVEL if hasattr(CFG, 'LOGLEVEL') else logging.INFO
logging.basicConfig(filename=logfile, level=loglevel)
logger = logging.getLogger(__name__)

