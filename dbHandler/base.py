import os
import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

import settings
settings.load_env_vars()

logger = logging.getLogger("server")

logger.debug("Creating DB Engine, DB Session and Base class.")

engine = db.create_engine("{db_conn}://{user}:{password}@{host}/{db_name}"
                          .format(db_conn=os.getenv("DB_CONN"),
                                  user=os.getenv("DB_USER"),
                                  password=os.getenv("DB_PASS"),
                                  host=os.getenv("DB_HOST"),
                                  db_name=os.getenv("DB_NAME")))

logger.debug("Connected to {}".format(engine))

Session = sessionmaker(bind=engine)
Base = declarative_base()
